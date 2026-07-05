from pathlib import Path

from tools.refactor.models import CheckResult
from tools.refactor.validators.base import BaseValidator


class DjangoValidator(BaseValidator):
    """
    Vérifie que le projet courant est un projet Django.
    """

    def validate(self) -> CheckResult:

        manage = Path("manage.py")

        if not manage.exists():
            return CheckResult(
                name="Django",
                passed=False,
                message="manage.py not found.",
            )

        return CheckResult(
            name="Django",
            passed=True,
            message="Django project detected.",
        )