from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from rest_framework import status, viewsets
from rest_framework.response import Response
from faq.models import FAQ
from faq.serializers import FAQSerializer


class FAQViewSet(viewsets.GenericViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer

    # POST /faq
    def create(self, request):
        body = request.data
        question = body.get('question')
        answer = body.get('answer')
        faq = FAQ.objects.create(question=question, answer=answer)
        serializer = self.get_serializer(faq)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # GET /faq
    def list(self, request):
        default_order = '-read_count'

        page = request.GET.get('page', '1')
        order = request.GET.get('order', default_order)
        category = request.GET.get('category')

        faqs = self.get_queryset().order_by(order)
        if category is not None:
            faqs = faqs.filter(category=category)
        faqs = Paginator(faqs, 5).get_page(page)
        serializer = self.get_serializer(faqs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # DELETE /faq/:faqId
    def delete(self, request, pk=None):
        faq = get_object_or_404(FAQ, pk=pk)
        faq.delete()
        return Response(status=status.HTTP_200_OK)

    # GET /faq/:faqId
    def retrieve(self, request, pk=None):
        faq = get_object_or_404(FAQ, pk=pk)
        faq.read_count += 1
        faq.save()
        serializer = self.get_serializer(faq)
        return Response(serializer.data, status=status.HTTP_200_OK)