from django.urls import path

from .views import CameraIndexView, videostream

app_name = "camera"

urlpatterns = [
    path("", CameraIndexView.as_view(), name="index"),
    path("videostream/", videostream, name="videostream"),
]
