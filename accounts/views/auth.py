from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsStaffMember
from accounts.serializers import UserSerializer
from accounts.services.authentication import login_with_token
from dental_clinic.api_registry import get_accessible_modules, get_role_label


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password') or ''

        if not email or not password:
            return Response({'detail': 'Email et mot de passe requis.'}, status=400)

        user, token_key = login_with_token(request=request, email=email, password=password)
        if user is None or not token_key:
            return Response({'detail': 'Identifiants invalides ou compte inactif.'}, status=400)

        return Response({
            'token': token_key,
            'user': UserSerializer(user).data,
            'role_label': get_role_label(user.role),
            'accessible_modules': get_accessible_modules(user),
        })


class LogoutView(APIView):
    permission_classes = [IsStaffMember]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({'detail': 'Déconnexion réussie.'})


class CurrentUserView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request):
        user = request.user
        return Response({
            'user': UserSerializer(user).data,
            'role_label': get_role_label(user.role),
            'accessible_modules': get_accessible_modules(user),
        })
