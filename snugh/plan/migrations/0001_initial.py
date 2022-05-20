# Generated by Django 3.2.4 on 2022-05-02 06:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('user', '0007_departmentequivalent_majorequivalent'),
    ]

    operations = [
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan_name', models.CharField(db_index=True, default='새로운 계획', max_length=50)),
                ('is_first_simulation', models.BooleanField(default=True)),
                ('user', models.ForeignKey(default=5, on_delete=django.db.models.deletion.CASCADE, related_name='plan', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PlanMajor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('major', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='planmajor', to='user.major')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='planmajor', to='plan.plan')),
            ],
        ),
        migrations.AddConstraint(
            model_name='planmajor',
            constraint=models.UniqueConstraint(fields=('plan', 'major'), name='major already exists in plan.'),
        ),
    ]
