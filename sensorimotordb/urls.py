# urls.py
from django.conf.urls import patterns, include, url
from tastypie.api import Api
from sensorimotordb.api import ExperimentResource, UnitResource, BrainRegionResource, RecordingTrialResource, EventResource, GraspObservationConditionResource, SpeciesResource, GraspPerformanceConditionResource, UnitRecordingResource, NomenclatureResource, UserResource, ConditionResource, FullRecordingTrialResource, VisuomotorClassificationAnalysisResource, VisuomotorClassificationAnalysisResultsResource, UnitClassificationResource, AnalysisResource, FactorResource, LevelResource, UnitAnalysisResultsResource, VisuomotorClassificationUnitAnalysisResultsResource, AnalysisResultsResource, MirrorTypeClassificationUnitAnalysisResultsResource, MirrorTypeClassificationAnalysisResource, MirrorTypeClassificationAnalysisResultsResource
from sensorimotordb.views import UnitDetailView, ConditionDetailView, ExperimentDetailView, SearchView, IndexView, ExperimentExportRequestView, ExperimentExportRequestDenyView, ExperimentExportRequestApproveView, ExperimentExportView, AnalysisResultsDetailView, VisuomotorClassificationAnalysisResultsDetailView, CreateVisuomotorClassificationAnalysisView, DeleteVisuomotorClassificationAnalysisResultsView, DeleteAnalysisResultsView, MirrorTypeClassificationAnalysisResultsDetailView, CreateMirrorTypeClassificationAnalysisView, DeleteMirrorTypeClassificationAnalysisResultsView, DeleteExperimentView, UpdateExperimentView

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
v1_api.register(AnalysisResource())
v1_api.register(VisuomotorClassificationAnalysisResource())
v1_api.register(AnalysisResultsResource())
v1_api.register(VisuomotorClassificationAnalysisResultsResource())
v1_api.register(UnitClassificationResource())
v1_api.register(FactorResource())
v1_api.register(LevelResource())
v1_api.register(UnitAnalysisResultsResource())
v1_api.register(VisuomotorClassificationUnitAnalysisResultsResource())
v1_api.register(MirrorTypeClassificationUnitAnalysisResultsResource())
v1_api.register(MirrorTypeClassificationAnalysisResource())
v1_api.register(MirrorTypeClassificationAnalysisResultsResource())

urlpatterns = patterns('',
    (r'^api/', include(v1_api.urls)),
    (r'^search/', SearchView.as_view(), {}, 'search_view'),
    (r'^experiment/(?P<pk>\d+)/$', ExperimentDetailView.as_view(), {}, 'experiment_view'),
    (r'^condition/(?P<pk>\d+)/$', ConditionDetailView.as_view(), {}, 'condition_view'),
    (r'^unit/(?P<pk>\d+)/$', UnitDetailView.as_view(), {}, 'unit_view'),
    (r'^experiment/(?P<pk>\d+)/edit/$', UpdateExperimentView.as_view(), {}, 'experiment_edit'),
    (r'^experiment/(?P<pk>\d+)/delete/$', DeleteExperimentView.as_view(), {}, 'experiment_delete'),
    (r'^experiment/(?P<pk>\d+)/export_request/$', ExperimentExportRequestView.as_view(), {}, 'experiment_export_request_view'),
    (r'^experiment/(?P<pk>\d+)/export_request/deny/(?P<activation_key>\w+)/$', ExperimentExportRequestDenyView.as_view(),
        {}, 'experiment_export_request_deny'),
    (r'^experiment/(?P<pk>\d+)/export_request/approve/(?P<activation_key>\w+)/$', ExperimentExportRequestApproveView.as_view(),
        {}, 'experiment_export_request_approve'),
    (r'^experiment/(?P<pk>\d+)/export/$', ExperimentExportView.as_view(), {}, 'experiment_export_view'),
    (r'^analysis_results/(?P<pk>\d+)/$', AnalysisResultsDetailView.as_view(), {}, 'analysis_results_view'),
    (r'^analysis_results/(?P<pk>\d+)/delete/$', DeleteAnalysisResultsView.as_view(), {}, 'analysis_results_delete'),
    (r'^visuomotor_classification_analysis_results/(?P<pk>\d+)/$', VisuomotorClassificationAnalysisResultsDetailView.as_view(), {}, 'visuomotor_classification_analysis_results_view'),
    (r'^visuomotor_classification_analysis/new/$', CreateVisuomotorClassificationAnalysisView.as_view(), {}, 'visuomotor_classification_analysis_add'),
    (r'^visuomotor_classification_analysis_results/(?P<pk>\d+)/delete/$', DeleteVisuomotorClassificationAnalysisResultsView.as_view(), {}, 'visuomotor_classification_analysis_results_delete'),
    (r'^mirror_type_classification_analysis_results/(?P<pk>\d+)/$', MirrorTypeClassificationAnalysisResultsDetailView.as_view(), {}, 'mirror_type_classification_analysis_results_view'),
    (r'^mirror_type_classification_analysis/new/$', CreateMirrorTypeClassificationAnalysisView.as_view(), {}, 'mirror_type_classification_analysis_add'),
    (r'^mirror_type_classification_analysis_results/(?P<pk>\d+)/delete/$', DeleteMirrorTypeClassificationAnalysisResultsView.as_view(), {}, 'mirror_type_classification_analysis_results_delete'),
    (r'', IndexView.as_view(), {}, 'index'),
)