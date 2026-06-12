from datetime import datetime

from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import DetailView
from .models import WeatherData


class WeatherDataListView(View):
    def get(self, request, *args, **kwargs):

        date_filter = request.GET.get("date", "")
        name_filter = request.GET.get("name", "")

        data = []  # WeatherData.objects.all()

        data.append(WeatherData("test1", datetime.now(), 25.4, 75.5))
        data.append(WeatherData("test2", datetime.now(), 15.0, 55.1))

        context = {
            "data": data,
            "date_filter": date_filter,
            "name_filter": name_filter,
        }

        return render(request, 'index.html', context)


class WeatherDataDetailView(DetailView):
    model = WeatherData
    template_name = "details.html"
    context_object_name = "data"

    def get_object(self, queryset=None):
        name = self.kwargs["name"]
        timestamp = self.kwargs["timestamp"]
        return WeatherData(name, timestamp, 0, 0)
