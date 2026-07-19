import datetime
from typing import Any

import requests
from requests import Response


class OpenSearchClient:
    def __init__(self, host: str, port: int, auth: dict[str, str], ssl: bool):
        self.host = host
        self.port = port
        self.use_ssl = ssl
        self.http_auth = auth
        # verify_certs = settings.OPENSEARCH_VERIFY_CERTS,
        # http_compress = True,
        # timeout = 30,

    def find(self, index: str, **kwargs) -> list[dict] | None:
        # response = self._execute_search(index, kwargs)
        # return response.json()

        if index == "weather":
            return [
                {
                    "name": "aussen",
                    "timestamp": datetime.datetime.strptime("01.05.2026 10:24:02", "%d.%m.%Y %H:%M:%S"),
                    "temperature": 17.5,
                    "humidity": 75.1,
                },
                {
                    "name": "aussen",
                    "timestamp": datetime.datetime.strptime("01.05.2026 13:30:43", "%d.%m.%Y %H:%M:%S"),
                    "temperature": 19.2,
                    "humidity": 75.1,
                },
                {
                    "name": "innen",
                    "timestamp": datetime.datetime.strptime("01.05.2026 11:24:02", "%d.%m.%Y %H:%M:%S"),
                    "temperature": 22.1,
                    "humidity": 75.1,
                },
                {
                    "name": "innen",
                    "timestamp": datetime.datetime.strptime("01.05.2026 13:01:51", "%d.%m.%Y %H:%M:%S"),
                    "temperature": 24.5,
                    "humidity": 75.1,
                },
            ]
        if index == "sensor":
            return [
                {"timestamp": datetime.datetime.strptime("01.05.2026 10:24:02", "%d.%m.%Y %H:%M:%S"), "value": 5},
                {"timestamp": datetime.datetime.strptime("01.05.2026 13:30:43", "%d.%m.%Y %H:%M:%S"), "value": 3},
                {"timestamp": datetime.datetime.strptime("01.05.2026 11:24:02", "%d.%m.%Y %H:%M:%S"), "value": 9},
                {"timestamp": datetime.datetime.strptime("01.05.2026 13:01:51", "%d.%m.%Y %H:%M:%S"), "value": 6},
            ]
        else:
            return []

    def get(self, index: str, **kwargs) -> dict | None:
        # response = self._execute_search(index, kwargs)
        # return response.json()[0]
        if index == "weather":
            return {
                "name": "aussen",
                "timestamp": datetime.datetime.strptime("01.05.2026 10:24:02", "%d.%m.%Y %H:%M:%S"),
                "temperature": 17.5,
                "humidity": 75.1,
            }
        if index == "sensor":
            return {"timestamp": datetime.datetime.strptime("01.05.2026 10:24:02", "%d.%m.%Y %H:%M:%S"), "value": 3}
        else:
            return {}

    def _execute_search(self, index: str, kwargs: dict[str, Any]) -> Response:
        filter_params = self._parse_filter_params(**kwargs)
        search_payload = {"query": {"match": filter_params}}
        response = requests.get(
            url=f"http{'s' if self.use_ssl else ''}://{self.host}:{self.port}/{index}*/_search", data=search_payload
        )
        # FIXME: ausgehend, wie die response aussieht, hier die ergebnisse aus dem json extrahieren !!!!!!!
        return response.json()

    @staticmethod
    def _parse_filter_params(**kwargs) -> dict:
        filter_params = {}
        for key in kwargs.keys():
            filter_params[key] = kwargs.get(key)
        return filter_params
