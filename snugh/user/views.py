from rest_framework import status, viewsets
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from user.models import *
from user.serializers import *
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import action


class MajorViewSet(viewsets.GenericViewSet):
    queryset = Major.objects.all()

    # GET /major/
    def list(self, request):
        user = request.user

        name = request.query_params.get('name')
        if name:
            majors = Major.objects.filter(major_name__contains=name)
        else:
            majors = Major.objects.all()

        ls = []
        for major in majors:
            if major.major_name not in ls:
                ls.append(major.major_name)
        body = {"majors": ls}
        return Response(body, status=status.HTTP_200_OK)


class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # POST /user/    
    def create(self, request):
        body = request.data
        errorls = []

        email=body.get('email')
        if not email:
            errorls.append('email')
        password=body.get('password')
        if not password:
            errorls.append('password')
        year=body.get('year')
        if not year:
            errorls.append('year')
        full_name=body.get('full_name')
        if not full_name:
            errorls.append('full_name')
        major_list=body.get('major_id')
        if not major_list:
            errorls.append('major_id')
        student_status=body.get('status')
        if not student_status:
            errorls.append('status')

        #err response 1
        if len(errorls)>0:
            text=""
            for j in errorls:
                text=text+j
                text=text+", "
            text=text[:-2]+" missing"
            return Response({"error":text}, status=status.HTTP_400_BAD_REQUEST)

        #err response 2
        ls1=[email, password, year, full_name, student_status]
        ls2=["str", "str", "int", "str", "str"]
        ls3=["email", "password", "year", "full_name", "status"]
        errorls=[]
        for i in range(0, len(ls1)):
            if ls2[i]=="str":
                a=isinstance(ls1[i], str)
            elif ls2[i]=="int":
                a=isinstance(ls1[i], int)
            if not a:
                errorls.append(ls3[i])

        if len(errorls)>0:
            text=""
            for j in errorls:
                text=text+j
                text=text+", "
            text=text[:-2]+" wrong_dtype"
            return Response({"error":text}, status=status.HTTP_400_BAD_REQUEST)

        if "@" not in email:
            return Response({"error":"email wrong_format"}, status=status.HTTP_400_BAD_REQUEST)
        if len(password)<6:
            return Response({"error":"password wrong_range(more than 6 letters)"}, status=status.HTTP_400_BAD_REQUEST)
        if year<1000 or year>9999:
            return Response({"error":"year wrong_range(4 digits)"}, status=status.HTTP_400_BAD_REQUEST)
        if len(full_name)<2 or len(full_name)>30:
            return Response({"error":"full_name wrong_range(2~30 letters)"}, status=status.HTTP_400_BAD_REQUEST)


        #err response 3
        try:
            User.objects.get(username=email)
            return Response({"error":"user already_exist"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            pass

        #create user
        user=User.objects.create_user(username=email, email=email, password=password, first_name=full_name)
        UserProfile.objects.create(user=user, year=year, status=student_status)
        for major in major_list:
            UserMajor.objects.create(user=user, major=Major.objects.get(id=major))
        login(request, user)

        #main response
        serializer=self.get_serializer(user)
        data=serializer.data
        token, created= Token.objects.get_or_create(user=user)
        data["token"]=token.key
        return Response(data, status=status.HTTP_201_CREATED)

    # GET /user/logout/
    @action(detail=False, methods=['GET'])
    def logout(self, request):
        if not request.user.is_authenticated:
            return Response({"error":"no_token"}, status=status.HTTP_401_UNAUTHORIZED)
        logout(request)
        return Response(status=status.HTTP_200_OK)

    # PUT /user/
    @action(detail=False, methods=['PUT'])
    def login(self, request):
        username = request.data.get('email')  # email을 username으로 사용하여 로그인
        password = request.data.get('password')

        # err response 1
        if not bool(username):
            return Response({"error": "username missing"}, status=status.HTTP_400_BAD_REQUEST)
        # err response 2
        if not bool(password):
            return Response({"error": "password missing"}, status=status.HTTP_400_BAD_REQUEST)

        # login
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # main response
            data = self.get_serializer(user).data
            token, created = Token.objects.get_or_create(user=user)
            data['token'] = token.key
            return Response(data, status=status.HTTP_200_OK)
        return Response({"error": "username or password wrong"}, status=status.HTTP_403_FORBIDDEN)

    # GET /user/me/
    def retrieve(self, request, pk=None):
        user = request.user

        #err response 1
        if not request.user.is_authenticated:
            return Response({"error":"no_token"}, status=status.HTTP_401_UNAUTHORIZED)
        #err response 2
        if pk != 'me':
            return Response( {"error": "pk≠me"}, status=status.HTTP_403_FORBIDDEN)

        # main response
        serializer = self.get_serializer(user)
        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)

    # PUT /user/me/
    def update(self, request, pk=None):
        user = request.user
        userprofile = user.userprofile

        # err response 1
        if pk != 'me':
            return Response( {"error": "pk≠me"}, status=status.HTTP_403_FORBIDDEN)
        #err response 2
        if not request.user.is_authenticated:
            return Response({"error":"no_token"}, status=status.HTTP_401_UNAUTHORIZED)

        # edit user
        data = request.data
        if "year" in data:
            userprofile.year = data.get("year")
            #####
            # (TBD) 사용자의 입학년도 변경에 따른 강의구분 및 졸업요건 재계산이 필요합니다.
            #####
        if "status" in data:
            userprofile.status=data.get("status")        
        if "full_name" in data:
            user.first_name=data.get("full_name")
        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # main response
        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)

    # DEL /user/me/
    def delete(self, request, pk=None):
        user = request.user

        # err response 1
        if pk != 'me':
            return Response( {"error": "pk≠me"}, status=status.HTTP_403_FORBIDDEN)
        #err response 2
        if not request.user.is_authenticated:
            return Response({"error":"no_token"}, status=status.HTTP_401_UNAUTHORIZED)

        # delete user & logout
        userprofile = request.user.userprofile
        token, created = Token.objects.get_or_create(user=user)
        logout(request)
        user.delete()
        userprofile.delete()
        token.delete()

        # main response
        return Response(status=status.HTTP_200_OK)

    # POST/DELETE /user/major/
    @action(detail=False, methods=['POST', 'DELETE'])
    def major(self, request):
        user = request.user

        #err response 1
        if not request.user.is_authenticated:
            return Response({"error":"no_token"}, status=status.HTTP_401_UNAUTHORIZED)

        # get query params
        if self.request.method == 'POST':
            major_name = request.data.get('major_name')
            major_type = request.data.get('major_type')
            try:
                searched_major = Major.objects.get(major_name=major_name, major_type=major_type)
                major_id = searched_major.id
            except Major.DoesNotExist:
                return Response({"error":"major not_exist"})
        elif self.request.method == 'DELETE':
            major_id=request.body.get("major_id")

        # err response 2
        if not bool(major_id):
            return Response({"error": "major_id missing"}, status=status.HTTP_400_BAD_REQUEST)
        # err response 3
        try:
            major = Major.objects.get(id=major_id)
        except Major.DoesNotExist:
            return Response({"error":"major not_exist"}, status=status.HTTP_404_NOT_FOUND)

        # POST /user/major/
        if self.request.method == 'POST':
            UserMajor.objects.create(user=user, major=major)
        # DEL /user/major/
        elif self.request.method == 'DELETE':
            try:
                usermajor = UserMajor.objects.get(user=user, major=major)
            # err response 4
            except UserMajor.DoesNotExist:
                return Response({"error":"major not_exist"}, status=status.HTTP_400_BAD_REQUEST)
            usermajor.delete()

        # main response
        ls = []
        for usermajor in user.usermajor.all():
            major = usermajor.major
            ls.append({"id": major.id, "major_name": major.major_name, "major_type": major.major_type})
        body = {"major": ls}

        if self.request.method == 'POST':
            return Response(body, status=status.HTTP_201_CREATED)
        else:
            return Response(body, status=status.HTTP_200_OK)

