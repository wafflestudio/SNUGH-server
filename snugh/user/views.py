from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.models import User
from user.models import *
from user.serializers import *


class MajorViewSet(viewsets.GenericViewSet):
    queryset = Major.objects.all()

    # GET /major/
    @transaction.atomic
    def list(self, request):
        user = request.user

        search_keyword = request.query_params.get('search_keyword')
        if search_keyword:
            majors = Major.objects.filter(major_name__contains=search_keyword)
        else:
            majors = Major.objects.all()

        ls = []
        for major in majors:
            if major.major_name not in ls:
                ls.append(major.major_name)

        if "none" in ls:
            ls.remove("none")

        ls = sorted(ls)
        body = {"majors": ls}
        return Response(body, status=status.HTTP_200_OK)


class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # POST /user/
    @transaction.atomic
    def create(self, request):
        body = request.data
        errorls = []

        email = body.get('email')
        if not email:
            errorls.append('email')
        password = body.get('password')
        if not password:
            errorls.append('password')
        entrance_year = body.get('entrance_year')
        if not entrance_year:
            errorls.append('entrance_year')
        full_name = body.get('full_name')
        if not full_name:
            errorls.append('full_name')
        major_list = body.get('majors')
        if not major_list:
            errorls.append('majors')
        student_status = body.get('status')
        if not student_status:
            errorls.append('status')

        # err response 1
        if len(errorls) > 0:
            text = ""
            for j in errorls:
                text = text+j
                text = text+", "
            text = text[:-2]+" missing"
            return Response({"error": text}, status=status.HTTP_400_BAD_REQUEST)

        # err response 2
        ls1 = [email, password, entrance_year, full_name, student_status]
        ls2 = ["str", "str", "int", "str", "str"]
        ls3 = ["email", "password", "entrance_year", "full_name", "status"]
        errorls = []
        for i in range(0, len(ls1)):
            if ls2[i] == "str":
                a = isinstance(ls1[i], str)
            elif ls2[i] == "int":
                a = isinstance(ls1[i], int)
            if not a:
                errorls.append(ls3[i])

        if len(errorls) > 0:
            text = ""
            for j in errorls:
                text = text+j
                text = text+", "
            text = text[:-2]+" wrong_dtype"
            return Response({"error": text}, status=status.HTTP_400_BAD_REQUEST)

        if "@" not in email:
            return Response({"error":"email wrong_format"}, status=status.HTTP_400_BAD_REQUEST)
        if len(password) < 6:
            return Response({"error": "password wrong_range(more than 6 letters)"}, status=status.HTTP_400_BAD_REQUEST)
        if entrance_year < 1000 or entrance_year > 9999:
            return Response({"error": "entrance_year wrong_range(4 digits)"}, status=status.HTTP_400_BAD_REQUEST)
        if len(full_name) < 2 or len(full_name) > 30:
            return Response({"error": "full_name wrong_range(2~30 letters)"}, status=status.HTTP_400_BAD_REQUEST)

        # err response 3
        try:
            User.objects.get(username=email)
            return Response({"error": "user already_exist"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            pass

        # create user
        user = User.objects.create_user(username=email, email=email, password=password, first_name=full_name)
        UserProfile.objects.create(user=user, entrance_year=entrance_year, status=student_status)

        # register majors
        if len(major_list) == 0:
            return Response({"error": "major missing"}, status=status.HTTP_400_BAD_REQUEST)
        elif len(major_list) == 1:
            major = major_list[0]
            if major['major_type'] == Major.MAJOR:
                try:
                    searched_major = Major.objects.get(major_name=major['major_name'], major_type=Major.SINGLE_MAJOR)
                except Major.DoesNotExist:
                    return Response({"error": "major not_exist"}, status=status.HTTP_404_NOT_FOUND)
                UserMajor.objects.create(user=user, major=searched_major)
            else:
                return Response({"error": "major_type not_allowed"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            major_count = 0
            for major in major_list:
                if major['major_type'] == Major.SINGLE_MAJOR:
                    return Response({"error": "major_type not_allowed"}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    searched_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
                    if major['major_type'] == Major.MAJOR:
                        major_count += 1
                except Major.DoesNotExist:
                    return Response({"error": "major not_exist"}, status=status.HTTP_404_NOT_FOUND)
                UserMajor.objects.create(user=user, major=searched_major)
            if major_count == 0:
                return Response({"error": "major_type not_allowed"}, status=status.HTTP_400_BAD_REQUEST)

        # login user
        login(request, user)

        # main response
        serializer = self.get_serializer(user)
        data = serializer.data
        token, created = Token.objects.get_or_create(user=user)
        data["token"] = token.key
        return Response(data, status=status.HTTP_201_CREATED)

    # GET /user/logout/
    @action(detail=False, methods=['GET'])
    @transaction.atomic
    def logout(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "no_token"}, status=status.HTTP_401_UNAUTHORIZED)

        request.user.auth_token.delete()

        logout(request)
        return Response(status=status.HTTP_200_OK)

    # PUT /user/
    @action(detail=False, methods=['PUT'])
    @transaction.atomic
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
    @transaction.atomic
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
    @transaction.atomic
    def update(self, request, pk=None):
        user = request.user
        userprofile = user.userprofile

        # err response 1
        if pk != 'me':
            return Response( {"error": "pk≠me"}, status=status.HTTP_403_FORBIDDEN)
        # err response 2
        if not request.user.is_authenticated:
            return Response({"error":"no_token"}, status=status.HTTP_401_UNAUTHORIZED)

        # edit user
        data = request.data
        if "entrance_year" in data:
            userprofile.entrance_year = data.get("entrance_year")
        if "status" in data:
            userprofile.status = data.get("status")
        if "full_name" in data:
            user.first_name = data.get("full_name")

        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        userprofile.save()

        # main response
        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)

    # DEL /user/me/
    @transaction.atomic
    def delete(self, request, pk=None):
        user = request.user

        # err response 1
        if pk != 'me':
            return Response( {"error": "pk≠me"}, status=status.HTTP_403_FORBIDDEN)
        # err response 2
        if not request.user.is_authenticated:
            return Response({"error": "no_token"}, status=status.HTTP_401_UNAUTHORIZED)

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
    @transaction.atomic
    def major(self, request):
        user = request.user

        # err response 1
        if not request.user.is_authenticated:
            return Response({"error": "no_token"}, status=status.HTTP_401_UNAUTHORIZED)

        major_name = request.data.get('major_name')
        major_type = request.data.get('major_type')
        try:
            searched_major = Major.objects.get(major_name=major_name, major_type=major_type)
        except Major.DoesNotExist:
            return Response({"error": "major not_exist"})

        # POST /user/major/
        if self.request.method == 'POST':
            if UserMajor.objects.filter(user=user, major__major_name=major_name).exists():
                return Response({"error": "major already exist"}, status=status.HTTP_400_BAD_REQUEST)

            UserMajor.objects.create(user=user, major=searched_major)
            try:
                changed_usermajor = UserMajor.objects.get(user=user, major__major_type=Major.SINGLE_MAJOR)
                not_only_major = changed_usermajor.major
                changed_usermajor.delete()
                new_type_major = Major.objects.get(major_name=not_only_major.major_name,
                                                   major_type=Major.MAJOR)
                UserMajor.objects.create(user=user, major=new_type_major)
            except UserMajor.DoesNotExist:
                pass

        # DEL /user/major/
        elif self.request.method == 'DELETE':
            try:
                usermajor = UserMajor.objects.get(user=user, major=searched_major)
            except UserMajor.DoesNotExist:
                return Response({"error": "usermajor not_exist"}, status=status.HTTP_400_BAD_REQUEST)

            if len(list(UserMajor.objects.filter(user=user))) == 1:
                return Response({"error": "The number of majors cannot be zero or minus."}, status=status.HTTP_400_BAD_REQUEST)

            usermajor.delete()

            changed_usermajor = UserMajor.objects.filter(user=user)
            if changed_usermajor.count() == 1:
                only_major = changed_usermajor.first().major
                if only_major.major_type == Major.MAJOR:
                    changed_usermajor.first().delete()
                    new_type_major = Major.objects.get(major_name=only_major.major_name, major_type=Major.SINGLE_MAJOR)
                    UserMajor.objects.create(user=user, major=new_type_major)

        # main response
        majors = Major.objects.filter(usermajor__user=user)
        body = {"majors": MajorSerializer(majors, many=True).data}

        if self.request.method == 'POST':
            return Response(body, status=status.HTTP_201_CREATED)
        else:
            return Response(body, status=status.HTTP_200_OK)

