# urls.py
from django.conf.urls import patterns, include
from tastypie.api import Api
from mirrordb.api import ExperimentResource, UnitResource, BrainRegionResource, RecordingTrialResource, EventResource, GraspObservationConditionResource, SpeciesResource, GraspPerformanceConditionResource, UnitRecordingResource, NomenclatureResource, UserResource, ConditionResource
from mirrordb.views import UnitDetailView, ConditionDetailView, ExperimentDetailView

v1_api = Api(api_name='v1')
v1_api.register(UserResource())
v1_api.register(SpeciesResource())
v1_api.register(NomenclatureResource())
v1_api.register(BrainRegionResource())
v1_api.register(ExperimentResource())
v1_api.register(ConditionResource())
v1_api.register(GraspObservationConditionResource())
v1_api.register(GraspPerformanceConditionResource())
v1_api.register(UnitResource())
v1_api.register(RecordingTrialResource())
v1_api.register(UnitRecordingResource())
v1_api.register(EventResource())

urlpatterns = patterns('',
    (r'^api/', include(v1_api.urls)),
    (r'^experiment/(?P<pk>\d+)/$', ExperimentDetailView.as_view(), {}, 'experiment_view'),
    (r'^condition/(?P<pk>\d+)/$', ConditionDetailView.as_view(), {}, 'condition_view'),
    (r'^unit/(?P<pk>\d+)/$', UnitDetailView.as_view(), {}, 'unit_view'),
)