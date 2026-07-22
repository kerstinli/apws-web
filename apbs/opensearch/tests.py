"""Offline unit tests for the ``opensearch`` app.

The whole suite runs without any OpenSearch instance, live server or real
network access. The production ``OpenSearchClient`` already returns canned
mock documents (its HTTP path is stubbed out in the source), so the client,
manager, queryset and views are exercised directly against that fake data.
Where a code path *does* build an HTTP request (``_execute_search``) a fake
``requests`` module is injected so no socket is ever opened.
"""

from unittest import mock

from django.template import Context, Template
from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve, reverse

from opensearch.client.client import OpenSearchClient
from opensearch.models import (
    OpenSearchQuerySet,
    SearchDataManager,
    SensorData,
    WeatherData,
)


class RecordingClient:
    """A fake OpenSearch client that records calls and returns canned data."""

    def __init__(self, find_result=None, get_result=None):
        self.find_result = find_result if find_result is not None else [{"hit": 1}]
        self.get_result = get_result if get_result is not None else {"doc": 1}
        self.find_calls = []
        self.get_calls = []

    def find(self, index, **kwargs):
        self.find_calls.append((index, kwargs))
        return self.find_result

    def get(self, index, **kwargs):
        self.get_calls.append((index, kwargs))
        return self.get_result


class OpenSearchClientFindTests(SimpleTestCase):
    def setUp(self):
        self.client = OpenSearchClient(host="localhost", port=9200, auth=None, ssl=False)

    def test_find_weather_returns_multi_hit_list(self):
        result = self.client.find("weather")
        self.assertEqual(len(result), 4)
        self.assertEqual({d["name"] for d in result}, {"aussen", "innen"})
        for doc in result:
            self.assertEqual(set(doc), {"name", "timestamp", "temperature", "humidity"})

    def test_find_sensor_returns_multi_hit_list(self):
        result = self.client.find("sensor")
        self.assertEqual(len(result), 4)
        for doc in result:
            self.assertEqual(set(doc), {"timestamp", "value"})

    def test_find_unknown_index_is_empty_branch(self):
        self.assertEqual(self.client.find("does-not-exist"), [])


class OpenSearchClientGetTests(SimpleTestCase):
    def setUp(self):
        self.client = OpenSearchClient(host="localhost", port=9200, auth=None, ssl=False)

    def test_get_weather_returns_single_doc(self):
        doc = self.client.get("weather")
        self.assertEqual(doc["name"], "aussen")
        self.assertEqual(doc["temperature"], 17.5)
        self.assertEqual(set(doc), {"name", "timestamp", "temperature", "humidity"})

    def test_get_sensor_returns_single_doc(self):
        doc = self.client.get("sensor")
        self.assertEqual(doc["value"], 3)
        self.assertEqual(set(doc), {"timestamp", "value"})

    def test_get_unknown_index_is_empty_branch(self):
        self.assertEqual(self.client.get("nope"), {})


class FilterParsingTests(SimpleTestCase):
    def test_parse_filter_params_passes_kwargs_through(self):
        params = OpenSearchClient._parse_filter_params(name="aussen", timestamp="01.05.2026")
        self.assertEqual(params, {"name": "aussen", "timestamp": "01.05.2026"})

    def test_parse_filter_params_empty(self):
        self.assertEqual(OpenSearchClient._parse_filter_params(), {})


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class FakeRequests:
    """Stand-in for the ``requests`` module capturing the outgoing call."""

    def __init__(self):
        self.calls = []

    def get(self, url, data):
        self.calls.append({"url": url, "data": data})
        return FakeResponse({"hits": {"hits": []}})


class SearchPayloadConstructionTests(SimpleTestCase):
    """Exercise ``_execute_search`` without touching the network."""

    def test_payload_and_url_for_plain_http(self):
        client = OpenSearchClient(host="os-host", port=9200, auth=None, ssl=False)
        fake = FakeRequests()
        with mock.patch("opensearch.client.client.requests", fake):
            client._execute_search("weather", {"name": "aussen", "timestamp": "01.05.2026"})

        self.assertEqual(len(fake.calls), 1)
        call = fake.calls[0]
        self.assertEqual(call["url"], "http://os-host:9200/weather*/_search")
        self.assertEqual(
            call["data"],
            {"query": {"match": {"name": "aussen", "timestamp": "01.05.2026"}}},
        )

    def test_url_uses_https_when_ssl_enabled(self):
        client = OpenSearchClient(host="secure", port=9243, auth=None, ssl=True)
        fake = FakeRequests()
        with mock.patch("opensearch.client.client.requests", fake):
            client._execute_search("sensor", {})
        self.assertEqual(fake.calls[0]["url"], "https://secure:9243/sensor*/_search")
        self.assertEqual(fake.calls[0]["data"], {"query": {"match": {}}})


class QuerySetDelegationTests(SimpleTestCase):
    def test_search_delegates_to_client_find(self):
        client = RecordingClient(find_result=[{"a": 1}, {"b": 2}])
        qs = OpenSearchQuerySet(model=WeatherData, client=client, index="weather")
        result = qs.search(name="aussen", timestamp="today")
        self.assertEqual(result, [{"a": 1}, {"b": 2}])
        self.assertEqual(client.find_calls, [("weather", {"name": "aussen", "timestamp": "today"})])

    def test_get_delegates_to_client_get(self):
        client = RecordingClient(get_result={"doc": 42})
        qs = OpenSearchQuerySet(model=SensorData, client=client, index="sensor")
        result = qs.get(timestamp="today")
        self.assertEqual(result, {"doc": 42})
        self.assertEqual(client.get_calls, [("sensor", {"timestamp": "today"})])

    def test_empty_result_branch(self):
        client = RecordingClient(find_result=[])
        qs = OpenSearchQuerySet(model=WeatherData, client=client, index="weather")
        self.assertEqual(qs.search(), [])


class ManagerTests(SimpleTestCase):
    def test_get_queryset_builds_client_from_settings(self):
        qs = WeatherData.objects.get_queryset()
        self.assertIsInstance(qs, OpenSearchQuerySet)
        self.assertEqual(qs.index, "weather")
        self.assertIsInstance(qs.client, OpenSearchClient)
        self.assertEqual(qs.client.host, "localhost")
        self.assertEqual(qs.client.port, 9200)
        self.assertFalse(qs.client.use_ssl)

    def test_manager_search_delegates_to_queryset(self):
        manager = SearchDataManager("weather")
        fake_qs = OpenSearchQuerySet(model=WeatherData, client=RecordingClient(find_result=["x"]), index="weather")
        with mock.patch.object(manager, "get_queryset", return_value=fake_qs):
            self.assertEqual(manager.search(name="a"), ["x"])

    def test_manager_get_delegates_to_queryset(self):
        manager = SearchDataManager("sensor")
        fake_qs = OpenSearchQuerySet(model=SensorData, client=RecordingClient(get_result={"v": 1}), index="sensor")
        with mock.patch.object(manager, "get_queryset", return_value=fake_qs):
            self.assertEqual(manager.get(timestamp="t"), {"v": 1})

    def test_manager_search_end_to_end_against_canned_data(self):
        # No injection: the real OpenSearchClient returns canned mock docs, still offline.
        self.assertEqual(len(SearchDataManager("weather").search()), 4)
        self.assertEqual(len(SearchDataManager("sensor").search()), 4)


class SearchIndexViewTests(SimpleTestCase):
    def test_status_and_template(self):
        response = self.client.get(reverse("search:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")


class WeatherListViewTests(SimpleTestCase):
    def test_status_template_and_multi_hit_context(self):
        response = self.client.get(reverse("search:weather"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "weather.html")
        self.assertEqual(len(response.context["data"]), 4)
        self.assertEqual(response.context["date_filter"], "")
        self.assertEqual(response.context["name_filter"], "")

    def test_filters_reflected_in_context(self):
        response = self.client.get(reverse("search:weather"), {"date": "01.05.2026", "name": "aussen"})
        self.assertEqual(response.context["date_filter"], "01.05.2026")
        self.assertEqual(response.context["name_filter"], "aussen")

    def test_filters_forwarded_to_manager(self):
        with mock.patch("opensearch.views.SearchDataManager.search", return_value=[]) as search:
            self.client.get(reverse("search:weather"), {"date": "01.05.2026", "name": "aussen"})
        _, kwargs = search.call_args
        self.assertEqual(kwargs["name"], "aussen")
        self.assertEqual(kwargs["timestamp"], "01.05.2026")

    def test_empty_result_branch(self):
        with mock.patch("opensearch.views.SearchDataManager.search", return_value=[]):
            response = self.client.get(reverse("search:weather"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["data"]), [])


class SensorListViewTests(SimpleTestCase):
    def test_status_template_and_multi_hit_context(self):
        response = self.client.get(reverse("search:sensor"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "sensor.html")
        self.assertEqual(len(response.context["data"]), 4)
        self.assertEqual(response.context["date_filter"], "")

    def test_filter_forwarded_to_manager(self):
        with mock.patch("opensearch.views.SearchDataManager.search", return_value=[]) as search:
            self.client.get(reverse("search:sensor"), {"date": "01.05.2026"})
        _, kwargs = search.call_args
        self.assertEqual(kwargs["timestamp"], "01.05.2026")

    def test_empty_result_branch(self):
        with mock.patch("opensearch.views.SearchDataManager.search", return_value=[]):
            response = self.client.get(reverse("search:sensor"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["data"]), [])


class DetailViewTests(SimpleTestCase):
    def test_weather_detail_returns_single_doc(self):
        url = reverse("search:weatherdetails", kwargs={"name": "aussen", "timestamp": "01.05.2026"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "weatherdetails.html")
        self.assertEqual(response.context["data"]["name"], "aussen")

    def test_sensor_detail_returns_single_doc(self):
        url = reverse("search:sensordetails", kwargs={"timestamp": "01.05.2026"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "sensordetails.html")
        self.assertEqual(response.context["data"]["value"], 3)


class UrlRoutingTests(SimpleTestCase):
    def test_reverse_search_urls(self):
        self.assertEqual(reverse("search:index"), "/search/")
        self.assertEqual(reverse("search:weather"), "/search/weather/")
        self.assertEqual(reverse("search:sensor"), "/search/sensor/")
        self.assertEqual(
            reverse("search:weatherdetails", kwargs={"name": "aussen", "timestamp": "t"}),
            "/search/weather/details/aussen/t/",
        )
        self.assertEqual(
            reverse("search:sensordetails", kwargs={"timestamp": "t"}),
            "/search/sensor/details/t/",
        )

    def test_resolve_search_index(self):
        match = resolve("/search/")
        self.assertEqual(match.view_name, "search:index")


class UrlReplaceTagTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _render(self, query, tag_args):
        request = self.factory.get("/search/weather/", query)
        template = Template("{% load url_tags %}{% url_replace " + tag_args + " %}")
        return template.render(Context({"request": request}))

    def test_adds_new_param_preserving_existing(self):
        output = self._render({"name": "aussen"}, "page=2")
        self.assertIn("name=aussen", output)
        self.assertIn("page=2", output)

    def test_replaces_existing_param(self):
        output = self._render({"date": "old"}, "date='new'")
        self.assertIn("date=new", output)
        self.assertNotIn("date=old", output)
