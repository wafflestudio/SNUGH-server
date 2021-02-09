from django.shortcuts import render
from rest_framework import status, viewsets
from django.contrib.auth.models import User

class UserViewSet(viewsets.GenericViewSet):
    queryset=User.objects.all()
#    serializer_class=
    permisison_classes=(IsAuthenticated(), )


