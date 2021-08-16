from django.urls import include, path 
from rest_framework.routers import SimpleRouter
from faq.views import FAQViewSet

app_name = 'faq'

router = SimpleRouter() 
router.register('faq', FAQViewSet, basename='faq')

urlpatterns = [
    path('', include((router.urls))),
]