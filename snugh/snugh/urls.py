from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from user.views import UserViewSet
import os


urlpatterns = [
    path('', include('user.urls')),
    path('', include('core.urls')),
    path('', include('faq.urls')),
    path('', include('bug_report.urls')),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('accounts/login/', UserViewSet.login_redirect, name='login_redirect'),
]

if os.environ.get('DJANGO_SETTINGS_MODULE')=='snugh.settings.local':
    import debug_toolbar
    urlpatterns += [path("__debug__/", include(debug_toolbar.urls)), path('admin/', admin.site.urls),]
