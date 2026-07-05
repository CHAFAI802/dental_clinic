from tools.refactor.validators import PythonValidator


class Engine:

    VERSION = "0.2.0"

    def __init__(self):

        self.validators = [
            PythonValidator(),
        ]

    def run(self):

        print("=" * 50)
        print("Dental Engineering Toolkit")
        print(f"Version {self.VERSION}")
        print("=" * 50)

        print()

        for validator in self.validators:

            result = validator.validate()

            status = "OK" if result.passed else "ERROR"

            print(f"[{status}] {result.name}")

            print(f"      {result.message}")

            print()