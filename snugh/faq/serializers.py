from rest_framework import serializers 
from faq.models import FAQ
from snugh.exceptions import FieldError


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'
        extra_kwargs = {
            "question": {"question": True}
        }


    def validate(self, data):
        question = data['question']
        if len(question) < 5:
            raise FieldError("Invalid field [question]")
    

    def create(self, validated_data):
        return FAQ.objects.create(
            user=self.context['request'].user, 
            question=self.validated_data['question'], 
            answer=self.validated_data['answer'], 
            category=self.validated_data.get('category'))

