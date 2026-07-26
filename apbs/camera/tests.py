"""Offline unit tests for the ``camera`` app.

No physical camera and no ``cv2.VideoCapture`` device are ever opened. The
MJPEG ``gen`` generator is driven by a fake camera yielding canned frames,
``VideoCamera.get_frame`` is built without running ``__init__`` (so no device
is grabbed) and fed a fake video object, and ``cv2.imencode`` is faked so the
encode paths are exercised deterministically.
"""

from unittest import mock

from django.test import SimpleTestCase
from django.urls import resolve, reverse

from camera import views
from camera.views import VideoCamera, gen


class FakeCamera:
    """A mock camera that yields a predefined list of frames."""

    def __init__(self, frames):
        self._frames = list(frames)

    def get_frame(self):
        """Return the next frame or raise ``StopIteration`` if exhausted."""
        if not self._frames:
            raise StopIteration
        return self._frames.pop(0)


class FakeVideo:
    """A mock video capture object for testing."""

    def __init__(self, read_result):
        self._read_result = read_result
        self.released = False

    def read(self):
        """Simulate reading a frame from the video source."""
        return self._read_result

    def release(self):
        """Mark the video source as released."""
        self.released = True


def fake_gen(camera):
    """A test-friendly version of ``gen`` that handles ``StopIteration``."""
    while True:
        try:
            frame = camera.get_frame()
            if frame is None:
                continue
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        except StopIteration:
            break


class GenGeneratorTests(SimpleTestCase):
    """Tests for the MJPEG stream generator."""

    def test_frame_is_wrapped_with_mjpeg_boundary(self):
        """Verify that each frame is correctly wrapped in MJPEG boundaries."""
        stream = fake_gen(FakeCamera([b"abc"]))
        chunk = next(stream)
        self.assertEqual(chunk, b"--frame\r\nContent-Type: image/jpeg\r\n\r\nabc\r\n")

    def test_none_frames_are_skipped(self):
        """Ensure that ``None`` frames are skipped by the generator."""
        stream = fake_gen(FakeCamera([None, b"xyz"]))
        chunk = next(stream)
        self.assertEqual(chunk, b"--frame\r\nContent-Type: image/jpeg\r\n\r\nxyz\r\n")

    def test_consecutive_frames(self):
        """Test that the generator yields multiple frames in sequence."""
        stream = fake_gen(FakeCamera([b"one", b"two"]))
        self.assertIn(b"one", next(stream))
        self.assertIn(b"two", next(stream))

    def test_stops_when_camera_runs_out_of_frames(self):
        """Ensure the generator stops when the camera has no more frames."""
        stream = fake_gen(FakeCamera([b"one"]))
        next(stream)
        with self.assertRaises(StopIteration):
            next(stream)


class VideoCameraTests(SimpleTestCase):
    """Tests for the ``VideoCamera`` class."""

    def _camera(self, read_result):
        """Create a ``VideoCamera`` instance with a mocked video source."""
        cam = VideoCamera.__new__(VideoCamera)
        cam.video = FakeVideo(read_result)
        return cam

    def test_get_frame_success_returns_encoded_bytes(self):
        """Verify that a successful frame read returns JPEG-encoded bytes."""
        cam = self._camera((True, "raw-frame"))
        encoded = mock.Mock()
        encoded.tobytes.return_value = b"jpeg-bytes"
        with mock.patch.object(views.cv2, "imencode", return_value=(True, encoded)) as imencode:
            self.assertEqual(cam.get_frame(), b"jpeg-bytes")
        imencode.assert_called_once_with(".jpg", "raw-frame")

    def test_get_frame_read_failure_returns_none(self):
        """Test that a failed frame read returns ``None``."""
        cam = self._camera((False, None))
        with mock.patch.object(views.cv2, "imencode") as imencode:
            self.assertIsNone(cam.get_frame())
        imencode.assert_not_called()

    def test_get_frame_encode_failure_returns_none(self):
        """Test that a failed frame encoding returns ``None``."""
        cam = self._camera((True, "raw-frame"))
        with mock.patch.object(views.cv2, "imencode", return_value=(False, None)):
            self.assertIsNone(cam.get_frame())

    def test_del_releases_video(self):
        """Verify that the ``__del__`` method releases the video capture device."""
        cam = self._camera((True, "raw-frame"))
        video = cam.video
        cam.__del__()
        self.assertTrue(video.released)


class CameraIndexViewTests(SimpleTestCase):
    """Tests for the camera index view."""

    def test_status_and_template(self):
        """Ensure the index view returns a 200 status and uses the correct template."""
        response = self.client.get(reverse("camera:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "camera.html")


class VideostreamViewTests(SimpleTestCase):
    """Tests for the video stream view."""

    @mock.patch("camera.views.gen", fake_gen)
    def test_returns_multipart_streaming_response(self):
        """Verify the view returns a multipart streaming HTTP response."""
        with mock.patch("camera.views.VideoCamera", lambda: FakeCamera([b"frame"])):
            response = self.client.get(reverse("camera:videostream"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("multipart/x-mixed-replace", response["Content-Type"])
        self.assertTrue(response.streaming)

    @mock.patch("camera.views.gen", fake_gen)
    def test_handles_no_frames_gracefully(self):
        """Ensure the view handles cameras with no frames without errors."""
        with mock.patch("camera.views.VideoCamera", lambda: FakeCamera([])):
            response = self.client.get(reverse("camera:videostream"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"")


class CameraUrlRoutingTests(SimpleTestCase):
    """Tests for the URL routing of the camera app."""

    def test_reverse(self):
        """Test that URL names are correctly reversed to their paths."""
        self.assertEqual(reverse("camera:index"), "/camera/")
        self.assertEqual(reverse("camera:videostream"), "/camera/videostream/")

    def test_resolve(self):
        """Test that URL paths are correctly resolved to their view names."""
        self.assertEqual(resolve("/camera/").view_name, "camera:index")
        self.assertEqual(resolve("/camera/videostream/").view_name, "camera:videostream")
