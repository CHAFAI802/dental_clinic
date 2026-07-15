#!/usr/bin/env python3

import json
import mimetypes
from multiprocessing import context
import os
import re
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path 


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dental_clinic.settings")

import django

django.setup()

from django.apps import apps
from django.db import models 
from accounts.models import AuditLog
from django.urls import URLPattern, URLResolver, get_resolver

API_BASE = os.getenv("API_BASE", "http://web:8000").rstrip("/")
EMAIL = os.getenv("API_EMAIL")
PASSWORD = os.getenv("API_PASSWORD")
LOGIN_URL = f"{API_BASE}/api/auth/login/"

SUCCESS_CODES = {200, 201, 204}
SMOKE_ID = uuid.uuid4().hex[:12]
NAMED_GROUP_PATTERN = re.compile(r"\(\?P<(?P<name>\w+)>[^)]+\)")

METHOD_ORDER = {
    "list": 0,
    "create": 1,
    "retrieve": 2,
    "update": 3,
    "partial_update": 4,
    "destroy": 5,
}

created_resources = []
orm_prerequisites = []


def request(url, token=None, data=None, method="GET", files=None):
    headers = {"Accept": "application/json"}

    if token:
        headers["Authorization"] = f"Token {token}"

    body = None

    if files:
        boundary = f"----DentalSmoke{uuid.uuid4().hex}"
        body = build_multipart(data or {}, files, boundary)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method,
    )

    return urllib.request.urlopen(req, timeout=20)


def build_multipart(data, files, boundary):
    chunks = []

    for name, value in data.items():
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
            str(value).encode(),
            b"\r\n",
        ])

    for name, file_info in files.items():
        filename, content = file_info
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            (
                f'Content-Disposition: form-data; name="{name}"; '
                f'filename="{filename}"\r\n'
            ).encode(),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            content,
            b"\r\n",
        ])

    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks)


def read_json(response):
    if response.status == 204:
        return None

    raw = response.read()

    if not raw:
        return None

    return json.loads(raw.decode("utf-8"))


def login():
    if not EMAIL or not PASSWORD:
        print("[FATAL] API_EMAIL and API_PASSWORD are required")
        sys.exit(1)

    try:
        with request(
            LOGIN_URL,
            data={"email": EMAIL, "password": PASSWORD},
            method="POST",
        ) as response:
            payload = read_json(response)
    except urllib.error.HTTPError as exc:
        print(f"[FATAL] Login failed: HTTP {exc.code}")
        print(exc.read().decode("utf-8", errors="replace"))
        sys.exit(1)

    token = payload.get("token")

    if not token:
        print("[FATAL] Login response does not contain a token")
        print(payload)
        sys.exit(1)

    print(f"[OK] Authenticated as {EMAIL}")
    return token


def walk_patterns(patterns, prefix=""):
    for pattern in patterns:
        route = prefix + str(pattern.pattern)

        if isinstance(pattern, URLResolver):
            yield from walk_patterns(pattern.url_patterns, route)
        elif isinstance(pattern, URLPattern):
            yield route, pattern


def normalize_route(route):
    route = route.removeprefix("^").removesuffix("$")
    return route.replace("/^", "/")


def discover_operations():
    discovered = {}

    for route, pattern in walk_patterns(get_resolver().url_patterns):
        route = normalize_route(route)

        if not route.startswith("api/") or "(?P<format>" in route:
            continue

        callback = pattern.callback
        actions = getattr(callback, "actions", None)

        if not actions:
            continue

        for method, action in actions.items():
            key = (callback.__name__, method.upper(), action)

            discovered[key] = {
                "viewset": callback.__name__,
                "method": method.upper(),
                "action": action,
                "route": route,
                "callback": callback,
            }

    return sorted(
        discovered.values(),
        key=lambda item: (
            item["viewset"],
            METHOD_ORDER.get(item["action"], 99),
            item["method"],
        ),
    )


def operation_map(operations):
    mapped = {}

    for operation in operations:
        mapped.setdefault(operation["viewset"], {})[operation["action"]] = operation

    return mapped


def route_to_path(route, lookup_value=None):
    resolved = route

    for match in list(NAMED_GROUP_PATTERN.finditer(route)):
        parameter = match.group("name")

        if parameter == "format":
            continue

        if lookup_value is None:
            return None

        resolved = resolved.replace(match.group(0), str(lookup_value), 1)

    path = "/" + resolved.lstrip("/")

    if not path.endswith("/"):
        path += "/"

    return path


def get_view_model(callback):
    view_class = getattr(callback, "cls", None)

    if view_class is None:
        return None

    queryset = getattr(view_class, "queryset", None)

    if queryset is not None:
        return queryset.model

    serializer_class = getattr(view_class, "serializer_class", None)
    meta = getattr(serializer_class, "Meta", None)

    return getattr(meta, "model", None)


def first_lookup_value(operation):
    model = get_view_model(operation["callback"])

    if model is None:
        return None

    obj = model._default_manager.first()

    if obj is None:
        return None

    lookup_field = getattr(operation["callback"].cls, "lookup_field", "pk")
    return getattr(obj, lookup_field, None)


def api_url(operation, lookup_value=None):
    path = route_to_path(operation["route"], lookup_value)

    if path is None:
        return None

    return f"{API_BASE}{path}"


def payloads(context):
    sid = SMOKE_ID

    return {
        "UserViewSet": {
            "create": {
                "email": f"smoke_{sid}@example.com",
                "password": f"Smoke-{sid}-Pass9!",
                "first_name": "Smoke",
                "last_name": "User",
                "role": "dentist",
            },
            "put": {
                "email": f"smoke_{sid}@example.com",
                "password": f"Smoke-{sid}-Pass9!",
                "first_name": "SmokePut",
                "last_name": "User",
                "role": "dentist",
            },
            "patch": {"first_name": "SmokePatch"},
        },
        "PatientViewSet": {
            "create": {
                "first_name": "Smoke",
                "last_name": f"Patient{sid}",
                "birthdate": "1990-01-01",
                "gender": "other",
                "phone": f"+213{sid[:9]}",
            },
            "put": {
                "first_name": "SmokePut",
                "last_name": f"Patient{sid}",
                "birthdate": "1990-01-01",
                "gender": "other",
                "phone": f"+213{sid[:9]}",
            },
            "patch": {"first_name": "SmokePatch"},
        },
        "RoomViewSet": {
            "create": {"name": f"Smoke Room {sid}"},
            "put": {"name": f"Smoke Room PUT {sid}", "capacity": 2},
            "patch": {"capacity": 3},
        },
        "AppointmentViewSet": {
            "create": {
                "start_at": "2035-01-15T09:00:00Z",
                "end_at": "2035-01-15T09:30:00Z",
                "patient": context["PatientViewSet"],
                "practitioner": context["UserViewSet"],
                "room": context["RoomViewSet"],
            },
            "put": {
                "start_at": "2035-01-15T10:00:00Z",
                "end_at": "2035-01-15T10:30:00Z",
                "patient": context["PatientViewSet"],
                "practitioner": context["UserViewSet"],
                "room": context["RoomViewSet"],
                "status": "pending",
            },
            "patch": {"status": "confirmed"},
        },
        "OdontogramViewSet": {
            "create": {"patient": context["PatientViewSet"], "notes": f"smoke {sid}"},
            "put": {"patient": context["PatientViewSet"], "notes": f"smoke put {sid}", "version": 1},
            "patch": {"notes": f"smoke patch {sid}"},
        },
        "ToothViewSet": {
            "create": {
                "number": "11",
                "type": "incisor",
                "status": "healthy",
                "odontogram": context["OdontogramViewSet"],
            },
            "put": {
                "number": "11",
                "type": "incisor",
                "status": "treated",
                "odontogram": context["OdontogramViewSet"],
            },
            "patch": {"remarks": f"smoke patch {sid}"},
        },
        "TreatmentPlanViewSet": {
            "create": {"status": "draft", "patient": context["PatientViewSet"]},
            "put": {"status": "active", "patient": context["PatientViewSet"], "notes": f"smoke put {sid}"},
            "patch": {"notes": f"smoke patch {sid}"},
        },
        "TreatmentViewSet": {
            "create": {
                "status": "planned",
                "category": "consultation",
                "code": f"SMK-{sid}",
                "label": "Smoke treatment",
                "patient": context["PatientViewSet"],
                "dentist": context["UserViewSet"],
                "appointment": context["AppointmentViewSet"],
                "treatment_plan": context["TreatmentPlanViewSet"],
            },
            "put": {
                "status": "completed",
                "category": "consultation",
                "code": f"SMK-{sid}",
                "label": "Smoke treatment PUT",
                "patient": context["PatientViewSet"],
                "dentist": context["UserViewSet"],
                "appointment": context["AppointmentViewSet"],
                "treatment_plan": context["TreatmentPlanViewSet"],
            },
            "patch": {"label": "Smoke treatment PATCH"},
        },
        "PrescriptionTemplateViewSet": {
            "create": {"name": f"Smoke prescription {sid}", "content": "Smoke {{patient}}"},
            "put": {"name": f"Smoke prescription PUT {sid}", "content": "Smoke PUT {{patient}}"},
            "patch": {"description": f"smoke patch {sid}"},
        },
        "PrescriptionViewSet": {
            "create": {
                "status": "draft",
                "patient": context["PatientViewSet"],
                "dentist": context["UserViewSet"],
                "template": context["PrescriptionTemplateViewSet"],
            },
            "put": {
                "status": "generated",
                "patient": context["PatientViewSet"],
                "dentist": context["UserViewSet"],
                "template": context["PrescriptionTemplateViewSet"],
                "notes": f"smoke put {sid}",
            },
            "patch": {"notes": f"smoke patch {sid}"},
        },
        "InvoiceViewSet": {
            "create": {
                "issued_at": "2035-01-15",
                "due_date": "2035-02-15",
                "status": "draft",
                "reference_number": f"SMK-INV-{sid}",
                "patient": context["PatientViewSet"],
                "related_treatment_plan": context["TreatmentPlanViewSet"],
            },
            "put": {
                "issued_at": "2035-01-15",
                "due_date": "2035-02-20",
                "status": "issued",
                "reference_number": f"SMK-INV-{sid}",
                "patient": context["PatientViewSet"],
                "related_treatment_plan": context["TreatmentPlanViewSet"],
            },
            "patch": {"notes": f"smoke patch {sid}"},
        },
        "PaymentViewSet": {
            "create": {
                "payment_at": "2035-01-16T10:00:00Z",
                "amount": "1.00",
                "method": "cash",
                "status": "completed",
                "invoice": context["InvoiceViewSet"],
                "patient": context["PatientViewSet"],
            },
            "put": {
                "payment_at": "2035-01-16T10:00:00Z",
                "amount": "2.00",
                "method": "cash",
                "status": "completed",
                "invoice": context["InvoiceViewSet"],
                "patient": context["PatientViewSet"],
            },
            "patch": {"reference": f"SMK-PAY-{sid}"},
        },
        "DocumentTemplateViewSet": {
            "create": {"name": f"Smoke document {sid}", "content": "Smoke content"},
            "put": {"name": f"Smoke document PUT {sid}", "content": "Smoke PUT content"},
            "patch": {"description": f"smoke patch {sid}"},
        },
        "DocumentViewSet": {
            "create": {
                "document_type": "other",
                "title": f"Smoke document {sid}",
                "content": "Smoke content",
                "status": "draft",
                "patient": context["PatientViewSet"],
                "template": context["DocumentTemplateViewSet"],
            },
            "put": {
                "document_type": "other",
                "title": f"Smoke document PUT {sid}",
                "content": "Smoke PUT content",
                "status": "draft",
                "patient": context["PatientViewSet"],
                "template": context["DocumentTemplateViewSet"],
            },
            "patch": {"title": f"Smoke document PATCH {sid}"},
        },
        "InventoryItemViewSet": {
            "create": {"sku": f"SMK-{sid}", "name": f"Smoke item {sid}", "unit": "unit"},
            "put": {"sku": f"SMK-{sid}", "name": f"Smoke item PUT {sid}", "unit": "unit"},
            "patch": {"description": f"smoke patch {sid}"},
        },
        "StaffProfileViewSet": {
            "create": {
                "employee_number": f"SMK-{sid}",
                "hire_date": "2035-01-01",
                "department": "dental",
                "job_title": "dentist",
                "employment_type": "full_time",
                "status": "active",
                "user": context["UserViewSet"],
            },
            "put": {
                "employee_number": f"SMK-{sid}",
                "hire_date": "2035-01-01",
                "department": "dental",
                "job_title": "senior dentist",
                "employment_type": "full_time",
                "status": "active",
                "user": context["UserViewSet"],
            },
            "patch": {"notes": f"smoke patch {sid}"},
        },
        "ReportDefinitionViewSet": {
            "create": {"name": f"Smoke report {sid}", "query_type": "smoke"},
            "put": {"name": f"Smoke report PUT {sid}", "query_type": "smoke"},
            "patch": {"description": f"smoke patch {sid}"},
        },
        "NotificationTemplateViewSet": {
            "create": {"name": f"Smoke notification {sid}", "channel": "email", "body": "Smoke body"},
            "put": {"name": f"Smoke notification PUT {sid}", "channel": "email", "body": "Smoke PUT body"},
            "patch": {"subject": f"Smoke patch {sid}"},
        },
        "NotificationViewSet": {
            "create": {
                "channel": "email",
                "status": "pending",
                "recipient_user": context["UserViewSet"],
                "recipient_patient": context["PatientViewSet"],
                "template": context["NotificationTemplateViewSet"],
            },
            "put": {
                "channel": "email",
                "status": "pending",
                "recipient_user": context["UserViewSet"],
                "recipient_patient": context["PatientViewSet"],
                "template": context["NotificationTemplateViewSet"],
                "payload": {"smoke": sid},
            },
            "patch": {"error_message": f"smoke patch {sid}"},
        },
        "ImagingStudyViewSet": {
            "create": {
                "study_type": "panoramic",
                "study_date": "2035-01-15T10:00:00Z",
                "status": "pending",
                "patient": context["PatientViewSet"],
                "practitioner": context["UserViewSet"],
            },
            "put": {
                "study_type": "panoramic",
                "study_date": "2035-01-15T10:00:00Z",
                "status": "completed",
                "patient": context["PatientViewSet"],
                "practitioner": context["UserViewSet"],
                "description": f"smoke put {sid}",
            },
            "patch": {"description": f"smoke patch {sid}"},
        },
        "ImagingInstanceViewSet": {
            "create": {
                "instance_number": 900001,
                "file_type": "text/plain",
                "study_date": "2035-01-15T10:00:00Z",
                "series": context["ImagingSeries"],
            },
            "put": {
                "instance_number": 900002,
                "file_type": "text/plain",
                "study_date": "2035-01-15T10:00:00Z",
                "series": context["ImagingSeries"],
                "notes": f"smoke put {sid}",
            },
            "patch": {"notes": f"smoke patch {sid}"},
            "files": {"file": (f"smoke_{sid}.txt", b"Dental smoke test temporary file\n")},
        },
    }


CREATE_ORDER = [
    "UserViewSet",
    "PatientViewSet",
    "RoomViewSet",
    "AppointmentViewSet",
    "OdontogramViewSet",
    "ToothViewSet",
    "TreatmentPlanViewSet",
    "TreatmentViewSet",
    "PrescriptionTemplateViewSet",
    "PrescriptionViewSet",
    "InvoiceViewSet",
    "PaymentViewSet",
    "DocumentTemplateViewSet",
    "DocumentViewSet",
    "InventoryItemViewSet",
    "StaffProfileViewSet",
    "ReportDefinitionViewSet",
    "NotificationTemplateViewSet",
    "NotificationViewSet",
    "ImagingStudyViewSet",
    "ImagingInstanceViewSet",
]


def log_ok(status, method, action, viewset, url):
    print(f"[OK]   {status:<3}  {method:<7} {action.upper():<18} {viewset:<35} {url}")


def log_fail(method, action, viewset, url, detail):
    print(f"[FAIL]      {method:<7} {action.upper():<18} {viewset:<35} {url}")
    if detail:
        print(f"             {detail[:1000]}")


def execute(operation, token, data=None, lookup_value=None, files=None):
    url = api_url(operation, lookup_value)

    try:
        with request(
            url,
            token=token,
            data=data,
            method=operation["method"],
            files=files,
        ) as response:
            status = response.status
            payload = read_json(response)

        if status not in SUCCESS_CODES:
            log_fail(operation["method"], operation["action"], operation["viewset"], url, f"HTTP {status}")
            return False, payload

        log_ok(status, operation["method"], operation["action"], operation["viewset"], url)
        return True, payload

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        log_fail(operation["method"], operation["action"], operation["viewset"], url, f"HTTP {exc.code}: {body}")
        return False, None
    except Exception as exc:
        log_fail(operation["method"], operation["action"], operation["viewset"], url, str(exc))
        return False, None


def create_imaging_series(study_id):
    model = apps.get_model("imaging", "ImagingSeries")
    values = {}

    for field in model._meta.concrete_fields:
        if field.primary_key or field.auto_created or field.has_default() or field.null:
            continue

        if field.is_relation:
            related_model = field.remote_field.model

            if related_model._meta.label_lower == "imaging.imagingstudy":
                values[field.name] = related_model._default_manager.get(pk=study_id)
                continue

            obj = related_model._default_manager.first()
            if obj is None:
                raise RuntimeError(
                    f"Cannot build ImagingSeries: required relation "
                    f"{field.name} -> {related_model._meta.label}"
                )
            values[field.name] = obj
            continue

        if isinstance(field, (models.CharField, models.TextField)):
            values[field.name] = f"smoke_{SMOKE_ID}"
        elif isinstance(field, models.IntegerField):
            values[field.name] = 1
        elif isinstance(field, models.BooleanField):
            values[field.name] = False
        elif isinstance(field, models.DateTimeField):
            from django.utils import timezone
            values[field.name] = timezone.now()
        elif isinstance(field, models.DateField):
            from django.utils import timezone
            values[field.name] = timezone.now().date()
        elif isinstance(field, models.DecimalField):
            values[field.name] = 0
        else:
            raise RuntimeError(
                f"Cannot auto-build ImagingSeries field "
                f"{field.name} ({field.__class__.__name__})"
            )

    obj = model._default_manager.create(**values)
    orm_prerequisites.append(obj)
    print(f"[FIXTURE] ORM ImagingSeries pk={obj.pk}")
    return obj.pk


def verify_patch(payload, expected):
    if not isinstance(payload, dict):
        return False, "PATCH response is not a JSON object"

    for field, expected_value in expected.items():
        actual = payload.get(field)

        if str(actual) != str(expected_value):
            return False, (
                f"{field}: expected {expected_value!r}, got {actual!r}"
            )

    return True, None


def cleanup(token, operations):
    print("=" * 130)
    print("[INFO] Reverse cleanup")

    for viewset, object_id in reversed(created_resources):
        destroy = operations.get(viewset, {}).get("destroy")

        if destroy is None:
            continue

        url = api_url(destroy, object_id)

        try:
            with request(url, token=token, method="DELETE") as response:
                print(f"[CLEANUP] HTTP {response.status} {viewset:<35} {url}")
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                print(f"[WARN] Cleanup HTTP {exc.code} {viewset:<35} {url}")
        except Exception as exc:
            print(f"[WARN] Cleanup {viewset:<35} {exc}")

    for obj in reversed(orm_prerequisites):
        try:
            label = obj._meta.label
            pk = obj.pk
            obj.delete()
            print(f"[CLEANUP] ORM {label} pk={pk}")
        except Exception as exc:
            print(f"[WARN] ORM cleanup {obj._meta.label}: {exc}") 


def create_audit_log_fixture():
    audit_log = AuditLog.objects.create(
        user=None,
        action="smoke_test",
        model_name="SmokeTest",
        object_id=None,
        changes={
            "smoke_test": SMOKE_ID,
        },
        context="smoke_test",
        ip_address=None,
        sensitive=False,
    )

    print(
        f"[FIXTURE] ORM AuditLog pk={audit_log.pk}"
    )

    return audit_log


def main():
    print("=" * 130)
    print("Dental API Full CRUD Smoke Test")
    print(f"API base: {API_BASE}")
    print(f"Smoke ID: {SMOKE_ID}")
    print("=" * 130)

    token = login()
    discovered = discover_operations()
    operations = operation_map(discovered)

    print(f"[INFO] Discovered {len(discovered)} unique HTTP operations")
    print(f"[INFO] ViewSets: {len(operations)}")
    print("=" * 130)

    results = {"passed": 0, "failed": 0}
    context = {
    viewset: None
    for viewset in CREATE_ORDER
}

    context["ImagingSeries"] = None


    try:
        # Test every LIST operation first.
        for viewset in sorted(operations):
            operation = operations[viewset].get("list")

            if operation:
                ok, _ = execute(operation, token)
                results["passed" if ok else "failed"] += 1

        # CRUD resources in dependency order.
        for viewset in CREATE_ORDER:
            view_operations = operations.get(viewset)

            if not view_operations:
                print(f"[FAIL]      DISCOVERY {'MISSING':<18} {viewset}")
                continue

            if viewset == "ImagingInstanceViewSet":
                context["ImagingSeries"] = create_imaging_series(
                    context["ImagingStudyViewSet"]
                )

            scenario = payloads(context)[viewset]

            create = view_operations["create"]
            ok, created = execute(
                create,
                token,
                data=scenario["create"],
                files=scenario.get("files"),
            )
            results["passed" if ok else "failed"] += 1

            if not ok or not isinstance(created, dict) or "id" not in created:
                raise RuntimeError(f"{viewset}: CREATE failed; dependency chain stopped")

            object_id = created["id"]
            context[viewset] = object_id
            created_resources.append((viewset, object_id))

            retrieve = view_operations["retrieve"]
            ok, _ = execute(retrieve, token, lookup_value=object_id)
            results["passed" if ok else "failed"] += 1

            update = view_operations["update"]
            ok, _ = execute(
                update,
                token,
                data=scenario["put"],
                lookup_value=object_id,
                files=scenario.get("files"),
            )
            results["passed" if ok else "failed"] += 1

            patch = view_operations["partial_update"]
            ok, patched = execute(
                patch,
                token,
                data=scenario["patch"],
                lookup_value=object_id,
            )

            if ok:
                valid, detail = verify_patch(patched, scenario["patch"])

                if not valid:
                    log_fail("PATCH", "partial_update validation", viewset, api_url(patch, object_id), detail)
                    ok = False

            results["passed" if ok else "failed"] += 1

        # Read-only detail operations are tested after CRUD activity,
        # so audit systems have had a chance to create rows.
        # Read-only detail operations.
                # Read-only detail operations.
        for viewset, view_operations in sorted(operations.items()):
            if "create" in view_operations:
                continue

            retrieve = view_operations.get("retrieve")

            if not retrieve:
                continue

            fixture = None

            try:
                if viewset == "AuditLogViewSet":
                    fixture = create_audit_log_fixture()
                    lookup_value = fixture.pk
                else:
                    lookup_value = first_lookup_value(retrieve)

                if lookup_value is None:
                    log_fail(
                        "GET",
                        "retrieve",
                        viewset,
                        api_url(retrieve),
                        "no database object available",
                    )
                    results["failed"] += 1
                    continue

                ok, _ = execute(
                    retrieve,
                    token,
                    lookup_value=lookup_value,
                )

                results["passed" if ok else "failed"] += 1

            finally:
                if fixture is not None:
                    fixture_pk = fixture.pk
                    fixture.delete()

                    print(
                        "[CLEANUP] ORM "
                        f"accounts.AuditLog pk={fixture_pk}"
                    )

        # DESTROY in reverse dependency order.
        for viewset, object_id in reversed(created_resources.copy()):
            destroy = operations[viewset]["destroy"]
            ok, _ = execute(destroy, token, lookup_value=object_id)
            results["passed" if ok else "failed"] += 1

            if ok:
                created_resources.remove((viewset, object_id))

    except Exception as exc:
        print(f"[FATAL] {exc}")
        results["failed"] += 1

    finally:
        cleanup(token, operations)

    total = len(discovered)

    print("=" * 130)
    print(f"ROUTES      : {total}")
    print(f"PASSED      : {results['passed']}")
    print(f"FAILED      : {results['failed']}")
    print("SKIPPED     : 0")
    print("=" * 130)

    if results["failed"] == 0 and results["passed"] == total:
        print("BACKEND API CRUD SURFACE VERIFIED")
    else:
        print("BACKEND API CRUD SURFACE NOT VERIFIED")

    print("=" * 130)

    sys.exit(1 if results["failed"] or results["passed"] != total else 0)


if __name__ == "__main__":
    main()
