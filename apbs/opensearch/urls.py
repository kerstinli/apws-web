from django.urls import path
from django.views.generic import RedirectView

from .views import WeatherDataDetailView, WeatherDataListView, SensorDataListView, SearchIndexView, SensorDataDetailView

app_name = "search"

urlpatterns = [
    path("", SearchIndexView.as_view(), name = "index"),
    path("weather/", WeatherDataListView.as_view(), name = "weather"),
    path("sensor/", SensorDataListView.as_view(), name = "sensor"),
    path("weather/details/<str:name>/<str:timestamp>/", WeatherDataDetailView.as_view(), name = "weatherdetails"),
    path("sensor/details/<str:timestamp>/", SensorDataDetailView.as_view(), name="sensordetails"),
]
