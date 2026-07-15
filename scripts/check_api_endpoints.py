#!/usr/bin/env python3

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "dental_clinic.settings",
)

import django

django.setup()

from django.urls import URLPattern, URLResolver, get_resolver


API_BASE = os.getenv("API_BASE", "http://web:8000")
EMAIL = os.getenv("API_EMAIL")
PASSWORD = os.getenv("API_PASSWORD")

LOGIN_URL = f"{API_BASE}/api/auth/login/"

SUCCESS_CODES = {200, 201, 204}

NAMED_GROUP_PATTERN = re.compile(
    r"\(\?P<(?P<name>\w+)>[^)]+\)"
)


def request(url, token=None, data=None):
    headers = {
        "Accept": "application/json",
    }

    if token:
        headers["Authorization"] = f"Token {token}"

    body = None
    method = "GET"

    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
        method = "POST"

    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method,
    )

    return urllib.request.urlopen(
        req,
        timeout=10,
    )


def login():
    if not EMAIL or not PASSWORD:
        print(
            "[FATAL] API_EMAIL and API_PASSWORD are required"
        )
        sys.exit(1)

    try:
        with request(
            LOGIN_URL,
            data={
                "email": EMAIL,
                "password": PASSWORD,
            },
        ) as response:
            payload = json.load(response)

    except urllib.error.HTTPError as exc:
        print(
            f"[FATAL] Login failed: HTTP {exc.code}"
        )

        print(
            exc.read().decode(
                "utf-8",
                errors="replace",
            )
        )

        sys.exit(1)

    token = payload.get("token")

    if not token:
        print(
            "[FATAL] Login response does not contain a token"
        )
        print(payload)
        sys.exit(1)

    print(
        f"[OK] Authenticated as {EMAIL}"
    )

    return token


def walk_patterns(patterns, prefix=""):
    endpoints = []

    for pattern in patterns:
        route = prefix + str(pattern.pattern)

        if isinstance(pattern, URLResolver):
            endpoints.extend(
                walk_patterns(
                    pattern.url_patterns,
                    route,
                )
            )

        elif isinstance(pattern, URLPattern):
            endpoints.append(
                (route, pattern)
            )

    return endpoints


def normalize_route(route):
    route = route.removeprefix("^")
    route = route.removesuffix("$")

    route = route.replace("/^", "/")

    return route

def classify_endpoint(callback):
    actions = getattr(
        callback,
        "actions",
        {},
    )

    get_action = actions.get("get")

    if get_action == "list":
        return "COLLECTION"

    if get_action == "retrieve":
        return "DETAIL"

    if get_action:
        return "ACTION"

    return None


def get_view_model(callback):
    view_class = getattr(
        callback,
        "cls",
        None,
    )

    if view_class is None:
        return None

    queryset = getattr(
        view_class,
        "queryset",
        None,
    )

    if queryset is not None:
        return queryset.model

    serializer_class = getattr(
        view_class,
        "serializer_class",
        None,
    )

    if serializer_class is None:
        return None

    meta = getattr(
        serializer_class,
        "Meta",
        None,
    )

    if meta is None:
        return None

    return getattr(
        meta,
        "model",
        None,
    )


def get_lookup_value(callback):
    model = get_view_model(callback)

    if model is None:
        return None

    try:
        obj = model._default_manager.first()

    except Exception:
        return None

    if obj is None:
        return None

    view_class = callback.cls

    lookup_field = getattr(
        view_class,
        "lookup_field",
        "pk",
    )

    return getattr(
        obj,
        lookup_field,
        None,
    )


def resolve_route(
    route,
    callback,
    endpoint_type,
):
    if endpoint_type == "COLLECTION":
        return route

    matches = list(
        NAMED_GROUP_PATTERN.finditer(route)
    )

    if not matches:
        return route

    lookup_value = get_lookup_value(
        callback
    )

    if lookup_value is None:
        return None

    resolved = route

    for match in matches:
        parameter = match.group("name")

        if parameter == "format":
            continue

        resolved = resolved.replace(
            match.group(0),
            str(lookup_value),
            1,
        )

    return resolved


def discover_api_endpoints():
    resolver = get_resolver()

    discovered = {}

    patterns = walk_patterns(
        resolver.url_patterns
    )

    for route, pattern in patterns:
        route = normalize_route(route)

        if not route.startswith("api/"):
            continue

        if "(?P<format>" in route:
            continue

        callback = pattern.callback

        actions = getattr(
            callback,
            "actions",
            None,
        )

        if not actions:
            continue

        if "get" not in actions:
            continue

        endpoint_type = classify_endpoint(
            callback
        )

        if endpoint_type is None:
            continue

        resolved_route = resolve_route(
            route,
            callback,
            endpoint_type,
        )

        path = None

        if resolved_route is not None:
            path = "/" + resolved_route.lstrip("/")

            if not path.endswith("/"):
                path += "/"

        key = (
            endpoint_type,
            route,
            callback.__name__,
        )

        discovered[key] = {
            "path": path,
            "name": callback.__name__,
            "type": endpoint_type,
            "route": route,
        }

    return sorted(
        discovered.values(),
        key=lambda item: (
            item["type"],
            item["route"],
        ),
    )


def check_endpoint(endpoint, token):
    path = endpoint["path"]
    name = endpoint["name"]
    endpoint_type = endpoint["type"]

    if path is None:
        print(
            f"[SKIP]      "
            f"{endpoint_type:<12} "
            f"{name:<35} "
            f"{endpoint['route']} "
            f"(no database object)"
        )

        return "skipped"

    url = f"{API_BASE}{path}"

    try:
        with request(
            url,
            token=token,
        ) as response:
            status = response.status

        if status in SUCCESS_CODES:
            print(
                f"[OK]   {status}  "
                f"{endpoint_type:<12} "
                f"{name:<35} "
                f"{url}"
            )

            return "passed"

        print(
            f"[FAIL] {status}  "
            f"{endpoint_type:<12} "
            f"{name:<35} "
            f"{url}"
        )

        return "failed"

    except urllib.error.HTTPError as exc:
        print(
            f"[FAIL] {exc.code}  "
            f"{endpoint_type:<12} "
            f"{name:<35} "
            f"{url}"
        )

        body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        if body:
            print(
                f"             {body[:500]}"
            )

        return "failed"

    except Exception as exc:
        print(
            f"[ERROR]      "
            f"{endpoint_type:<12} "
            f"{name:<35} "
            f"{url}"
        )

        print(
            f"             {exc}"
        )

        return "failed"


def main():
    print("=" * 130)
    print(
        "Dental API Route Smoke Test"
    )
    print(
        f"API base: {API_BASE}"
    )
    print("=" * 130)

    token = login()

    endpoints = discover_api_endpoints()

    collections = sum(
        endpoint["type"] == "COLLECTION"
        for endpoint in endpoints
    )

    details = sum(
        endpoint["type"] == "DETAIL"
        for endpoint in endpoints
    )

    actions = sum(
        endpoint["type"] == "ACTION"
        for endpoint in endpoints
    )

    print(
        f"[INFO] Discovered "
        f"{len(endpoints)} GET routes"
    )

    print(
        f"[INFO] Collections: {collections} | "
        f"Details: {details} | "
        f"Actions: {actions}"
    )

    print("=" * 130)

    results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
    }

    for endpoint in endpoints:
        result = check_endpoint(
            endpoint,
            token,
        )

        results[result] += 1

    print("=" * 130)

    print(
        f"TOTAL   : {len(endpoints)}"
    )

    print(
        f"PASSED  : {results['passed']}"
    )

    print(
        f"FAILED  : {results['failed']}"
    )

    print(
        f"SKIPPED : {results['skipped']}"
    )

    print("=" * 130)

    sys.exit(
        1 if results["failed"] else 0
    )


if __name__ == "__main__":
    main()