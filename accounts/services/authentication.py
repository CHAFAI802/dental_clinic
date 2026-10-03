from django.contrib.auth import authenticate
from django.utils import timezone
import hashlib
import secrets
from datetime import timedelta
from accounts.models import AuthenticationSession, User
from accounts.services.login_history import get_client_ip, log_login_attempt



def normalize_login_email(email: str) -> str:
    """Normalize email the same way the login endpoint expects it."""
    return (email or '').strip().lower()


def authenticate_user(*, request, email: str, password: str) -> User | None:
    """Authenticate and return a user or None."""
    email = normalize_login_email(email)
    return authenticate(request, username=email, password=password)


AUTHENTICATION_SESSION_LIFETIME = timedelta(hours=8)


def generate_authentication_credential() -> str:
    """Generate a cryptographically secure authentication credential."""
    return secrets.token_urlsafe(32)


def hash_authentication_credential(credential: str) -> str:
    """Return the SHA-256 hash of an authentication credential."""
    return hashlib.sha256(credential.encode("utf-8")).hexdigest()


def create_authentication_session(user: User) -> tuple[AuthenticationSession, str]:
    """
    Create a new authentication session and return the session plus
    the raw credential.

    The raw credential is returned to the caller only and is never stored
    in the database.
    """
    credential = generate_authentication_credential()
    token_hash = hash_authentication_credential(credential)
    now = timezone.now()

    session = AuthenticationSession.objects.create(
        user=user,
        token_hash=token_hash,
        created_at=now,
        expires_at=now + AUTHENTICATION_SESSION_LIFETIME,
    )

    return session, credential


def get_authentication_session(credential: str) -> AuthenticationSession | None:
    """Resolve a credential to a currently valid authentication session."""
    if not credential:
        return None

    token_hash = hashlib.sha256(credential.encode("utf-8")).hexdigest()

    session = (
        AuthenticationSession.objects
        .select_related("user")
        .filter(
            token_hash=token_hash,
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .first()
    )

    if session is None:
        return None

    user = session.user

    if not user.is_active or user.is_deleted:
        return None

    return session


def login_with_token(
    *, request, email: str, password: str
) -> tuple[User | None, str | None]:
    """Authenticate a user, log the attempt and issue an authentication session."""

    email = normalize_login_email(email)

    user = authenticate_user(
        request=request,
        email=email,
        password=password,
    )

    if user is None or not user.is_active or user.is_deleted:
        existing_user = None
        try:
            existing_user = User.objects.get(email=email)
        except User.DoesNotExist:
            pass

        log_login_attempt(
            user=existing_user,
            request=request,
            successful=False,
        )
        return None, None

    _session, credential = create_authentication_session(user)

    user.last_login_ip = get_client_ip(request)
    user.save(update_fields=["last_login_ip"])

    log_login_attempt(
        user=user,
        request=request,
        successful=True,
    )

    return user, credential
