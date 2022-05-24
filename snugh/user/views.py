from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import action
from user.models import *
from user.serializers import *
from user.const import *
from django.core.mail.message import EmailMessage
from django.contrib.auth import get_user_model

User = get_user_model()


class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # POST /user
    @transaction.atomic
    def create(self, request):
        body = request.data

        email = body.get('email')
        password = body.get('password')
        entrance_year = body.get('entrance_year')
        full_name = body.get('full_name')
        student_status = body.get('status')
        major_list = body.get('majors')

        error_list = []

        # error case 1
        if not email:
            error_list.append('email')
        if not password:
            error_list.append('password')
        if not entrance_year:
            error_list.append('entrance_year')
        if not full_name:
            error_list.append('full_name')
        if not student_status:
            error_list.append('status')
        if not major_list:
            error_list.append('majors')

        if len(error_list) > 0:
            error_msg = ''
            for error in error_list:
                error_msg += (error + ', ')
            error_msg = error_msg[:-2] + ' missing'
            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)

        # error case 2
        list1 = [email, password, entrance_year, full_name, student_status]
        list2 = ['str', 'str', 'int', 'str', 'str']
        list3 = ['email', 'password', 'entrance_year', 'full_name', 'status']
        for i in range(len(list1)):
            if list2[i] == 'str':
                isValid = isinstance(list1[i], str)
            elif list2[i] == 'int':
                isValid = isinstance(list1[i], int)
            if not isValid:
                error_list.append(list3[i])

        if len(error_list) > 0:
            error_msg = ''
            for error in error_list:
                error_msg += (error + ', ')
            error_msg = error_msg[:-2]+' wrong_type'
            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)

        # error case 3
        if '@' not in email:
            return Response({'error':'email wrong_format'}, status=status.HTTP_400_BAD_REQUEST)
        if len(password) < 6:
            return Response({'error': 'password wrong_range(more than 6 letters)'}, status=status.HTTP_400_BAD_REQUEST)
        if entrance_year < 1000 or entrance_year > 9999:
            return Response({'error': 'entrance_year wrong_range(4 digits)'}, status=status.HTTP_400_BAD_REQUEST)
        if len(full_name) < 2 or len(full_name) > 30:
            return Response({'error': 'full_name wrong_range(2~30 letters)'}, status=status.HTTP_400_BAD_REQUEST)

        # error case 4
        if self.get_queryset().filter(username=email).exists():
            return Response({'error': 'email already_exist'}, status=status.HTTP_400_BAD_REQUEST)

        # error case 5
        if len(major_list) == 0:
            return Response({'error': 'major missing'}, status=status.HTTP_400_BAD_REQUEST)
        elif len(major_list) == 1:
            major = major_list[0]
            if major['major_type'] != MAJOR:
                return Response({'error': 'major_type not_allowed'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            major_count = 0
            for major in major_list:
                if major['major_type'] == MAJOR:
                    major_count += 1
            if major_count == 0:
                return Response({'error': 'major_type not_allowed'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=email, email=email, password=password, first_name=full_name)
        UserProfile.objects.create(user=user, entrance_year=entrance_year, status=student_status)

        for major in major_list:
            searched_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
            UserMajor.objects.create(user=user, major=searched_major)

        login(request, user)

        data = self.get_serializer(user).data
        token, created = Token.objects.get_or_create(user=user)
        data['token'] = token.key
        return Response(data, status=status.HTTP_201_CREATED)

    # GET /user/logout
    @action(detail=False, methods=['GET'])
    def logout(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'no_token'}, status=status.HTTP_401_UNAUTHORIZED)

        request.user.auth_token.delete()
        logout(request)
        return Response(status=status.HTTP_200_OK)

    # PUT /user
    @action(detail=False, methods=['PUT'])
    def login(self, request):
        username = request.data.get('email')
        password = request.data.get('password')

        # error case 1
        if not username:
            return Response({'error': 'username missing'}, status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({'error': 'password missing'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            data = self.get_serializer(user).data
            token, created = Token.objects.get_or_create(user=user)
            data['token'] = token.key
            return Response(data, status=status.HTTP_200_OK)
        return Response({'error': 'username or password wrong'}, status=status.HTTP_403_FORBIDDEN)

    # GET /user/me
    def retrieve(self, request, pk=None):
        user = request.user

        # error case 1
        if not request.user.is_authenticated:
            return Response({'error':'no_token'}, status=status.HTTP_401_UNAUTHORIZED)

        # error case 2
        if pk != 'me':
            return Response( {'error': 'pk≠me'}, status=status.HTTP_403_FORBIDDEN)

        data = self.get_serializer(user).data
        return Response(data, status=status.HTTP_200_OK)

    # PUT /user/me
    @transaction.atomic
    def update(self, request, pk=None):
        user = request.user
        userprofile = user.userprofile

        # error case 1
        if pk != 'me':
            return Response( {'error': 'pk≠me'}, status=status.HTTP_403_FORBIDDEN)

        # error case 2
        if not request.user.is_authenticated:
            return Response({'error':'no_token'}, status=status.HTTP_401_UNAUTHORIZED)

        # edit user
        body = request.data
        if 'entrance_year' in body:
            userprofile.entrance_year = body.get('entrance_year')
        if 'status' in body:
            userprofile.status = body.get('status')
        if 'full_name' in body:
            user.first_name = body.get('full_name')
        if 'password' in body:
            user.set_password(body.get('password'))

        serializer = self.get_serializer(user, data=body, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        userprofile.save()

        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)

    # DEL /user/me
    @transaction.atomic
    def delete(self, request, pk=None):
        user = request.user

        # error case 1
        if pk != 'me':
            return Response( {'error': 'pk≠me'}, status=status.HTTP_403_FORBIDDEN)

        # error case 2
        if not request.user.is_authenticated:
            return Response({'error': 'no_token'}, status=status.HTTP_401_UNAUTHORIZED)

        userprofile = request.user.userprofile
        token, created = Token.objects.get_or_create(user=user)
        logout(request)

        user.delete()
        userprofile.delete()
        token.delete()

        return Response(status=status.HTTP_200_OK)

    # POST/DELETE /user/major
    @action(detail=False, methods=['POST', 'DELETE'])
    @transaction.atomic
    def major(self, request):
        user = request.user

        # error case 1
        if not request.user.is_authenticated:
            return Response({'error': 'no_token'}, status=status.HTTP_401_UNAUTHORIZED)

        # error case 2
        major_name = request.data.get('major_name')
        major_type = request.data.get('major_type')

        if not Major.objects.filter(major_name=major_name, major_type=major_type).exists():
            return Response({'error': 'major not_exist'}, status=status.HTTP_400_BAD_REQUEST)

        searched_major = Major.objects.get(major_name=major_name, major_type=major_type)

        # POST /user/major
        if self.request.method == 'POST':
            if UserMajor.objects.filter(user=user, major__major_name=major_name).exists():
                return Response({'error': 'major already_exist'}, status=status.HTTP_400_BAD_REQUEST)

            UserMajor.objects.create(user=user, major=searched_major)
            try:
                changed_usermajor = UserMajor.objects.get(user=user, major__major_type=SINGLE_MAJOR)
                not_only_major = changed_usermajor.major
                changed_usermajor.delete()
                new_type_major = Major.objects.get(major_name=not_only_major.major_name, major_type=MAJOR)
                UserMajor.objects.create(user=user, major=new_type_major)
            except UserMajor.DoesNotExist:
                pass

        # DEL /user/major
        elif self.request.method == 'DELETE':
            if not UserMajor.objects.filter(user=user, major=searched_major).exists():
                return Response({'error': 'usermajor not_exist'}, status=status.HTTP_400_BAD_REQUEST)

            if len(list(UserMajor.objects.filter(user=user))) == 1:
                return Response({'error': 'The number of majors cannot be zero or minus.'}, status=status.HTTP_400_BAD_REQUEST)

            usermajor = UserMajor.objects.get(user=user, major=searched_major)
            usermajor.delete()

            changed_usermajor = UserMajor.objects.filter(user=user)
            if changed_usermajor.count() == 1:
                only_major = changed_usermajor.first().major
                if only_major.major_type == MAJOR:
                    changed_usermajor.first().delete()
                    new_type_major = Major.objects.get(major_name=only_major.major_name, major_type=SINGLE_MAJOR)
                    UserMajor.objects.create(user=user, major=new_type_major)

        majors = Major.objects.filter(usermajor__user=user)
        body = {'majors': MajorSerializer(majors, many=True).data}

        if self.request.method == 'POST':
            return Response(body, status=status.HTTP_201_CREATED)
        else:
            return Response(body, status=status.HTTP_200_OK)

    def login_redirect(request):
        return redirect('http://snugh.s3-website.ap-northeast-2.amazonaws.com')


class MajorViewSet(viewsets.GenericViewSet):
    queryset = Major.objects.all()

    # GET /major
    def list(self, request):
        search_keyword = request.query_params.get('search_keyword')
        major_type = request.query_params.get('major_type')

        majors = self.get_queryset().all()

        # filtering
        if search_keyword:
            majors = majors.filter(major_name__icontains=search_keyword)
        if major_type:
            majors = majors.filter(major_type=major_type)

        # remove duplicated major
        unique_major_list = []
        for major in majors:
            if major.major_name not in unique_major_list:
                unique_major_list.append(major.major_name)

        # remove default major
        if 'none' in unique_major_list:
            unique_major_list.remove('none')

        body = { 'majors': sorted(unique_major_list) }
        return Response(body, status=status.HTTP_200_OK)
