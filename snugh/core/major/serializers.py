from rest_framework import serializers
from core.major.models import Major


class MajorSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    major_name = serializers.CharField()
    major_type = serializers.CharField()

    class Meta:
        model = Major
        fields = (
            "id",
            "major_name",
            "major_type",
        )