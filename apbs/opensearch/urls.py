from django.urls import path
from . import views
from .views import WeatherDataDetailView, WeatherDataListView

urlpatterns = [
    path("", WeatherDataListView.as_view(), name = "search"),
    path("details/<str:name>/<str:timestamp>/", WeatherDataDetailView.as_view(), name = "details"),
]
