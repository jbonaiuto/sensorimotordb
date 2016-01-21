# urls.py
from django.conf.urls import patterns, include, url
from tastypie.api import Api
from mirrordb.api import ExperimentResource, UnitResource, BrainRegionResource, RecordingTrialResource, EventResource, GraspObservationConditionResource, SpeciesResource, GraspPerformanceConditionResource, UnitRecordingResource, NomenclatureResource, UserResource, ConditionResource, FullRecordingTrialResource
from mirrordb.views import UnitDetailView, ConditionDetailView, ExperimentDetailView, SearchView, IndexView, ExperimentExportRequestView, ExperimentExportRequestDenyView, ExperimentExportRequestApproveView, ExperimentExportView

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
v1_api.register(FullRecordingTrialResource())

urlpatterns = patterns('',
    (r'^api/', include(v1_api.urls)),
    (r'^search/', SearchView.as_view(), {}, 'search_view'),
    (r'^experiment/(?P<pk>\d+)/$', ExperimentDetailView.as_view(), {}, 'experiment_view'),
    (r'^condition/(?P<pk>\d+)/$', ConditionDetailView.as_view(), {}, 'condition_view'),
    (r'^unit/(?P<pk>\d+)/$', UnitDetailView.as_view(), {}, 'unit_view'),
    (r'^experiment/(?P<pk>\d+)/export_request/$', ExperimentExportRequestView.as_view(), {}, 'experiment_export_request_view'),
    (r'^experiment/(?P<pk>\d+)/export_request/deny/(?P<activation_key>\w+)/$', ExperimentExportRequestDenyView.as_view(),
        {}, 'experiment_export_request_deny'),
    (r'^experiment/(?P<pk>\d+)/export_request/approve/(?P<activation_key>\w+)/$', ExperimentExportRequestApproveView.as_view(),
        {}, 'experiment_export_request_approve'),
    (r'^experiment/(?P<pk>\d+)/export/$', ExperimentExportView.as_view(), {}, 'experiment_export_view'),
    (r'', IndexView.as_view(), {}, 'index'),
)