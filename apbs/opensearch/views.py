from datetime import datetime
import json

from django.shortcuts import render
from django.views import View
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


class WeatherDataDetailView(View):
    def get(self, request, *args, **kwargs):
        name = self.kwargs["name"]
        timestamp = self.kwargs["timestamp"]
        data = WeatherData(name, timestamp, 0, 0)
        context = {"data": data}
        return render(request, "details.html", context)
