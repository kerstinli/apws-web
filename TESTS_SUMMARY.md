# Test Suite Summary

Offline, deterministic Django unit tests for the **apbs** project. The suite
requires **no OpenSearch instance, no live server and makes zero real network
calls**. Everything runs against mock data / fakes.

## Mock-data approach

- **OpenSearch client** — the production `OpenSearchClient.find/get` already
  return canned mock documents (weather + sensor indices, empty branch for
  unknown indices). Tests call these directly and assert on the fake docs. No
  HTTP layer is mocked for them because there is nothing to reach.
- **Payload construction** — the only method that would build a real HTTP call,
  `_execute_search`, is exercised by injecting a `FakeRequests` object (via
  `mock.patch` on the module's `requests` attribute) that records the URL and
  payload and returns a `FakeResponse`. No socket is opened; the http/https
  URL scheme, `{index}*/_search` path and `{"query": {"match": ...}}` payload
  are asserted.
- **QuerySet / manager delegation** — a `RecordingClient` fake is injected into
  `OpenSearchQuerySet` to verify `search`→`find` and `get`→`get` delegation and
  the empty-result branch. The manager's `get_queryset` is verified to build a
  real `OpenSearchClient` from settings (host/port/ssl).
- **Views** — driven with Django's test client. List views render against the
  canned multi-hit data; filter-forwarding and the empty-result branch are
  verified by patching `SearchDataManager.search` to capture kwargs / return
  `[]`. Detail views exercise the single-doc `get`.
- **Camera** — a `FakeCamera` feeds canned frames to the `gen` MJPEG generator
  (boundary framing + `None`-skip). `VideoCamera.get_frame` is built with
  `__new__` (so `cv2.VideoCapture(0)` is never called) and fed a `FakeVideo`;
  `cv2.imencode` is faked for success / read-fail / encode-fail. The
  `videostream` view is tested with `VideoCamera` replaced by a fake so no
  capture device is opened.
- **Project** — root redirect, i18n `set_language`, cross-namespace routing and
  the custom 404 page (`DEBUG=False`) via the test client only.

## Files added / changed

- `apbs/opensearch/tests.py` — regenerated (client, filter parsing, payload,
  queryset/manager delegation, all views, URL routing, `url_replace` tag).
- `apbs/camera/tests.py` — regenerated (`gen`, `VideoCamera.get_frame`, views,
  URL routing).
- `apbs/apbs/tests.py` — added (root redirect, i18n, namespaces, custom 404).
- `apbs/__init__.py` — removed (stray outer package marker that broke test
  discovery: `manage.py test` mis-resolved apps as `apbs.opensearch`).
- Production code otherwise untouched.

## Commands & results

```
uv run python manage.py test   ->  Ran 46 tests ... OK   (databases skipped)
uv run ruff check              ->  1 pre-existing error in opensearch/models.py
                                    (I001 import sort; present on HEAD, left as-is
                                    to keep the production change minimal)
uv run ruff check opensearch/tests.py camera/tests.py apbs/tests.py -> All checks passed
```

All 46 tests pass with the default database setup skipped (all tests use
`SimpleTestCase`). No OpenSearch instance and no network access are required.
