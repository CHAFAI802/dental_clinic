from decimal import Decimal

from billing.models import InvoiceLine
from prescriptions.models import Prescription
from treatments.models import Treatment

# Identifiant métier de la prestation « Acte de prescrire ».
PRESC_CODE = "PRESC"

# La prescription est facturée avec une quantité fixe de 1.
PRESC_QUANTITY = Decimal("1")


def prescription_is_billable(*, appointment):
    """
    Règle de facturation de la prescription :

    l'acte PRESC n'est facturable que si aucune prestation dentaire
    n'a été réalisée pendant le même rendez-vous et qu'une ordonnance a
    bien été générée pendant ce rendez-vous.
    """
    has_prescription = Prescription.objects.filter(
        appointment=appointment,
    ).exists()

    if not has_prescription:
        return False

    has_dental_treatment = (
        Treatment.objects
        .filter(appointment=appointment)
        .exclude(prestation__code=PRESC_CODE)
        .exists()
    )

    return not has_dental_treatment


def apply_prescription_billing(*, appointment):
    """
    Applique la facturation de l'acte PRESC à la clôture du rendez-vous.

    - aucune ordonnance pendant la séance          → aucune ligne ;
    - au moins une prestation dentaire enregistrée → aucune ligne PRESC ;
    - ordonnance seule                             → une ligne PRESC de
      quantité 1, créée une seule fois (idempotent).

    Aucune ligne existante (y compris payée ou créditée) n'est supprimée
    ni modifiée : seules les nouvelles séances sont concernées.

    Retourne True si une ligne de facture a été créée.
    """
    presc_treatments = (
        Treatment.objects
        .filter(
            appointment=appointment,
            prestation__code=PRESC_CODE,
        )
        .select_related("prestation")
    )

    if not presc_treatments.exists():
        return False

    if not prescription_is_billable(appointment=appointment):
        return False

    # Un seul traitement PRESC est facturé par rendez-vous, même si
    # plusieurs requêtes ont créé des traitements équivalents.
    if InvoiceLine.objects.filter(treatment__in=presc_treatments).exists():
        return False

    treatment = presc_treatments.first()

    # InvoiceLine.save() calcule le tarif et la TVA à partir de la
    # prestation, puis recalcule la facture : aucun montant n'est
    # calculé ici.
    InvoiceLine.objects.create(
        treatment=treatment,
        prestation=treatment.prestation,
        description=treatment.prestation.label,
        quantity=PRESC_QUANTITY,
    )

    return True
