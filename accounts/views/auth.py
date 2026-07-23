from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsStaffMember
from accounts.serializers import LoginSerializer, UserSerializer
from accounts.services.authentication import login_with_token
from dental_clinic.api_registry import (
    get_accessible_modules,
    get_role_label,
)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user, token_key = login_with_token(
            request=request,
            email=email,
            password=password,
        )

        if user is None or not token_key:
            return Response(
                {"detail": "Identifiants invalides ou compte inactif."},
                status=400,
            )

        return Response(
            {
                "token": token_key,
                "user": UserSerializer(user).data,
                "role_label": get_role_label(user.role),
                "accessible_modules": get_accessible_modules(user),
            }
        )


class LogoutView(APIView):
    permission_classes = [IsStaffMember]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({"detail": "Déconnexion réussie."})


class CurrentUserView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request):
        user = request.user
        return Response(
            {
                "user": UserSerializer(user).data,
                "role_label": get_role_label(user.role),
                "accessible_modules": get_accessible_modules(user),
            }
        )