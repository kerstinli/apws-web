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
    """Yields the supplied frames one per ``get_frame`` call."""

    def __init__(self, frames):
        self._frames = list(frames)

    def get_frame(self):
        return self._frames.pop(0)


class FakeVideo:
    def __init__(self, read_result):
        self._read_result = read_result
        self.released = False

    def read(self):
        return self._read_result

    def release(self):
        self.released = True


class GenGeneratorTests(SimpleTestCase):
    def test_frame_is_wrapped_with_mjpeg_boundary(self):
        stream = gen(FakeCamera([b"abc"]))
        chunk = next(stream)
        self.assertEqual(chunk, b"--frame\r\nContent-Type: image/jpeg\r\n\r\nabc\r\n")

    def test_none_frames_are_skipped(self):
        # First frame is None (skipped via ``continue``), second is emitted.
        stream = gen(FakeCamera([None, b"xyz"]))
        chunk = next(stream)
        self.assertEqual(chunk, b"--frame\r\nContent-Type: image/jpeg\r\n\r\nxyz\r\n")

    def test_consecutive_frames(self):
        stream = gen(FakeCamera([b"one", b"two"]))
        self.assertIn(b"one", next(stream))
        self.assertIn(b"two", next(stream))


class VideoCameraGetFrameTests(SimpleTestCase):
    def _camera(self, read_result):
        # Build without __init__ so cv2.VideoCapture(0) is never called.
        cam = VideoCamera.__new__(VideoCamera)
        cam.video = FakeVideo(read_result)
        return cam

    def test_success_returns_encoded_bytes(self):
        cam = self._camera((True, "raw-frame"))
        encoded = mock.Mock()
        encoded.tobytes.return_value = b"jpeg-bytes"
        with mock.patch.object(views.cv2, "imencode", return_value=(True, encoded)) as imencode:
            self.assertEqual(cam.get_frame(), b"jpeg-bytes")
        imencode.assert_called_once_with(".jpg", "raw-frame")

    def test_read_failure_returns_none(self):
        cam = self._camera((False, None))
        with mock.patch.object(views.cv2, "imencode") as imencode:
            self.assertIsNone(cam.get_frame())
        imencode.assert_not_called()

    def test_encode_failure_returns_none(self):
        cam = self._camera((True, "raw-frame"))
        with mock.patch.object(views.cv2, "imencode", return_value=(False, None)):
            self.assertIsNone(cam.get_frame())


class CameraIndexViewTests(SimpleTestCase):
    def test_status_and_template(self):
        response = self.client.get(reverse("camera:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "camera.html")


class VideostreamViewTests(SimpleTestCase):
    def test_returns_multipart_streaming_response(self):
        # Replace VideoCamera so no capture device is opened; do not consume the
        # (infinite) streaming body.
        with mock.patch("camera.views.VideoCamera", lambda: FakeCamera([b"frame"])):
            response = self.client.get(reverse("camera:videostream"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("multipart/x-mixed-replace", response["Content-Type"])
        self.assertTrue(response.streaming)


class CameraUrlRoutingTests(SimpleTestCase):
    def test_reverse(self):
        self.assertEqual(reverse("camera:index"), "/camera/")
        self.assertEqual(reverse("camera:videostream"), "/camera/videostream/")

    def test_resolve(self):
        self.assertEqual(resolve("/camera/").view_name, "camera:index")
        self.assertEqual(resolve("/camera/videostream/").view_name, "camera:videostream")
