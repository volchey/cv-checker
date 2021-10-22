# Generated by Django 3.1.12 on 2021-10-22 17:47

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Vacancy',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('status', models.IntegerField(choices=[(1, 'Open'), (2, 'Closed')], default=1, max_length=2)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name_plural': 'vacancies',
            },
        ),
    ]
