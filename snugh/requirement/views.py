from django.shortcuts import render
from rest_framework import status, viewsets, filters
from rest_framework.response import Response
from requirement.models import Requirement, PlanRequirement

class RequirementViewSet(viewsets.GenericViewSet):
    queryset = Requirement.objects.all()

    # GET /requirement

    # PUT /requirement

    # GET /requirement/progress
