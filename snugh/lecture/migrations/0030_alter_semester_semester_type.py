# Generated by Django 3.2.4 on 2022-04-24 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lecture', '0029_auto_20220424_1415'),
    ]

    operations = [
        migrations.AlterField(
            model_name='semester',
            name='semester_type',
            field=models.CharField(max_length=50),
        ),
    ]