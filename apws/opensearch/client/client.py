
import requests


class OpenSearchClient:
    def __init__(self, host: str, port: int, auth: tuple[str, str] | None, ssl: bool, ssl_verify: bool):
        self.host = host
        self.port = port
        self.use_ssl = ssl
        self.ssl_verify = ssl_verify
        self.http_auth = auth

    def find(self, index: str, **kwargs) -> list[dict]:
        """Find multiple documents matching a query."""
        response = requests.post(
            url=f"http{'s' if self.use_ssl else ''}://{self.host}:{self.port}/{index}-*/_search",
            json={"query": {"match_all": {}}},
            auth=self.http_auth,
            verify=self.ssl_verify
        )
        response.raise_for_status()
        hits = response.json()["hits"]["hits"]
        return [hit["_source"] for hit in hits]

    def get(self, index: str, **kwargs) -> dict | None:
        """Find a single document matching a query."""
        filter_params = self._parse_filter_params(**kwargs)

        must_clauses = [{"match": {key: value}} for key, value in filter_params.items()]
        search_payload = {"query": {"bool": {"must": must_clauses}}}

        response = requests.post(
            url=f"http{'s' if self.use_ssl else ''}://{self.host}:{self.port}/{index}-*/_search",
            json=search_payload,
            auth=self.http_auth,
            verify=self.ssl_verify
        )
        response.raise_for_status()
        hits = response.json()["hits"]["hits"]
        results = [hit["_source"] for hit in hits]
        return results[0] if results else None


    @staticmethod
    def _parse_filter_params(**kwargs) -> dict[str, str]:
        return {key: value for key, value in kwargs.items() if value is not None}
