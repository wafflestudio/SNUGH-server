from django.urls import include, path
from rest_framework.routers import SimpleRouter
from plan.views import PlanViewSet 

app_name = 'plan'

router = SimpleRouter() 
router.register('plan', PlanViewSet, basename='plan')

urlpatterns = [
    path('', include((router.urls))),
]
