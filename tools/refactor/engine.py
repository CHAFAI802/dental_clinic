from tools.refactor.validators import (
    DjangoValidator,
    DockerValidator,
    GitValidator,
    PythonValidator,
)


class Engine:

    VERSION = "0.2.0"

    def __init__(self):

        self.validators = [
            PythonValidator(),
            GitValidator(),
            DockerValidator(),
            DjangoValidator(),
        ]

    def run(self):

        print("=" * 50)
        print("Dental Engineering Toolkit")
        print(f"Version {self.VERSION}")
        print("=" * 50)
        print()

        overall = True

        for validator in self.validators:

            result = validator.validate()

            status = "OK" if result.passed else "ERROR"

            if not result.passed:
                overall = False

            print(f"[{status}] {result.name}")
            print(f"      {result.message}")
            print()

        print("=" * 50)

        if overall:
            print("Environment Status : READY")
        else:
            print("Environment Status : NOT READY")

        print("=" * 50)