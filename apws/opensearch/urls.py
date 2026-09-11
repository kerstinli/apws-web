from django.urls import path

from .views import (
    SearchIndexView,
    SensorDataDetailView,
    SensorDataListView,
    WeatherDataDetailView,
    WeatherDataListView,
)

app_name = "search"

urlpatterns = [
    path("", SearchIndexView.as_view(), name="index"),
    path("weather/", WeatherDataListView.as_view(), name="weather"),
    path("sensor/", SensorDataListView.as_view(), name="sensor"),
    path("weather/details/<str:name>/<str:timestamp>/", WeatherDataDetailView.as_view(), name="weatherdetails"),
    path("sensor/details/<str:timestamp>/", SensorDataDetailView.as_view(), name="sensordetails"),
]
