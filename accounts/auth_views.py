from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from dental_clinic.api_registry import get_accessible_modules, get_role_label
from .models import User, UserLoginHistory
from .serializers import UserSerializer


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _log_login(user, request, successful):
    UserLoginHistory.objects.create(
        user=user if successful else None,
        login_at=timezone.now(),
        source_ip=_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
        successful=successful,
    )


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password') or ''

        if not email or not password:
            return Response({'detail': 'Email et mot de passe requis.'}, status=400)

        user = authenticate(request, username=email, password=password)

        if user is None or not user.is_active or user.is_deleted:
            failed_user = None
            try:
                failed_user = User.objects.get(email=email)
            except User.DoesNotExist:
                pass
            _log_login(failed_user, request, successful=False)
            return Response({'detail': 'Identifiants invalides ou compte inactif.'}, status=400)

        token, _created = Token.objects.get_or_create(user=user)
        user.last_login_ip = _client_ip(request)
        user.save(update_fields=['last_login_ip'])
        _log_login(user, request, successful=True)

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'role_label': get_role_label(user.role),
            'accessible_modules': get_accessible_modules(user),
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({'detail': 'Déconnexion réussie.'})


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'user': UserSerializer(user).data,
            'role_label': get_role_label(user.role),
            'accessible_modules': get_accessible_modules(user),
        })
