from django.urls import include, path
from rest_framework.routers import SimpleRouter
from user.views import UserSignUpView, UserLoginView, UserViewSet


app_name = 'user'

router = SimpleRouter()
router.register('user', UserViewSet, basename='user')  

urlpatterns = [
    path('signup/', UserSignUpView.as_view(), name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('', include((router.urls))),
]
