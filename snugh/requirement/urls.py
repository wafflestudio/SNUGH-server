from django.urls import include, path
from rest_framework.routers import SimpleRouter
from requirement.views import RequirementViewSet


app_name = 'requirement'

router = SimpleRouter()
router.register('requirement', RequirementViewSet, basename='requirement')

urlpatterns = [
    path('', include((router.urls))),
]
