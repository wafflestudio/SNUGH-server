# Generated by Django 3.2.4 on 2022-05-02 07:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lecture', '0036_auto_20220502_0644'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='semesterlecture',
            name='lecture already exists in semester.',
        ),
    ]