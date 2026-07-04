from django.urls import path
from .views import WeatherDataDetailView, WeatherDataListView

app_name = "search"

urlpatterns = [
    path("weather/", WeatherDataListView.as_view(), name = "index"),
    path("weather/details/<str:name>/<str:timestamp>/", WeatherDataDetailView.as_view(), name = "details"),
]
