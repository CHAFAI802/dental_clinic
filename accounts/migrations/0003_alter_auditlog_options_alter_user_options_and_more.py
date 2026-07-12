from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auditlog_and_loginhistory_indexes'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='auditlog',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ['last_name', 'first_name', 'email']},
        ),
        migrations.AlterModelOptions(
            name='userloginhistory',
            options={'ordering': ['-login_at']},
        ),
    ]
