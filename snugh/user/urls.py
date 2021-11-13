from django.urls import include, path
from rest_framework.routers import SimpleRouter
from user.views import UserViewSet, MajorViewSet


app_name = 'user'

router = SimpleRouter()
router.register('user', UserViewSet, basename='user')  
router.register('major', MajorViewSet, basename='major')  

urlpatterns = [
    path('', include((router.urls))),
]
