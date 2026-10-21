"""Génère trois échantillons d'ordonnances à partir du VRAI modèle Word.

Usage (conteneur web) :

    docker compose exec -t web python scripts/generate_prescription_render_samples.py

Trois scénarios sont produits, puis convertis en PDF avec LibreOffice sur
l'hôte pour contrôler la pagination réelle :

    A court       : 1 médicament (tient sur une page)
    B long        : 12 médicaments (dépasse la première page)
    C très long   : 45 médicaments (au moins trois pages)

Le script est STRICTEMENT LECTURE SUR LA BASE : aucun Patient, Medication,
Prescription ou DocumentTemplate n'est créé ou modifié. Le fichier modèle
source n'est pas touché (empreinte SHA-256 vérifiée avant/après).
"""

import os
import sys
from datetime import date
from hashlib import sha256

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dental_clinic.settings")
django.setup()

from django.conf import settings  # noqa: E402
from django.utils import timezone  # noqa: E402
from pathlib import Path  # noqa: E402

from accounts.models import User  # noqa: E402
from documents.models import DocumentTemplate  # noqa: E402
from documents.services.docx import render_prescription_docx  # noqa: E402
from patients.models import Medication, Patient  # noqa: E402

OUTPUT_DIR = Path(settings.MEDIA_ROOT) / "_e2e_render"
SCENARIOS = {"a_court": 1, "b_long": 12, "c_tres_long": 45}


def build_medications(patient, dentist, count):
    """Objets Medication non enregistrés, alignés sur le modèle réel."""
    medications = []
    for index in range(1, count + 1):
        medications.append(
            Medication(
                patient=patient,
                prescribed_by=dentist,
                name=f"Médicament {index:02d} — amoxicilline acide clavulanique",
                dosage=f"{250 + 25 * index} mg",
                frequency="2 fois par jour matin et soir",
                route="orale",
                start_date=date(2026, 10, 15),
                end_date=date(2026, 11, 15),
                notes=(
                    "Posologie à ajuster selon la tolérance digestive ; prendre "
                    "pendant le repas avec un grand verre d'eau ; signaler toute "
                    "réaction inhabituelle au praticien traitant. "
                    f"Réf interne RÉF{index:03d}."
                ),
            )
        )
    return medications


def main():
    template = (
        DocumentTemplate.objects.filter(file__isnull=False)
        .order_by("-is_active", "-pk")
        .first()
    )
    if template is None:
        raise SystemExit("Aucun modèle documentaire avec fichier.")

    patient = Patient.objects.filter(is_deleted=False).order_by("pk").first()
    if patient is None:
        raise SystemExit("Aucun patient en base.")

    dentist = User.objects.filter(role=User.Role.DENTIST).order_by("pk").first()
    if dentist is None:
        dentist = User(role=User.Role.DENTIST, first_name="Rendu", last_name="Test")

    with template.file.open("rb") as handle:
        source = handle.read()
    source_sha = sha256(source).hexdigest()

    print(f"modele       : #{template.pk} {template.name}")
    print(f"fichier      : {template.file.name}")
    print(f"sha256 avant : {source_sha}")
    print(f"patient      : #{patient.pk} {patient.first_name} {patient.last_name}")
    print(f"praticien    : #{dentist.pk} {dentist.first_name} {dentist.last_name}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for label, count in SCENARIOS.items():
        medications = build_medications(patient, dentist, count)
        content = render_prescription_docx(
            source,
            patient=patient,
            dentist=dentist,
            generated_at=timezone.now(),
            notes="Échantillon de rendu paginé.",
            medications=medications,
        )
        path = OUTPUT_DIR / f"ordonnance_{label}.docx"
        path.write_bytes(content)
        print(f"{label:12s} : {count:3d} médicaments -> {path} ({len(content)} octets)")

    with template.file.open("rb") as handle:
        source_after = sha256(handle.read()).hexdigest()
    print(f"sha256 après  : {source_after}")
    print(f"modèle source intact : {source_after == source_sha}")


if __name__ == "__main__":
    main()
