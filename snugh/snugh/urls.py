from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from user.views import UserViewSet


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('user.urls')),
    path('', include('lecture.urls')),
    path('', include('requirement.urls')),
    path('', include('faq.urls')),
    path('', include('bug_report.urls')),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('accounts/login/', UserViewSet.login_redirect, name='login_redirect'),
]
