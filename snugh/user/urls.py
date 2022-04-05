from django.urls import include, path
from rest_framework.routers import SimpleRouter
from user.views import UserSignUpView, UserViewSet, MajorViewSet


app_name = 'user'

router = SimpleRouter()
router.register('user', UserViewSet, basename='user')  
router.register('major', MajorViewSet, basename='major')  

urlpatterns = [
    path('signup/', UserSignUpView.as_view(), name='signup'),
    path('', include((router.urls))),
]
