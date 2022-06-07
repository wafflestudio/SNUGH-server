from rest_framework import serializers
from core.major.models import Major


class MajorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Major
        fields = (
            "id",
            "major_name",
            "major_type",
        )
