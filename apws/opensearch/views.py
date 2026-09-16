from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import DetailView

from .models import SearchDataManager, HygrometerData, WeatherData


class SearchIndexView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "index.html")


class WeatherDataListView(View):
    def get(self, request, *args, **kwargs):
        date_filter = request.GET.get("date", "")
        name_filter = request.GET.get("name", "")

        kwargs.update({"name": name_filter, "timestamp": date_filter})

        data = SearchDataManager("weather").search(**kwargs)

        context = {
            "data": data,
            "date_filter": date_filter,
            "name_filter": name_filter,
        }
        return render(request, "weather.html", context)


class HygrometerDataListView(View):
    def get(self, request, *args, **kwargs):
        date_filter = request.GET.get("date", "")

        kwargs.update({"timestamp": date_filter})
        data = SearchDataManager("hygrometer").search(**kwargs)

        context = {
            "data": data,
            "date_filter": date_filter,
        }
        return render(request, "hygrometer.html", context)


class WeatherDataDetailView(DetailView):
    """
    Weather data detail view
    """

    model = WeatherData
    template_name = "weatherdetails.html"
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


class HygrometerDataDetailView(DetailView):
    """
    Hygrometer data detail view
    """

    model = HygrometerData
    template_name = "hygrometerdetails.html"
    context_object_name = "data"

    def get_queryset(self):
        return HygrometerData.objects.all()

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_object_or_404(
            queryset,
            timestamp=self.kwargs["timestamp"],
        )
