from django.shortcuts import render
from rest_framework import status, viewsets
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from user.models import *
from user.serializers import *
from rest_framework.response import Response
from rest_framework.decorators import action

class UserViewSet(viewsets.GenericViewSet):
    queryset=User.objects.all()
    serializer_class=UserSerializer
#    permisison_classes=()
#    def get_permissions(self):
#        if self.action in ('create', 'login', 'update'):
#            return (AllowAny(), )
#        return self.permission_classes
    
    def create(self, request):
        body=request.data
        username=body.get('username')
        password=body.get('password')
        student_id=body.get('student_id')
        first_name=body.get('first_name')
        last_name=body.get('last_name')
        major_list=body.get('major_id')
        #optionals
        semesters=body.get('cumulative_semester')
        student_status=body.get('status')
        full_name=first_name+last_name

        user=User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name)
        profile=UserProfile.objects.create(user=user, student_id=student_id, status=student_status)
        user.save()
        profile.save()
        login(request, user)

        serializer=self.get_serializer(user)
        data=serializer.data
        token, created=Token.objects.get_or_create(user=user)
        data["token"]=token.key

        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def logout(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        logout(request)
        return Response(status=status.HTTP_200_OK)


    @action(detail=False, methods=['PUT'])
    def login(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        username=body.get('username')
        password=body.get('password')
        user=User.objects.get(username=username, password=password)
        login(request, user)

        serializer=self.get_serializer(user)
        data=serializer.data
        token, created=Token.objects.get(user=user)
        data["token"]=token.key

        return Response(status=status.HTTP_200_OK)

            
    def retrieve(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        if pk != 'me':
            return Response({"error": "Can't see other user's information"}, status=status.HTTP_403_FORBIDDEN)

        serializer=self.get_serializer(user)
        data=serializer.data
        return Response(data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        if pk != 'me':
            return Response({"error": "Can't update other user's information"}, status=status.HTTP_403_FORBIDDEN)

        user = request.user
        userprofile=user.userprofile
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


        data=request.data
        if "student_id" in data:
            userprofile.student_id=data.get("student_id")
#        if data.hasOwnProperty("cumulative_semester"):
#            cumulative_semester=data.body.get("cumulative_semester")
        if "status" in data:
            userprofile.status=data.get("status")
        
        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data=serializer.data
        return Response(data, status=status.HTTP_200_OK)


    def delete(self, request, pk=None):
        if pk != 'me':
            return Response({"error": "Can't update other user's information"}, status=status.HTTP_403_FORBIDDEN)

        user=request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        userprofile=request.user.userprofile
        logout(request)
        user.delete()
        userprofile.delete()
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST', 'DELETE', 'GET'])    
    def major(self, request):
        user=request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


        if self.request.method == 'GET':
            ls=[]
            for major in Major.objects.all():
                ls.append({"id":major.id, "name":major.major_name, "type":major.major_type})
            body={"major":ls}

            return Response(body, status=status.HTTP_200_OK)        

        elif self.request.method == 'POST':
            major_id=request.query_params.get("major_id")
            major=Major.objects.get(id=major_id)
            UserMajor.objects.create(user=user, major=major)
        elif self.request.method == 'DELETE':
            major_id=request.query_params.get("major_id")
            major=Major.objects.get(id=major_id)
            usermajor=UserMajor.objects.get(user=user, major=major)
            usermajor.delete()
        ls=[]
        for usermajor in user.usermajor.objects.all():
            major=usermajor.major
            ls.append({"id":major.id, "name":major.major_name, "type":major.major_type})
        body={"major":ls}

        return Response(body, status=status.HTTP_200_OK)
    
