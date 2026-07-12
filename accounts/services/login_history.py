from django.utils import timezone

from accounts.models import UserLoginHistory


def get_client_ip(request) -> str | None:
    """Extract the most reliable client IP from request headers."""

    if request is None:
        return None

    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_login_attempt(*, user, request, successful: bool) -> UserLoginHistory:
    """Persist a login attempt (successful or not).

    If the email exists we keep the user FK even for failed attempts.
    """

    user_agent = ''
    if request is not None:
        user_agent = request.META.get('HTTP_USER_AGENT', '') or ''

    return UserLoginHistory.objects.create(
        user=user,
        login_at=timezone.now(),
        source_ip=get_client_ip(request),
        user_agent=user_agent[:512],
        successful=successful,
    )
