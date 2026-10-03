from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from accounts.services.authentication import get_authentication_session


class AuthenticationSessionAuthentication(BaseAuthentication):
    """
    Authenticate API requests using AuthenticationSession credentials.
    """

    keyword = "Token"

    def authenticate(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth:
            return None

        try:
            keyword, credential = auth.split(None, 1)
        except ValueError:
            raise AuthenticationFailed(
                "Identifiants d'authentification invalides."
            )

        if keyword.lower() != self.keyword.lower():
            return None

        session = get_authentication_session(credential)

        if session is None:
            raise AuthenticationFailed(
                "Identifiants d'authentification invalides."
            )

        return session.user, session

    def authenticate_header(self, request):
        return self.keyword
