from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):

    def delete(self):
        return self.update(
            is_deleted=True,
            deleted_at=timezone.now()
        )

    def restore(self):
        return self.update(
            is_deleted=False,
            deleted_at=None
        )

class ProtectedDeleteQuerySet(models.QuerySet):

    def delete(self):
        raise ValidationError(
            "Deletion is not allowed for this model."
        )

class SoftDeleteManager(models.Manager):

    def get_queryset(self):
        return SoftDeleteQuerySet(
            self.model,
            using=self._db
        ).filter(
            is_deleted=False
        )

class ProtectedDeleteManager(models.Manager):

    def get_queryset(self):
        return ProtectedDeleteQuerySet(
            self.model,
            using=self._db,
        )


class SoftDeleteModel(TimestampedModel):

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(
            update_fields=[
                "is_deleted",
                "deleted_at",
            ]
        )

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(
            update_fields=[
                "is_deleted",
                "deleted_at",
            ]
        )

    class Meta:
        abstract = True
