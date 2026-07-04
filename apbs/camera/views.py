import cv2

from django.http import StreamingHttpResponse
from django.shortcuts import render
from django.views import View


class CameraIndexView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "camera.html")


class VideoCamera:
    def __init__(self):
        self.video = cv2.VideoCapture(0)

    def __del__(self):
        if self.video:
            self.video.release()

    def get_frame(self):
        ok, frame = self.video.read()
        if not ok:
            return None
        ok, jpeg = cv2.imencode(".jpg", frame)
        if not ok:
            return None
        return jpeg.tobytes()


def videostream(request):
    return StreamingHttpResponse(
        gen(VideoCamera()),
        content_type="multipart/x-mixed-replace; boundary=frame",
    )


def gen(camera):
    while True:
        frame = camera.get_frame()
        if frame is None:
            continue
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        )
