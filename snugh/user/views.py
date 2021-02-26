from django.shortcuts import render
from rest_framework import status, viewsets
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from user.models import *
from user.serializers import *
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import action

class UserViewSet(viewsets.GenericViewSet):
    queryset=User.objects.all()
    serializer_class=UserSerializer

    # POST /user/    
    def create(self, request):
        body=request.data
        username=body.get('username')
        password=body.get('password')
        student_id=body.get('student_id')
        first_name=body.get('first_name')
        last_name=body.get('last_name')
        major_list=body.get('major_id')
        student_status=body.get('status')

        #err response 1
        if not ( bool(username) and bool(password) and bool(student_id) and bool (first_name) and bool(last_name) and bool (major_list) and bool(student_status) ):
            return Response({"error":"Required fields missing"}, status=status.HTTP_400_BAD_REQUEST)
        #err response 2
        try: 
            UserProfile.objects.get(student_id=student_id)
            return Response({"error":"existing user"}, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            pass

        #create user
        user=User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name)
        UserProfile.objects.create(user=user, student_id=student_id, status=student_status)
        for major in major_list:
            UserMajor.objects.create(user=user, major=Major.objects.get(id=major))
        login(request, user)

        #main response 
        serializer=self.get_serializer(user)
        data=serializer.data
        token, created= Token.objects.get_or_create(user=user)
        data["token"]=token.key
        return Response(data, status=status.HTTP_201_CREATED)

    #GET /user/logout
    @action(detail=False, methods=['GET'])
    def logout(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        logout(request)
        return Response(status=status.HTTP_200_OK)


    #PUT /user/
    @action(detail=False, methods=['PUT'])
    def login(self, request):
        username=request.data.get('username')
        password=request.data.get('password')

        #err response 1
        if not bool(username):
            return Response({"error":"username missing"}, status=status.HTTP_400_BAD_REQUEST)
        #err response 2
        if not bool(password):
            return Response({"error":"password missing"}, status=status.HTTP_400_BAD_REQUEST)

        #login
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            #main response
            data = self.get_serializer(user).data
            token, created = Token.objects.get_or_create(user=user)
            data['token'] = token.key
            return Response(data, status=status.HTTP_200_OK)
        return Response({"error": "Wrong username or wrong password"}, status=status.HTTP_403_FORBIDDEN)

    #GET /user/me/
    def retrieve(self, request, pk=None):
        user = request.user

        #err response 1
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        #err response 2        
        if pk != 'me':
            return Response({"error": "Can't see other user's information"}, status=status.HTTP_403_FORBIDDEN)

        #main response
        serializer=self.get_serializer(user)
        data=serializer.data
        return Response(data, status=status.HTTP_200_OK)

    #PUT /user/me/
    def update(self, request, pk=None):
        user = request.user
        userprofile=user.userprofile

        #err response 1
        if pk != 'me':
            return Response({"error": "Can't update other user's information"}, status=status.HTTP_403_FORBIDDEN)
        #err response 2
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


        #edit user
        data=request.data
        if "student_id" in data:
            userprofile.student_id=data.get("student_id")
        if "status" in data:
            userprofile.status=data.get("status")        
        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        #main response
        data=serializer.data
        return Response(data, status=status.HTTP_200_OK)

    #DEL /user/me/
    def delete(self, request, pk=None):
        user=request.user

        #err response 1        
        if pk != 'me':
            return Response({"error": "Can't update other user's information"}, status=status.HTTP_403_FORBIDDEN)
        #err response 2
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        #delete user&logout
        userprofile=request.user.userprofile
        token, created= Token.objects.get_or_create(user=user)
        logout(request)
        user.delete()
        userprofile.delete()
        token.delete()

        #main response
        return Response(status=status.HTTP_200_OK)

    #POST/DELETE/GET /user/major/  
    @action(detail=False, methods=['POST', 'DELETE', 'GET'])    
    def major(self, request):
        user=request.user

        #err response 1
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        #GET all majors
        if self.request.method == 'GET':
            name=request.query_params.get('name')
            ls=[]

            if name:
                majors=Major.objects.filter(major_name__contains=name)
            else: 
                majors=Major.objects.all()

            for major in majors:
                ls.append({"id":major.id, "name":major.major_name, "type":major.major_type})
            body={"major":ls}
            return Response(body, status=status.HTTP_200_OK)        

        else:
            major_id=request.query_params.get("major_id")
            #err response 2
            if not bool(major_id):
                return Response({"error":"major_id missing"}, status=status.HTTP_400_BAD_REQUEST)    
            #err response 3
            try:
                major=Major.objects.get(id=major_id)
            except Major.DoesNotExist:
                return Response({"error":"No major with the given major_id"}, status=status.HTTP_404_NOT_FOUND)    

            #POST usermajor
            if self.request.method == 'POST':
                UserMajor.objects.create(user=user, major=major)
            #DEL usermajor
            elif self.request.method == 'DELETE':
                try:
                    usermajor=UserMajor.objects.get(user=user, major=major)
                #err response 4
                except UserMajor.DoesNotExist:
                    return Response({"error":"wrong major_id"}, status=status.HTTP_400_BAD_REQUEST)
                usermajor.delete()

        #main response
        ls=[]
        for usermajor in user.usermajor.all():
            major=usermajor.major
            ls.append({"id":major.id, "name":major.major_name, "type":major.major_type})
        body={"major":ls}

        if self.request.method == 'POST':
            return Response(body, status=status.HTTP_201_CREATED)
        else:
            return Response(body, status=status.HTTP_200_OK)
    
