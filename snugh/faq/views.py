from rest_framework import status, viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from faq.models import FAQ
from faq.serializers import FAQSerializer


class FAQViewSet(viewsets.GenericViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer

    def list(self, request):
        page = request.GET.get('page', '1')
        faqs = self.get_queryset().order_by('created_at')
        faqs = Paginator(faqs, 5).get_page(page)
        serializer = self.get_serializer(faqs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        body = request.data
        question = body.get('question')
        answer = body.get('answer')
        faq = FAQ.objects.create(question=question, answer=answer)
        serializer = self.get_serializer(faq)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk=None):
        faq = get_object_or_404(FAQ, pk=pk)
        faq.delete()
        return Response(status=status.HTTP_200_OK)