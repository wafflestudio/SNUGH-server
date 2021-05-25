# Generated by Django 3.1 on 2021-05-25 08:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0005_auto_20210319_1716'),
    ]

    operations = [
        migrations.AlterField(
            model_name='major',
            name='major_type',
            field=models.CharField(choices=[('major', 'major'), ('double_major', 'double_major'), ('minor', 'minor'), ('interdisciplinary_major', 'interdisciplinary_major'), ('interdisciplinary', 'interdisciplinary'), ('single_major', 'single_major'), ('interdisciplinary_major_for_teacher_training_programs', 'interdisciplinary_major_for_teacher_training_programs'), ('student_directed_major', 'student_directed_major')], max_length=100),
        ),
    ]
