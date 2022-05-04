from rest_framework import serializers 
from faq.models import FAQ
from snugh.exceptions import FieldError


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'
        extra_kwargs = {
            "question": {"required": True}
        }


    def validate(self, data):
        question = data['question']
        if len(question) < 5:
            raise FieldError("Invalid field [question]")
        return data
    

    def create(self, validated_data):
        return FAQ.objects.create(
            question=self.validated_data['question'], 
            answer=self.validated_data.get('answer', ""), 
            category=self.validated_data.get('category'))

