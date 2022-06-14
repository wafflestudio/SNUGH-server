from rest_framework import status, viewsets
from rest_framework.response import Response
from core.major.models import Major
from core.major.const import *


class MajorViewSet(viewsets.GenericViewSet):
    queryset = Major.objects.all()

    # GET /major
    def list(self, request):
        search_keyword = request.query_params.get('search_keyword')
        major_type = request.query_params.get('major_type')

        # remove default major
        majors = self.get_queryset().all().exclude(id=1)

        # filtering
        if search_keyword:
            majors = majors.filter(major_name__icontains=search_keyword)
        if major_type:
            majors = majors.filter(major_type=major_type)

        # remove duplicated major
        results = sorted(list(set(majors.values_list('major_name', flat=True))))

        body = { 'majors': results }
        return Response(body, status=status.HTTP_200_OK)
