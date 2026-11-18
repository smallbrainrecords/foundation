# Office documents (2026-11-18). One operation per migration: concurrent
# boots race `migrate` on MySQL, and a single operation leaves no partial
# state to strand (see SBR1 CLAUDE.md, "Migrations run automatically").

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0203_documentedit'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OfficeDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('moved_at', models.DateTimeField()),
                ('source', models.CharField(default='pool', max_length=16)),
                ('note', models.TextField(blank=True, default='')),
                ('document', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='office', to='emr.document')),
                ('moved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
