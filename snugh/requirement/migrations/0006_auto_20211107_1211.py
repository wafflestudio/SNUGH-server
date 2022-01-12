# Generated by Django 3.1 on 2021-11-07 12:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('requirement', '0005_auto_20210902_1426'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='planrequirement',
            name='is_fulfilled',
        ),
        migrations.CreateModel(
            name='RequirementChangeHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entrance_year', models.IntegerField(default=0)),
                ('past_required_credit', models.PositiveIntegerField(default=0)),
                ('curr_required_credit', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateField(auto_now_add=True)),
                ('change_count', models.IntegerField(default=1)),
                ('requirement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requirementchangehistory', to='requirement.requirement')),
            ],
        ),
    ]