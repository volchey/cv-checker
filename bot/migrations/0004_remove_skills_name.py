# Generated by Django 3.1.12 on 2021-12-06 06:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0003_skills'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='skills',
            name='name',
        ),
    ]
