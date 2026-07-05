from dataclasses import dataclass


@dataclass(slots=True)
class CheckResult:
    """
    Représente le résultat d'une vérification.
    """

    name: str
    passed: bool
    message: str