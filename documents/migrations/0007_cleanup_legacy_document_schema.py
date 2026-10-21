from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0006_documenttemplate_approved_file_sha256"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE IF EXISTS documents_document
                    DROP COLUMN IF EXISTS template_version_id;

                DROP TABLE IF EXISTS documents_documenttemplateversion;
                DROP TABLE IF EXISTS documents_documenttype;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]