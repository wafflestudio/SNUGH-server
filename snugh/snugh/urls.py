from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('user.urls')),
    path('', include('lecture.urls')),
    path('', include('requirement.urls')),
    path('', include('faq.urls')),
]
