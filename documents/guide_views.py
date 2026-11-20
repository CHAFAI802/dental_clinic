from pathlib import Path

from django.http import FileResponse, Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdministrator
from documents.admin_guide_content import ADMIN_GUIDE_CONTENT


GUIDE_DOCUMENTS = {
    "pdf": (
        "guide-utilisateur-dental-clinic.pdf",
        "application/pdf",
        False,
    ),
    "docx": (
        "guide-utilisateur-dental-clinic.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        True,
    ),
}


class UserGuideDocumentView(APIView):
    """Serve the user guide only to authenticated application users."""

    permission_classes = [IsAuthenticated]

    def get(self, request, document_format):
        document = GUIDE_DOCUMENTS.get(document_format.lower())
        if document is None:
            raise Http404("Document de guide introuvable.")

        filename, content_type, as_attachment = document
        file_path = Path(__file__).resolve().parent / "user_guide" / filename
        if not file_path.is_file():
            raise Http404("Le fichier du guide est indisponible.")

        response = FileResponse(
            file_path.open("rb"),
            as_attachment=as_attachment,
            filename=filename,
            content_type=content_type,
        )
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response


class AdminGuideContentView(APIView):
    """Serve administrator documentation to administrator roles only."""

    permission_classes = [IsAuthenticated, IsAdministrator]

    def get(self, request):
        response = Response(ADMIN_GUIDE_CONTENT)
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
