"""Offline unit tests for project-level ``apbs`` routing and error pages.

These tests use Django's test client only; no external services are touched.
"""

from django.test import SimpleTestCase, override_settings
from django.urls import resolve, reverse


class RootRedirectTests(SimpleTestCase):
    def test_root_redirects_to_search(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "search/")


class I18nSetLanguageTests(SimpleTestCase):
    def test_set_language_url_is_wired(self):
        self.assertEqual(reverse("set_language"), "/i18n/setlang/")

    def test_set_language_switches_active_language(self):
        response = self.client.post(
            reverse("set_language"),
            data={"language": "de", "next": "/search/"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/search/")


class CrossNamespaceRoutingTests(SimpleTestCase):
    def test_search_and_camera_namespaces_resolve(self):
        self.assertEqual(resolve(reverse("search:index")).view_name, "search:index")
        self.assertEqual(resolve(reverse("camera:index")).view_name, "camera:index")


@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
class Custom404Tests(SimpleTestCase):
    def test_missing_page_uses_custom_404_template(self):
        response = self.client.get("/this/does/not/exist/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertContains(response, "Your request could not be processed", status_code=404)
        self.assertContains(response, "Page not found", status_code=404)
