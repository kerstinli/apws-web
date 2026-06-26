from datetime import datetime

from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import DetailView
from .models import WeatherData, WeatherDataManager


class WeatherDataListView(View):
    def get(self, request, *args, **kwargs):

        date_filter = request.GET.get("date", "")
        name_filter = request.GET.get("name", "")

        kwargs.update({"name": name_filter, "timestamp": date_filter})

        data = WeatherDataManager().search(**kwargs)

        context = {
            "data": data,
            "date_filter": date_filter,
            "name_filter": name_filter,
        }

        return render(request, 'index.html', context)


class WeatherDataDetailView(DetailView):
    """
    Weather data detail view
    """
    model = WeatherData
    template_name = "details.html"
    context_object_name = "data"

    def get_queryset(self):
        return WeatherData.objects.all()

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_object_or_404(
            queryset,
            name=self.kwargs["name"],
            timestamp=self.kwargs["timestamp"],
        )
