"""Fax set members (2026-11-25; `FaxSetMember`): one directory entry in a
fax set.

One operation, on purpose (MySQL DDL is not transactional): one table, after
the set table of 0218. On production run it by the migrate job BEFORE the
revision that uses it serves.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0218_faxset'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FaxSetMember',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_on', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('fax_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='emr.faxset')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='set_memberships', to='emr.faxrecipient')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('fax_set', 'recipient'), name='uniq_fax_set_member')],
            },
        ),
    ]
