from django.urls import path

from .views import (
    SearchIndexView,
    HygrometerDataDetailView,
    HygrometerDataListView,
    WeatherDataDetailView,
    WeatherDataListView,
)

app_name = "search"

urlpatterns = [
    path("", SearchIndexView.as_view(), name="index"),
    path("weather/", WeatherDataListView.as_view(), name="weather"),
    path("hygrometer/", HygrometerDataListView.as_view(), name="hygrometer"),
    path("weather/details/<str:name>/<str:timestamp>/", WeatherDataDetailView.as_view(), name="weatherdetails"),
    path("hygrometer/details/<str:timestamp>/", HygrometerDataDetailView.as_view(), name="hygrometerdetails"),
]
