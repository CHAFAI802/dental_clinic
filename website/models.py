from django.db import models

from accounts.models import User


class WorkingHours(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    practitioner = models.ForeignKey(
        "accounts.User",
        related_name="working_hours",
        on_delete=models.CASCADE,
        limit_choices_to={"role": User.Role.DENTIST},
    )
    weekday = models.PositiveSmallIntegerField(
        choices=Weekday.choices,
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["practitioner", "weekday", "start_time"]
        indexes = [
            models.Index(
                fields=["practitioner", "weekday", "is_active"],
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    end_time__gt=models.F("start_time"),
                ),
                name="working_hours_end_after_start",
            ),
            models.UniqueConstraint(
                fields=[
                    "practitioner",
                    "weekday",
                    "start_time",
                    "end_time",
                ],
                name="unique_practitioner_working_hours",
            ),
        ]

    def __str__(self):
        return (
            f"{self.practitioner} - "
            f"{self.get_weekday_display()} "
            f"{self.start_time}-{self.end_time}"
        )