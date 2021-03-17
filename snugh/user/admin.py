from django.contrib import admin
from django.contrib.auth.models import User
from user.models import UserProfile, Major, UserMajor

admin.site.register(User)
admin.site.register(UserProfile)
admin.site.register(Major)
admin.site.register(UserMajor)
