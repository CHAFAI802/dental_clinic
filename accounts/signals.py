from django.dispatch import receiver

from axes.signals import user_locked_out
from rest_framework.exceptions import Throttled


@receiver(user_locked_out)
def handle_user_locked_out(sender, request, **kwargs):
    raise Throttled(
        detail="Too many failed login attempts. Please try again later."
    )
