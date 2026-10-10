from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateDocumentStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(
            location=None,
            base_url=None,
            file_permissions_mode=0o600,
            directory_permissions_mode=0o700,
        )

    @property
    def location(self):
        return str(settings.PRIVATE_DOCUMENT_ROOT)

    @property
    def base_url(self):
        return None

    def url(self, name):
        raise ValueError('Private documents do not have public URLs.')


private_document_storage = PrivateDocumentStorage()