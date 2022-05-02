from django.urls import include, path
from rest_framework.routers import SimpleRouter
from semester.views import SemesterViewSet 

app_name = 'semester'

router = SimpleRouter() 
router.register('semester', SemesterViewSet, basename='semester')
urlpatterns = [
    path('', include((router.urls))),
]
