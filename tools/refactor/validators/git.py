from pathlib import Path
import subprocess

from tools.refactor.models import CheckResult
from tools.refactor.validators.base import BaseValidator


class GitValidator(BaseValidator):
    """
    Vérifie que le projet est un dépôt Git valide.
    """

    def validate(self) -> CheckResult:

        if not Path(".git").exists():
            return CheckResult(
                name="Git",
                passed=False,
                message="No Git repository found.",
            )

        try:
            branch = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            return CheckResult(
                name="Git",
                passed=True,
                message=f"Repository detected (branch: {branch})",
            )

        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
        ) as exc:

            return CheckResult(
                name="Git",
                passed=False,
                message=str(exc),
            )