# Generated by Django 3.2.4 on 2022-04-24 14:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lecture', '0031_auto_20220424_1424'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='semester',
            unique_together={('semester_type', 'year', 'plan')},
        ),
    ]