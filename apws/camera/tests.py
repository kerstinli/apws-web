"""Offline unit tests for the ``camera`` app.

Tests the CameraConnection class and mjpeg_response function without
requiring a physical camera or network connection.
"""

from unittest import mock

from django.test import SimpleTestCase, override_settings
from django.urls import resolve, reverse

from camera import views


class FakeSocket:
    """A mock socket for testing CameraConnection."""

    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.closed = False
        self.shutdown_called = False

    def recv(self, size):
        """Simulate receiving data from socket."""
        if not self.chunks:
            return b""
        return self.chunks.pop(0)

    def settimeout(self, timeout):
        """Mock settimeout."""
        pass

    def shutdown(self, how):
        """Mock shutdown."""
        self.shutdown_called = True

    def close(self):
        """Mock close."""
        self.closed = True


class MjpegResponseTests(SimpleTestCase):
    """Tests for the mjpeg_response generator."""

    def test_frame_is_wrapped_with_mjpeg_boundary(self):
        """Verify that each frame is correctly wrapped in MJPEG boundaries."""
        camera = mock.Mock()
        camera.frames.return_value = iter([b"jpeg-frame"])
        
        response = views.mjpeg_response(camera)
        chunk = next(response)
        
        self.assertIn(b"--frame", chunk)
        self.assertIn(b"Content-Type: image/jpeg", chunk)
        self.assertIn(b"jpeg-frame", chunk)

    def test_includes_content_length(self):
        """Verify that Content-Length header is included."""
        camera = mock.Mock()
        camera.frames.return_value = iter([b"test-frame"])
        
        response = views.mjpeg_response(camera)
        chunk = next(response)
        
        self.assertIn(b"Content-Length: 10", chunk)

    def test_handles_generator_exit(self):
        """Ensure the generator handles GeneratorExit gracefully."""
        camera = mock.Mock()
        camera.frames.return_value = iter([b"frame1", b"frame2"])
        
        response = views.mjpeg_response(camera)
        next(response)
        response.close()
        
        camera.close.assert_called_once()


class CameraConnectionTests(SimpleTestCase):
    """Tests for the CameraConnection class."""

    def test_connect_creates_socket(self):
        """Verify that connect creates a socket connection."""
        with mock.patch("socket.create_connection") as mock_create:
            mock_socket = mock.Mock()
            mock_create.return_value = mock_socket
            
            camera = views.CameraConnection("localhost", 8080)
            camera.connect()
            
            mock_create.assert_called_once_with(("localhost", 8080), timeout=10)
            self.assertEqual(camera.socket, mock_socket)

    def test_close_shuts_down_socket(self):
        """Verify that close properly shuts down the socket."""
        camera = views.CameraConnection("localhost", 8080)
        mock_socket = mock.Mock()
        camera.socket = mock_socket
        
        camera.close()
        
        mock_socket.shutdown.assert_called_once()
        mock_socket.close.assert_called_once()
        self.assertIsNone(camera.socket)

    def test_close_handles_none_socket(self):
        """Verify that close handles None socket gracefully."""
        camera = views.CameraConnection("localhost", 8080)
        camera.socket = None
        
        # Should not raise an exception
        camera.close()

    def test_frames_yields_jpeg_data(self):
        """Verify that frames generator yields complete JPEG frames."""
        # Create a fake socket with JPEG start/end markers
        jpeg_data = b"\xff\xd8" + b"test" + b"\xff\xd9"
        fake_socket = FakeSocket([jpeg_data])
        
        camera = views.CameraConnection("localhost", 8080)
        camera.socket = fake_socket
        
        # Mock connect to avoid real connection
        with mock.patch.object(camera, 'connect'):
            # Collect frames until ConnectionError (stream closed)
            frames = []
            try:
                for frame in camera.frames():
                    frames.append(frame)
            except ConnectionError:
                pass  # Expected when socket runs out of data
        
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0], jpeg_data)


class CameraIndexViewTests(SimpleTestCase):
    """Tests for the camera index view."""

    def test_status_and_template(self):
        """Ensure the index view returns a 200 status and uses the correct template."""
        response = self.client.get(reverse("camera:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "camera.html")


class VideostreamViewTests(SimpleTestCase):
    """Tests for the video stream view."""

    @override_settings(CAMERA_HOST="localhost", CAMERA_PORT=8080)
    @mock.patch("camera.views.CameraConnection")
    def test_returns_multipart_streaming_response(self, mock_camera_class):
        """Verify the view returns a multipart streaming HTTP response."""
        mock_camera = mock.Mock()
        mock_camera.frames.return_value = iter([b"frame"])
        mock_camera_class.return_value = mock_camera
        
        response = self.client.get(reverse("camera:videostream"))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("multipart/x-mixed-replace", response["Content-Type"])
        self.assertTrue(response.streaming)
        mock_camera_class.assert_called_once_with(host="localhost", port=8080)

    @override_settings(CAMERA_HOST="localhost", CAMERA_PORT=8080)
    @mock.patch("camera.views.CameraConnection")
    def test_handles_no_frames_gracefully(self, mock_camera_class):
        """Ensure the view handles cameras with no frames without errors."""
        mock_camera = mock.Mock()
        mock_camera.frames.return_value = iter([])
        mock_camera_class.return_value = mock_camera
        
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
