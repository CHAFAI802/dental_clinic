import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Rattache une ordonnance au rendez-vous pendant lequel elle a été
    générée.

    Champ nullable : les ordonnances historiques (créées avant ce lien)
    sont conservées telles quelles. Le flux de génération impose
    néanmoins un rendez-vous valide (cf. prescriptions.views).
    """

    dependencies = [
        ("appointments", "0002_initial"),
        ("prescriptions", "0003_cleanup_legacy_prescription_columns"),
    ]

    operations = [
        migrations.AddField(
            model_name="prescription",
            name="appointment",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="prescriptions",
                to="appointments.appointment",
            ),
        ),
    ]
