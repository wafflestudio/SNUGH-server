from django.core.paginator import Paginator
from rest_framework import status, viewsets, generics
from rest_framework.response import Response
from faq.models import FAQ
from faq.serializers import FAQSerializer
from snugh.permissions import IsOwnerOrCreateReadOnly
# TODO: FAQ 작동 방식? 공지 사항 형식 or 질문 & 답글 형식?

class FAQViewSet(
    viewsets.GenericViewSet,
    generics.CreateAPIView,
    generics.RetrieveUpdateDestroyAPIView
):
    """
    Generic ViewSet of FAQ Object.
    """
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [IsOwnerOrCreateReadOnly]

    # GET /faq
    def list(self, request):
        """Get list of all FAQs."""
        default_order = '-read_count'
        page = request.GET.get('page', '1')
        order = request.GET.get('order', default_order)
        category = request.GET.get('category')

        faqs = self.get_queryset().order_by(order)
        if category:
            faqs = faqs.filter(category=category)
            
        faqs = Paginator(faqs, 5).get_page(page)
        serializer = self.get_serializer(faqs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # GET /faq/:faqId
    def retrieve(self, request, pk=None):
        """Get certain faq."""
        faq = self.get_object()
        faq.read_count += 1
        faq.save()
        serializer = self.get_serializer(faq)
        return Response(serializer.data, status=status.HTTP_200_OK)
