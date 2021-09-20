from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from rest_framework import status, viewsets
from rest_framework.response import Response
from bug_report.models import BugReport
from bug_report.serializers import BugReportSerializer


class BugReportViewSet(viewsets.GenericViewSet):
    queryset = BugReport.objects.all()
    serializer_class = BugReportSerializer

    # POST /bug
    def create(self, request):
        body = request.data
        user = request.user
        title = body.get('title')
        description = body.get('description')
        bug_report = BugReport.objects.create(user=request.user, title=title, description=description)
        serializer = self.get_serializer(bug_report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # GET /bug
    def list(self, request):
        page = request.GET.get('page', '1')
        bug_reports = self.get_queryset().order_by('created_at')
        bug_reports = Paginator(bug_reports, 5).get_page(page)
        serializer = self.get_serializer(bug_reports, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # DELETE /bug/:bugId
    def delete(self, request, pk=None):
        bug_report = get_object_or_404(BugReport, pk=pk)
        bug_report.delete()
        return Response(status=status.HTTP_200_OK)
