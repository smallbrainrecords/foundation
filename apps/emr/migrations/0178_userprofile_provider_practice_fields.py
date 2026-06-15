# Generated 2026-06-14 — UserProfile gains provider identity (credentials,
# NPI, signature) and practice info (name/address/phone/fax). Adds
# updated_at (auto_now=True) so the mobile_api signature_url can carry a
# `?v=<timestamp>` cache-bust param without a separate signature-only
# timestamp field.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0177_todo_accomplished_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='credentials',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='npi_number',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='signature_image',
            field=models.ImageField(blank=True, null=True, upload_to='signatures/'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='practice_name',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='practice_street_address',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='practice_city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='practice_state',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='practice_zip',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='practice_phone',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='practice_fax',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
