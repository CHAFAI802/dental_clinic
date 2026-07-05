import sys

from tools.refactor.models import CheckResult
from tools.refactor.validators.base import BaseValidator


class PythonValidator(BaseValidator):

    def validate(self) -> CheckResult:

        version = ".".join(map(str, sys.version_info[:3]))

        return CheckResult(
            name="Python",
            passed=True,
            message=f"Python {version}",
        )