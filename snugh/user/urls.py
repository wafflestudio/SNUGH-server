from django.urls import include, path
from rest_framework.routers import SimpleRouter
from user.views import *


app_name = 'user'

router = SimpleRouter()
router.register('user', UserViewSet, basename='user')  
router.register('major', MajorViewSet, basename='major')  

urlpatterns = [
    path('signup/', UserSignUpView.as_view(), name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('', include((router.urls))),
]
