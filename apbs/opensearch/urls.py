from django.urls import path
from django.views.generic import RedirectView

from .views import WeatherDataDetailView, WeatherDataListView

app_name = "search"

urlpatterns = [
    path('', RedirectView.as_view(url='weather/', permanent=False)),
    path("weather/", WeatherDataListView.as_view(), name = "index"),
    path("weather/details/<str:name>/<str:timestamp>/", WeatherDataDetailView.as_view(), name = "details"),
]
