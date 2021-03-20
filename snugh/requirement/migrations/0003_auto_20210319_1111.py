# Generated by Django 3.1 on 2021-03-19 11:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('requirement', '0002_auto_20210307_0956'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requirement',
            name='requirement_type',
            field=models.CharField(choices=[('none', 'none'), ('major_requirement', 'major_requirement'), ('major_elective', 'major_elective'), ('general', 'general'), ('general_elective', 'general_elective'), ('teaching', 'teaching'), ('all', 'all')], max_length=50),
        ),
        migrations.AlterField(
            model_name='requirement',
            name='requirement_type_detail',
            field=models.CharField(choices=[('none', 'none'), ('base_of_study', 'base_of_study'), ('world_of_study', 'world_of_study'), ('other', 'other')], default='none', max_length=50),
        ),
        migrations.AlterField(
            model_name='requirement',
            name='requirement_type_detail_detail',
            field=models.CharField(choices=[('none', 'none'), ('thought_and_expression', 'thought_and_expression'), ('foreign_languages', 'foreign_languages'), ('mathematical_analysis_and_reasoning', 'mathematical_analysis_and_reasoning'), ('scientific_thinking_and_experiment', 'scientific_thinking_and_experiment'), ('computer_and_informatics', 'computer_and_informatics'), ('language_and_literature', 'language_and_literature'), ('culture_and_arts', 'culture_and_arts'), ('history_and_philosophy', 'history_and_philosophy'), ('politics_and_economics', 'politics_and_economics'), ('humanity_and_society', 'humanity_and_society'), ('nature_and_technology', 'nature_and_technology'), ('life_and_environment', 'life_and_environment')], default='none', max_length=50),
        ),
    ]
