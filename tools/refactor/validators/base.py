from abc import ABC, abstractmethod

from tools.refactor.validators.models import CheckResult


class BaseValidator(ABC):
    """
    Classe mère de tous les validateurs.
    """

    @abstractmethod
    def validate(self) -> CheckResult:
        raise NotImplementedError