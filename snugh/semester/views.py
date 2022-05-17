from django.db import transaction
from rest_framework import status, viewsets, generics
from rest_framework.response import Response
from snugh.permissions import IsOwnerOrCreateReadOnly
from snugh.exceptions import FieldError
from semester.models import Semester
from semester.serializers import SemesterSerializer


class SemesterViewSet(viewsets.GenericViewSet, generics.RetrieveDestroyAPIView):
    """
    Generic ViewSet of Semester Object.
    """
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer
    permission_classes = [IsOwnerOrCreateReadOnly]

    # POST /semester
    @transaction.atomic
    def create(self, request):
        """Create new semester."""
        data = request.data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # PUT /semester/:semesterId
    @transaction.atomic
    def update(self, request, pk=None):
        """
        Update semester.
        # TODO: SemesterLectures? Duplication Error?
        """
        data = request.data
        semester = self.get_object()
        year = data.get('year')
        semester_type = data.get('semester_type')
        if not (year or semester_type):
            raise FieldError("Field missing [year, semester_type]")
        serializer = self.get_serializer(semester, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(semester, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # DEL /semester/:semesterId
    def destroy(self, request, pk=None):
        """Destroy semester."""
        return super().destroy(request, pk)
    
    # GET /semester/:semesterId
    def retrieve(self, request, pk=None):
        """Retrieve semester."""
        return super().retrieve(request, pk)
