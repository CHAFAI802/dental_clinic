from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0005_documenttemplate_approval"),
    ]

    operations = [
        migrations.AddField(
            model_name="documenttemplate",
            name="approved_file_sha256",
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
