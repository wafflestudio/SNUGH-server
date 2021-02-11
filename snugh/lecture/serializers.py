from rest_framework import serializers 
from lecture.models import Plan 

class PlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = Plan 
        fields = (
            'id',
            'user_id',
            'plan_name',
            'recent_scroll'
        )

