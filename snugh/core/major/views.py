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