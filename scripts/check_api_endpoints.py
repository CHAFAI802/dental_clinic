#!/usr/bin/env python3

import json
import os
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

from django.urls import URLPattern, URLResolver, get_resolver
django.setup()




API_BASE = os.getenv("API_BASE", "http://web:8000")
EMAIL = os.getenv("API_EMAIL")
PASSWORD = os.getenv("API_PASSWORD")

LOGIN_URL = f"{API_BASE}/api/auth/login/"
SUCCESS_CODES = {200, 201, 204}


def request(url, token=None, data=None):
    headers = {"Accept": "application/json"}

    if token:
        headers["Authorization"] = f"Token {token}"

    body = None

    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method="POST" if data is not None else "GET",
    )

    return urllib.request.urlopen(req, timeout=10)


def login():
    if not EMAIL or not PASSWORD:
        print("[FATAL] API_EMAIL and API_PASSWORD are required")
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
        print(f"[FATAL] Login failed: HTTP {exc.code}")
        print(exc.read().decode("utf-8", errors="replace"))
        sys.exit(1)

    token = payload.get("token")

    if not token:
        print("[FATAL] Login response does not contain a token")
        sys.exit(1)

    print(f"[OK] Authenticated as {EMAIL}")

    return token


def walk_patterns(patterns, prefix=""):
    endpoints = []

    for pattern in patterns:
        route = prefix + str(pattern.pattern)

        if isinstance(pattern, URLResolver):
            endpoints.extend(
                walk_patterns(pattern.url_patterns, route)
            )

        elif isinstance(pattern, URLPattern):
            endpoints.append((route, pattern))

    return endpoints


def discover_api_endpoints():
    resolver = get_resolver()

    discovered = {}

    for route, pattern in walk_patterns(resolver.url_patterns):
        route = route.replace("^", "").replace("$", "")

        if not route.startswith("api/"):
            continue

        if "<" in route or "(?P<" in route:
            continue

        if route.endswith(".<format>"):
            continue

        callback = pattern.callback

        actions = getattr(callback, "actions", None)

        if not actions:
            continue

        if "get" not in actions:
            continue

        path = "/" + route.lstrip("/")

        if not path.endswith("/"):
            path += "/"

        discovered[path] = callback.__name__

    return sorted(discovered.items())


def check_endpoint(path, name, token):
    url = f"{API_BASE}{path}"

    try:
        with request(url, token=token) as response:
            status = response.status

        if status in SUCCESS_CODES:
            print(f"[OK]   {status}  {name:<35} {url}")
            return True

        print(f"[FAIL] {status}  {name:<35} {url}")
        return False

    except urllib.error.HTTPError as exc:
        print(f"[FAIL] {exc.code}  {name:<35} {url}")
        return False

    except Exception as exc:
        print(f"[ERROR]      {name:<35} {url}")
        print(f"             {exc}")
        return False


def main():
    print("=" * 110)
    print("Dental API Endpoint Smoke Test")
    print(f"API base: {API_BASE}")
    print("=" * 110)

    token = login()
    endpoints = discover_api_endpoints()

    print(f"[INFO] Discovered {len(endpoints)} GET collection endpoints")
    print("=" * 110)

    passed = 0
    failed = 0

    for path, name in endpoints:
        if check_endpoint(path, name, token):
            passed += 1
        else:
            failed += 1

    print("=" * 110)
    print(f"TOTAL  : {passed + failed}")
    print(f"PASSED : {passed}")
    print(f"FAILED : {failed}")
    print("=" * 110)

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()