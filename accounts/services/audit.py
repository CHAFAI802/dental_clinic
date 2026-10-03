from typing import Any

from accounts.models import AuditLog


def log_audit(
    *,
    action: str,
    model_name: str,
    object_id: str | int | None = None,
    user=None,
    changes: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Create a centralized audit trail entry."""

    return AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id is not None else None,
        changes=changes or {},
        context=context or {},
        ip_address=ip_address,
    )
