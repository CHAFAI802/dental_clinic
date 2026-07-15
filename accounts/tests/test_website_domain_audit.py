from django.apps import apps
from django.test import SimpleTestCase
from django.urls import get_resolver

from website import models as website_models


class WebsiteDomainAuditTests(SimpleTestCase):
    """PHASE B11 characterization tests.

    These tests document the current website domain implementation.
    """

    def test_website_app_is_installed(self):
        self.assertTrue(apps.is_installed("website"))

    def test_website_app_has_no_concrete_domain_models(self):
        models = list(apps.get_app_config("website").get_models())
        self.assertEqual(models, [])

    def test_website_models_module_defines_no_django_models(self):
        concrete_models = [
            value
            for value in vars(website_models).values()
            if isinstance(value, type)
            and hasattr(value, "_meta")
            and value.__module__ == "website.models"
        ]
        self.assertEqual(concrete_models, [])

    def test_no_website_urlconf_is_included(self):
        route_strings = []

        def walk(patterns):
            for pattern in patterns:
                route_strings.append(str(pattern.pattern))
                children = getattr(pattern, "url_patterns", None)
                if children is not None:
                    walk(children)

        walk(get_resolver().url_patterns)

        self.assertFalse(
            any("website" in route.lower() for route in route_strings)
        )

    def test_public_surface_uses_spa_catch_all(self):
        patterns = get_resolver().url_patterns

        spa_patterns = [
            pattern
            for pattern in patterns
            if getattr(pattern, "name", None) == "spa"
        ]

        self.assertEqual(len(spa_patterns), 1)

        callback = spa_patterns[0].callback
        self.assertEqual(
            callback.view_initkwargs.get("template_name"),
            "public/app.html",
        )
