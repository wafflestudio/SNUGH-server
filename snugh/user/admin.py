from django.contrib import admin
from user.models import UserProfile, Major, UserMajor


admin.site.register(UserProfile)
admin.site.register(Major)
admin.site.register(UserMajor)
