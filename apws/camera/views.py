# camera/views.py

from __future__ import annotations

import logging
import socket
from typing import Generator

from django.conf import settings
from django.http import HttpRequest, StreamingHttpResponse
from django.shortcuts import render
from django.views import View

logger = logging.getLogger(__name__)

JPEG_START = b"\xff\xd8"
JPEG_END = b"\xff\xd9"


class CameraConnection:
    """
    Connects to the raw MJPEG TCP stream produced by rpicam-vid.
    """

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.socket: socket.socket | None = None

    def connect(self) -> None:
        self.close()

        logger.info(f"Connecting to camera at {self.host}:{self.port}")
        try:
            self.socket = socket.create_connection(
                (self.host, self.port),
                timeout=10,
            )
            logger.info("Connected to camera")
        except Exception as e:
            logger.error(f"Failed to connect to camera: {e}")
            raise

        # Do not impose a read timeout while streaming.
        self.socket.settimeout(None)

    def close(self) -> None:
        if self.socket is not None:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

            try:
                self.socket.close()
            except OSError:
                pass

            self.socket = None

    def frames(self) -> Generator[bytes, None, None]:
        """
        Read JPEG images from the raw TCP MJPEG stream.
        """
        self.connect()

        buffer = bytearray()
        frame_count = 0

        try:
            while True:
                if self.socket is None:
                    return

                chunk = self.socket.recv(64 * 1024)

                if not chunk:
                    raise ConnectionError(
                        "The Raspberry Pi camera stream closed the connection"
                    )

                buffer.extend(chunk)

                while True:
                    start = buffer.find(JPEG_START)

                    if start == -1:
                        # Preserve one byte in case the JPEG marker is split
                        # across two socket reads.
                        if len(buffer) > 1:
                            del buffer[:-1]
                        break

                    if start > 0:
                        del buffer[:start]

                    end = buffer.find(JPEG_END, len(JPEG_START))

                    if end == -1:
                        break

                    frame_end = end + len(JPEG_END)
                    frame = bytes(buffer[:frame_end])
                    del buffer[:frame_end]

                    frame_count += 1
                    if frame_count % 30 == 0:
                        logger.debug(f"Received frame {frame_count}, size: {len(frame)}")

                    yield frame

        finally:
            logger.info(f"Closing connection after {frame_count} frames")
            self.close()


def mjpeg_response(
        camera: CameraConnection,
) -> Generator[bytes, None, None]:
    """
    Convert each JPEG into an HTTP MJPEG multipart section.
    """
    boundary = b"frame"

    try:
        frames = camera.frames()

        for frame in frames:
            yield (
                    b"--" + boundary + b"\r\n"
                                       b"Content-Type: image/jpeg\r\n"
                                       b"Content-Length: "
                    + str(len(frame)).encode("ascii")
                    + b"\r\n\r\n"
                    + frame
                    + b"\r\n"
            )

    except GeneratorExit:
        # The browser disconnected - close immediately
        logger.info("GeneratorExit - closing camera")
        camera.close()
    except (ConnectionError, ConnectionResetError, BrokenPipeError, OSError) as e:
        logger.warning(f"Connection error: {e}")
        camera.close()
        raise


class CameraIndexView(View):
    def get(
            self,
            request: HttpRequest,
            *args,
            **kwargs,
    ):
        return render(request, "camera.html")


def videostream(request: HttpRequest) -> StreamingHttpResponse:
    logger.info("videostream endpoint called")
    camera = CameraConnection(
        host=settings.CAMERA_HOST,
        port=settings.CAMERA_PORT,
    )

    response = StreamingHttpResponse(
        mjpeg_response(camera),
        content_type="multipart/x-mixed-replace; boundary=frame",
    )

    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"

    return response
