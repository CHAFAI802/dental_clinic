from django.db import models
from django.utils import timezone


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


class SoftDeleteManager(models.Manager):

    def get_queryset(self):
        return SoftDeleteQuerySet(
            self.model,
            using=self._db
        ).filter(
            is_deleted=False
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
