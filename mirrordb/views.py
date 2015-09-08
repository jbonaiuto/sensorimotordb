from django.contrib.sites.shortcuts import get_current_site
from django.views.generic import DetailView
import os
from mirrordb.models import Condition, GraspObservationCondition, GraspPerformanceCondition, Unit
from uscbp import settings

class ConditionView(DetailView):
    permission_required = 'view'

    def get_context_data(self, **kwargs):
        context=super(ConditionView,self).get_context_data(**kwargs)
        context['site_url']='http://%s' % get_current_site(self.request)
        context['video_url_mp4']=''
        if os.path.exists(os.path.join(settings.MEDIA_ROOT,'video','condition_%d.mp4' % self.object.id)):
            context['video_url_mp4']=''.join(['http://', get_current_site(None).domain, os.path.join('/media/video/',
                'condition_%d.mp4' % self.object.id)])
        return context


class GraspObservationConditionDetailView(ConditionView):
    model = GraspObservationCondition
    template_name = 'mirrordb/condition/grasp_observation_condition_view.html'


class GraspPerformanceConditionDetailView(ConditionView):
    model = GraspPerformanceCondition
    template_name = 'mirrordb/condition/grasp_performance_condition_view.html'


class UnitDetailView(DetailView):
    model = Unit
    template_name = 'mirrordb/unit/unit_view.html'