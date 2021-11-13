from django.urls import include, path
from rest_framework.routers import SimpleRouter
from django.contrib.auth import views as auth_views
from user.views import UserViewSet, MajorViewSet


app_name = 'user'

router = SimpleRouter()
router.register('user', UserViewSet, basename='user')  
router.register('major', MajorViewSet, basename='major')  

urlpatterns = [
    path('', include((router.urls))),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
