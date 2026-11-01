import time

from django.core.management.base import BaseCommand
from django.db import connections
from django.utils import timezone

from appointments.services.appointment_closure import (
    close_expired_appointments,
)


class Command(BaseCommand):
    help = (
        "Clôture les rendez-vous confirmés dont l'heure de fin est "
        "passée, applique la facturation de la prescription et journalise "
        "la transition. Commande idempotente : peut être exécutée "
        "plusieurs fois sans effet de bord."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=None,
            metavar="SECONDES",
            help=(
                "Exécute la clôture en boucle toutes les N secondes "
                "(processus long, adapté au service scheduler Docker). "
                "Sans cette option, la commande s'exécute une seule fois."
            ),
        )

    def handle(self, *args, **options):
        interval = options["interval"]

        if interval is None:
            closed_ids = self._run_once()
            self.stdout.write(
                f"{len(closed_ids)} rendez-vous clôturé(s)."
            )
            return

        if interval < 1:
            raise SystemExit("--interval doit être supérieur ou égal à 1.")

        self.stdout.write(
            f"Clôture automatique des rendez-vous toutes les "
            f"{interval} seconde(s)."
        )

        while True:
            try:
                closed_ids = self._run_once()
                if closed_ids:
                    self.stdout.write(
                        f"{timezone.now().isoformat()} : "
                        f"{len(closed_ids)} rendez-vous clôturé(s) "
                        f"(ids {closed_ids})."
                    )
            except Exception as error:  # noqa: BLE001 - le service ne
                # doit jamais s'arrêter : une erreur est journalisée et
                # la boucle reprend au tour suivant (reprise après
                # redémarrage ou incident de base de données).
                self.stderr.write(
                    f"{timezone.now().isoformat()} : échec de la "
                    f"clôture automatique - {error}"
                )
            finally:
                # Évite une connexion PostgreSQL fermée entre deux tours.
                connections.close_all()

            time.sleep(interval)

    def _run_once(self):
        return close_expired_appointments()
