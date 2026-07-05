import shutil
import subprocess

from tools.refactor.models import CheckResult
from tools.refactor.validators.base import BaseValidator


class DockerValidator(BaseValidator):
    """
    Vérifie que Docker et Docker Compose sont disponibles.
    """

    def validate(self) -> CheckResult:

        if shutil.which("docker") is None:
            return CheckResult(
                name="Docker",
                passed=False,
                message="Docker executable not found.",
            )

        try:
            subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True,
                text=True,
                check=True,
            )

            return CheckResult(
                name="Docker",
                passed=True,
                message="Docker Compose detected.",
            )

        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
        ) as exc:

            return CheckResult(
                name="Docker",
                passed=False,
                message=str(exc),
            )