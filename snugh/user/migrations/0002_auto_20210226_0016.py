# Generated by Django 3.1.6 on 2021-02-26 00:16

from django.db import migrations


def add_cities(apps, schema_editor):
    Major = apps.get_model("user", "Major")    

    cities=["종로구", "중구", "용산구", "성동구", "광진구", "동대문구", "중랑구", "성북구","강북구", "도봉구", "노원구", "은평구", "서대문구", "마포구", "양천구", 
    "강서구", "구로구", "금천구", "영등포구", "동작구", "관악구", "서초구", "강남구", "송파구", "강동구"]

    for i in range(0, 25):
        row=Major.objects.create(major_name=cities[i], major_type=1)


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_cities)
    ]
