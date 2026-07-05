from django.db import models

from apbs import settings
from opensearch.client.client import OpenSearchClient


class OpenSearchQuerySet(models.QuerySet):
    def __init__(self, *args, index = None, client: OpenSearchClient = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = client
        self.index = index

    def search(self, **kwargs):
        return self.client.find(self.index, **kwargs)

    def get(self, **kwargs):
        return self.client.get(self.index, **kwargs)


class SearchDataManager(models.Manager):
    def __init__(self, index: str):
        super().__init__()
        self.index = index

    def get_queryset(self) -> OpenSearchQuerySet:
        return OpenSearchQuerySet(
            model=self.model,
            client=OpenSearchClient(
                host=settings.OPENSEARCH_HOST,
                port=settings.OPENSEARCH_PORT,
                auth=settings.OPENSEARCH_AUTH,
                ssl=settings.OPENSEARCH_USE_SSL
            ),
            index=self.index,
        )

    def search(self, **kwargs):
        return self.get_queryset().search(**kwargs)

    def get(self, **kwargs):
        return self.get_queryset().get(**kwargs)



class WeatherData(models.Model):
    name = models.CharField(max_length=255)
    temperature = models.FloatField()
    humidity = models.FloatField()
    timestamp = models.DateTimeField()

    objects = SearchDataManager("weather")

    class Meta:
        managed = False

class SensorData(models.Model):
    value = models.FloatField()
    timestamp = models.DateTimeField()

    objects = SearchDataManager("sensor")

    class Meta:
        managed = False
