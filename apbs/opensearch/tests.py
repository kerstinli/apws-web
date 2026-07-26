from unittest import mock

from django.test import SimpleTestCase

from opensearch.client.client import OpenSearchClient


class FakeResponse:
    """A mock HTTP response for testing the OpenSearch client."""

    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        """Return the JSON payload of the response."""
        return self._payload

    def raise_for_status(self):
        """Raise an exception for HTTP error status codes."""
        if self.status_code >= 400:
            raise Exception("HTTP Error")


class OpenSearchClientTests(SimpleTestCase):
    """Tests for the OpenSearch client."""

    def setUp(self):
        """Set up a client instance for all tests."""
        self.client = OpenSearchClient(host="localhost", port=9200, auth=None, ssl=False, ssl_verify=False)

    @mock.patch("opensearch.client.client.requests")
    def test_find_returns_list_of_documents(self, mock_requests):
        """Verify that ``find`` returns a list of documents from a mocked response."""
        canned_response = {
            "hits": {
                "hits": [
                    {"_source": {"name": "room-1", "temperature": 21.5}},
                    {"_source": {"name": "room-2", "temperature": 23.0}},
                ]
            }
        }
        mock_requests.post.return_value = FakeResponse(canned_response)
        result = self.client.find("weather", name="room-1")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "room-1")
        self.assertEqual(result[1]["name"], "room-2")

    @mock.patch("opensearch.client.client.requests")
    def test_get_returns_single_document(self, mock_requests):
        """Verify that ``get`` returns a single document from a mocked response."""
        canned_response = {"hits": {"hits": [{"_source": {"name": "room-1", "temperature": 21.5}}]}}
        mock_requests.post.return_value = FakeResponse(canned_response)
        result = self.client.get("weather", name="room-1")
        self.assertEqual(result["name"], "room-1")

    @mock.patch("opensearch.client.client.requests")
    def test_empty_find_result(self, mock_requests):
        """Ensure ``find`` returns an empty list when there are no hits."""
        mock_requests.post.return_value = FakeResponse({"hits": {"hits": []}})
        result = self.client.find("weather")
        self.assertEqual(result, [])

    @mock.patch("opensearch.client.client.requests")
    def test_empty_get_result(self, mock_requests):
        """Ensure ``get`` returns ``None`` when there are no hits."""
        mock_requests.post.return_value = FakeResponse({"hits": {"hits": []}})
        result = self.client.get("weather")
        self.assertIsNone(result)

    def test_parse_filter_params(self):
        """Test that filter parameters are correctly parsed into a dictionary."""
        params = self.client._parse_filter_params(name="room-1", timestamp="gestern")
        self.assertEqual(params, {"name": "room-1", "timestamp": "gestern"})

    def test_parse_filter_params_with_none_value(self):
        """Test that parameters with ``None`` values are excluded."""
        params = self.client._parse_filter_params(name="room-1", timestamp=None)
        self.assertEqual(params, {"name": "room-1"})

    @mock.patch("opensearch.client.client.requests")
    def test_search_payload_construction(self, mock_requests):
        """Verify the search payload is correctly constructed with filters."""
        mock_requests.post.return_value = FakeResponse({"hits": {"hits": []}})
        self.client.find("weather", name="room-1", timestamp="gestern")
        mock_requests.post.assert_called_with(
            url="http://localhost:9200/weather-*/_search",
            json={"query": {"match": {"name": "room-1", "timestamp": "gestern"}}},
            auth=None,
            verify=False,
        )

    @mock.patch("opensearch.client.client.requests")
    def test_search_payload_with_no_filters(self, mock_requests):
        """Verify the payload uses ``match_all`` when no filters are provided."""
        mock_requests.post.return_value = FakeResponse({"hits": {"hits": []}})
        self.client.find("weather")
        mock_requests.post.assert_called_with(
            url="http://localhost:9200/weather-*/_search",
            json={"query": {"match_all": {}}},
            auth=None,
            verify=False,
        )
