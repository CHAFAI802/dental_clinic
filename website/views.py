from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdministrator

from .models import SiteImage, SiteSettings, WorkingHours
from .serializers import SiteImageSerializer, SiteSettingsSerializer, WorkingHoursSerializer


class SiteSettingsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        site_settings = SiteSettings.get_solo()
        return Response({"config": site_settings.config})

    def patch(self, request, *args, **kwargs):
        if not IsAdministrator().has_permission(request, self):
            return Response({"detail": "Rôle administrateur requis."}, status=status.HTTP_403_FORBIDDEN)

        site_settings = SiteSettings.get_solo()
        serializer = SiteSettingsSerializer(site_settings, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class SiteImageViewSet(viewsets.ModelViewSet):
    queryset = SiteImage.objects.all().order_by("key")
    serializer_class = SiteImageSerializer

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [AllowAny()]
        return [IsAdministrator()]


class WorkingHoursViewSet(viewsets.ModelViewSet):
    queryset = WorkingHours.objects.select_related("practitioner").all()
    serializer_class = WorkingHoursSerializer
    permission_classes = [IsAdministrator]
