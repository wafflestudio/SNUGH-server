from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from user.models import User, UserProfile, Major, UserMajor

admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)
admin.site.register(Major)
admin.site.register(UserMajor)
