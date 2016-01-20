from django.contrib.sites.shortcuts import get_current_site
from django.views.generic import DetailView, TemplateView
import os
from mirrordb.models import Condition, GraspObservationCondition, GraspPerformanceCondition, Unit, Experiment
from uscbp import settings

class IndexView(TemplateView):
    template_name = 'mirrordb/index.html'


class ConditionDetailView(DetailView):
    model=Condition
    permission_required = 'view'

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if GraspObservationCondition.objects.filter(id=pk).count():
            self.model=GraspObservationCondition
            self.template_name = 'mirrordb/condition/grasp_observation_condition_view.html'
        elif GraspPerformanceCondition.objects.filter(id=pk).count():
            self.model = GraspPerformanceCondition
            self.template_name = 'mirrordb/condition/grasp_performance_condition_view.html'
        return super(ConditionDetailView,self).get_object(queryset=queryset)

    def get_context_data(self, **kwargs):
        context=super(ConditionDetailView,self).get_context_data(**kwargs)
        context['site_url']='http://%s' % get_current_site(self.request)
        context['video_url_mp4']=''
        if os.path.exists(os.path.join(settings.MEDIA_ROOT,'video','condition_%d.mp4' % self.object.id)):
            context['video_url_mp4']=''.join(['http://', get_current_site(None).domain, os.path.join('/media/video/',
                'condition_%d.mp4' % self.object.id)])
        return context


class UnitDetailView(DetailView):
    model = Unit
    template_name = 'mirrordb/unit/unit_view.html'

class ExperimentDetailView(DetailView):
    model = Experiment
    template_name = 'mirrordb/experiment/experiment_view.html'

class SearchView(TemplateView):
    template_name = 'mirrordb/search.html'
