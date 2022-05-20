from django.db import transaction
from rest_framework import status, viewsets, generics
from rest_framework.response import Response
from snugh.permissions import IsOwnerOrCreateReadOnly
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

    
    # DEL /semester/:semesterId
    def destroy(self, request, pk=None):
        """Destroy semester."""
        return super().destroy(request, pk)
    
    # GET /semester/:semesterId
    def retrieve(self, request, pk=None):
        """Retrieve semester."""
        return super().retrieve(request, pk)
