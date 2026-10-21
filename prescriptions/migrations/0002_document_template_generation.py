import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0005_documenttemplate_approval"),
        ("prescriptions", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="prescription",
            name="template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="prescriptions",
                to="prescriptions.prescriptiontemplate",
            ),
        ),
        migrations.AddField(
            model_name="prescription",
            name="document_template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="prescriptions",
                to="documents.documenttemplate",
            ),
        ),
        migrations.AddField(
            model_name="prescription",
            name="generated_file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="prescriptions/generated/",
            ),
        ),
    ]
