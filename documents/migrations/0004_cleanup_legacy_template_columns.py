from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0003_remove_documenttemplate_content_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE documents_documenttemplate
                    DROP COLUMN IF EXISTS code,
                    DROP COLUMN IF EXISTS created_by_id,
                    DROP COLUMN IF EXISTS document_type_id;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
