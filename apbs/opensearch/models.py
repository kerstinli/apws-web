import datetime

from django.db import models
from django.db.models import Manager


class OpenSearchQuerySet:

  def __init__(
          self,
          model,
          index,
          filters=None,
          query=None,
          ordering=None
  ):
    self.model = model
    self.index = index

    self.filters = filters or []
    self.query = query
    self.ordering = ordering


class WeatherDataManager(Manager):

  def get_queryset(self):
    return OpenSearchQuerySet(
      model=self.model,
      index="products"
    )

  def filter(self, **kwargs):
    return self.get_queryset().filter(**kwargs)

  def get(self, **kwargs):
    return self.get_queryset().get(**kwargs)

  def search(self, text):
    return self.get_queryset().search(text)

class WeatherData(models.Model):
  def __init__(self, name: str, timestamp: datetime.datetime, temperature: float, humidity: float):
    """
    Initialize a WeatherData object with data
    """
    super(WeatherData, self).__init__()
    self.name = name
    self.timestamp = timestamp
    self.temperature = temperature
    self.humidity = humidity

  name = models.CharField(max_length=255)
  temperature = models.FloatField()
  humidity = models.FloatField()
  timestamp = models.DateTimeField()

  objects = WeatherDataManager()

  class Meta:
    managed = False