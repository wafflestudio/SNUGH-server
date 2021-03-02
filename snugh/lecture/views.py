from django.shortcuts import render
from rest_framework import status, viewsets, filters 
from rest_framework.response import Response
from lecture.models import * 
from user.models import *
from rest_framework.decorators import action

# Create your views here.

class PlanViewSet(viewsets.GenericViewSet):
    queryset = Plan.objects.all()

    #POST/GET/DELETE /plan/major/
    @action(detail=True, methods=['POST', 'DELETE', 'GET'])    
    def major(self, request, pk=None):    
        plan_id=request.query_params.get("plan_id")
        plan=Plan.objects.get(id=plan_id)

        #err response 1
        if not bool(plan_id):
            return Response({"error":"plan_id missing"}, status=status.HTTP_400_BAD_REQUEST)    

        #GET planmajor
        if self.request.method == 'GET':
            planmajor=PlanMajor.objects.filter(plan=plan)
        else:
            major_id=request.query_params.get("major_id")

            #err response 2
            if not bool(major_id):
                return Response({"error":"major_id missing"}, status=status.HTTP_400_BAD_REQUEST)    
            #err response 3
            try:
                major=Major.objects.get(id=major_id)
            except Major.DoesNotExist:
                return Response({"error":"No major matching the given major_id and plan id"}, status=status.HTTP_404_NOT_FOUND)

            #POST planmajor
            if self.request.method == 'POST':
                PlanMajor.objects.create(plan=plan, major=major)
            #DELETE planmajor
            elif self.request.method == 'DELETE':
                planmajor=PlanMajor.objects.get(plan=plan, major=major)
                planmajor.delete()            

            planmajor=PlanMajor.objects.filter(plan=plan)

        #main response            
        ls=[]
        for major in planmajor.major.all():
            ls.append({"id":major.id, "name":major.major_name, "type":major.major_type})        
        body={"plan_id":plan.id, "major":ls}
        if self.request.method == 'POST':
            return Response(body, status=status.HTTP_201_CREATED)
        else:
            return Response(body, status=status.HTTP_200_OK)