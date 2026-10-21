from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("prescriptions", "0002_document_template_generation"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE IF EXISTS prescriptions_prescription
                    DROP COLUMN IF EXISTS generated_docx;

                ALTER TABLE IF EXISTS prescriptions_prescriptiontemplate
                    DROP COLUMN IF EXISTS docx_file;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]