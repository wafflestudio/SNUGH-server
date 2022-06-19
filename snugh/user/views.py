from django.contrib.auth import get_user_model, login, logout
from django.db import transaction
from django.shortcuts import redirect
from rest_framework import status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from user.serializers import UserCreateSerializer, UserLoginSerializer, UserSerializer, UserMajorSerializer

User = get_user_model()


class UserSignUpView(GenericAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = (permissions.AllowAny, )

    # POST /signup/
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserLoginView(GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = (permissions.AllowAny, )

    # PUT /login/
    def put(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserLogoutView(GenericAPIView):
    permission_classes = (permissions.IsAuthenticated, )

    # GET /logout/
    def get(self, request):
        request.user.auth_token.delete()
        logout(request)
        return Response(status=status.HTTP_200_OK)


class UserViewSet(viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated, )

    def get_serializer_class(self):
        if self.action == "major":
            return UserMajorSerializer
        else:
            return UserSerializer

    # GET /user/me
    def retrieve(self, request, pk=None):
        if pk != 'me':
            raise PermissionDenied("Only 'me' allowed for pk")

        user = request.user
        data = self.get_serializer(user).data
        return Response(data, status=status.HTTP_200_OK)

    # PUT /user/me
    @transaction.atomic
    def update(self, request, pk=None):
        if pk != 'me':
            raise PermissionDenied("Only 'me' allowed for pk")

        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    # DEL /user/me
    @transaction.atomic
    def delete(self, request, pk=None):
        if pk != 'me':
            raise PermissionDenied("Only 'me' allowed for pk")

        user = request.user
        userprofile = user.userprofile
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
        if self.request.method == 'POST':
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid()
            serializer.create()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid()
            serializer.delete()
            return Response(serializer.data, status=status.HTTP_200_OK)

    def login_redirect(request):
        return redirect('http://snugh.s3-website.ap-northeast-2.amazonaws.com')
