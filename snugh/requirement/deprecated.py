# Deprecated
#     @transaction.atomic
#     def put(self, request):
#         user = request.user
#         if not user.is_authenticated:
#             return Response(status=status.HTTP_401_UNAUTHORIZED)
#
#         update_list = request.data.copy()
#         for curr_request in update_list:
#             plan_id = curr_request['plan_id']
#             requirement_id = curr_request['requirement_id']
#             is_fulfilled = curr_request['is_fulfilled']
#
#             plan = Plan.objects.get(pk=plan_id)
#             requirement = Requirement.objects.get(pk=requirement_id)
#             planrequirement = PlanRequirement.objects.filter(plan=plan, requirement=requirement)
#             planrequirement.update(is_fulfilled=is_fulfilled)
#
#         return Response(status=status.HTTP_200_OK)