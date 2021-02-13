from django.shortcuts import render
from rest_framework import status, viewsets, filters 
from rest_framework.response import Response
from lecture.models import * 
from user.models import *

# Create your views here.

class PlanViewSet(viewsets.GenericViewSet):
    queryset = Plan.objects.all()

    @action(detail=True, methods=['POST', 'DELETE', 'GET'])    
    def major(self, request, pk=None):    


        plan_id=request.query_params.get("plan_id")
        plan=Plan.objects.get(id=plan_id)

        if self.request.method == 'GET':
            planmajor=PlanMajor.objects.filter(plan=plan)

        else:
            major_id=request.query_params.get("major_id")
            major=Major.objects.get(id=major_id)
            if self.request.method == 'POST':
                PlanMajor.objects.create(plan=plan, major=major)
            elif self.request.method == 'DELETE':
                planmajor=PlanMajor.objects.get(plan=plan, major=major)
            
            planmajor=PlanMajor.objects.filter(plan=plan)
            
        ls=[]
        for major in planmajor.major.all():
            ls.append({"id":major.id, "name":major.major_name, "type":major.major_type})
    
        
        body={"plan_id":plan.id, "major":ls}

        if self.request.method == 'POST':
            return Response(body, status=status.HTTP_201_CREATED)
        else:
            return Response(body, status=status.HTTP_200_OK)
    