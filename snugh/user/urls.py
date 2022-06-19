from django.urls import include, path
from rest_framework.routers import SimpleRouter
from user.views import UserSignUpView, UserLoginView, UserLogoutView, UserViewSet


app_name = 'user'

router = SimpleRouter()
router.register('user', UserViewSet, basename='user')  

urlpatterns = [
    path('user/', UserSignUpView.as_view(), name='signup'),
    path('user/login/', UserLoginView.as_view(), name='login'),
    path('user/logout/', UserLogoutView.as_view(), name='logout'),
    path('', include((router.urls))),
]
