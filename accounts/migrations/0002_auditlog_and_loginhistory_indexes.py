from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['created_at'], name='acc_audit_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user', 'created_at'], name='acc_audit_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['model_name', 'object_id'], name='acc_audit_model_object_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['action', 'created_at'], name='acc_audit_action_created_idx'),
        ),
        migrations.AddIndex(
            model_name='userloginhistory',
            index=models.Index(fields=['user', 'login_at'], name='acc_login_user_login_idx'),
        ),
        migrations.AddIndex(
            model_name='userloginhistory',
            index=models.Index(fields=['login_at'], name='acc_login_login_at_idx'),
        ),
    ]
