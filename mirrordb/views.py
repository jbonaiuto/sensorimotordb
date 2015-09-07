from django.views.generic import DetailView
from mirrordb.models import Condition, GraspObservationCondition

class GraspObservationConditionDetailView(DetailView):
    model = GraspObservationCondition
    template_name = 'mirrordb/condition/grasp_observation_condition_view.html'
    permission_required = 'view'
