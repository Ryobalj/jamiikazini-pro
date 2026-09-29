# Generated manually (Kidato V-VI advanced calendar support)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('syllabus', '0017_teacher_download_credits'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='annualcalendar',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='annualcalendar',
            name='level_group',
            field=models.CharField(
                choices=[
                    ('basic', 'Awali - Kidato IV (Msingi/O-Level)'),
                    ('advanced', 'Kidato V - VI (A-Level)'),
                ],
                default='basic',
                help_text=(
                    'Kundi la madarasa yanayotumia kalenda hii: Awali-Kidato IV '
                    '(basic) au Kidato V-VI (advanced).'
                ),
                max_length=20,
                verbose_name='Kundi la Elimu',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='annualcalendar',
            unique_together={('year', 'institute', 'level_group')},
        ),
        migrations.AlterModelOptions(
            name='annualcalendar',
            options={
                'ordering': ['year', 'institute', 'level_group'],
                'verbose_name': 'Kalenda ya Mwaka',
                'verbose_name_plural': 'Kalenda za Mwaka',
            },
        ),
    ]
