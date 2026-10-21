"""Instance isolée pour la validation E2E du parcours médecin (Phase 5).

Ce module n'est PAS utilisé par l'application : il ne sert qu'à lancer une
seconde instance Django (base et fichiers séparés) afin de vérifier le
parcours complet dans un navigateur sans jamais toucher à la base réelle ni
au volume média de production (règle du cahier des charges : aucune donnée
métier réelle modifiée, aucun modèle documentaire réel approuvé).

Usage :
    DATABASE_URL=postgres://dental:dental@db:5432/dental_ui_e2e \\
    DJANGO_SETTINGS_MODULE=dental_clinic.settings_ui_e2e \\
    python manage.py runserver 0.0.0.0:8000

DATABASE_URL reste piloté par l'environnement (cf. settings.py) ; seuls les
fichiers média sont redirigés vers un répertoire éphémère du conteneur.
"""

from pathlib import Path

from .settings import *  # noqa: F401,F403  (configuration de base du projet)

import os  # noqa: E402

MEDIA_ROOT = Path(
    os.environ.get("MEDIA_ROOT_E2E", "/tmp/media_ui_e2e")
)
