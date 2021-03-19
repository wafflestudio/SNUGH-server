# Generated by Django 3.1 on 2021-03-19 15:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_auto_20210319_1111'),
    ]

    operations = [
        migrations.AlterField(
            model_name='major',
            name='major_type',
            field=models.PositiveSmallIntegerField(choices=[('major', 'major'), ('double_major', 'double_major'), ('minor', 'minor'), ('interdisciplinary_major', 'interdisciplinary_major'), ('interdisciplinary', 'interdisciplinary'), ('single_major', 'single_major'), ('interdisciplinary_major_for_teacher_training_programs', 'interdisciplinary_major_for_teacher_training_programs'), ('student_directed_major', 'student_directed_major')]),
        ),
    ]
