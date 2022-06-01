from django.contrib import admin
from user.models import User, UserProfile
from django.contrib.auth.admin import UserAdmin

admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)
