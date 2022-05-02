from django.core.paginator import Paginator
from rest_framework import status, viewsets, generics
from rest_framework.response import Response
from bug_report.models import BugReport
from bug_report.serializers import BugReportSerializer
from snugh.permissions import IsOwnerOrCreateReadOnly


class BugReportViewSet(
    viewsets.GenericViewSet, 
    generics.CreateAPIView,
    generics.RetrieveUpdateDestroyAPIView):
    """
    Generic ViewSet of BugReport Object.
    """
    queryset = BugReport.objects.all()
    serializer_class = BugReportSerializer
    permission_classes = [IsOwnerOrCreateReadOnly]

    # GET /bug
    def list(self, request):
        """Get list of all bug reports."""
        page = request.GET.get('page', '1')
        category = request.GET.get('category')

        bug_reports = self.get_queryset().order_by('-created_at')
        if category:
            bug_reports.filter(category=category)

        bug_reports = Paginator(bug_reports, 5).get_page(page)
        serializer = self.get_serializer(bug_reports, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
