from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

from accounts.models import User
from accounts.services.login_history import get_client_ip, log_login_attempt


def normalize_login_email(email: str) -> str:
    """Normalize email the same way the login endpoint expects it."""
    return (email or '').strip().lower()


def authenticate_user(*, request, email: str, password: str) -> User | None:
    """Authenticate and return a user or None."""
    email = normalize_login_email(email)
    return authenticate(request, username=email, password=password)


def issue_token_for_user(user: User) -> str:
    """Return an existing token or create a new one (TokenAuthentication)."""
    token, _created = Token.objects.get_or_create(user=user)
    return token.key


def login_with_token(*, request, email: str, password: str) -> tuple[User | None, str | None]:
    """Authenticate a user, log the attempt and issue an auth token.

    Returns (user, token_key). If authentication fails, returns (None, None).
    """
    email = normalize_login_email(email)

    user = authenticate_user(request=request, email=email, password=password)

    if user is None or not user.is_active or user.is_deleted:
        existing_user = None
        try:
            existing_user = User.objects.get(email=email)
        except User.DoesNotExist:
            pass

        log_login_attempt(user=existing_user, request=request, successful=False)
        return None, None

    token_key = issue_token_for_user(user)

    user.last_login_ip = get_client_ip(request)
    user.save(update_fields=['last_login_ip'])

    log_login_attempt(user=user, request=request, successful=True)

    return user, token_key
