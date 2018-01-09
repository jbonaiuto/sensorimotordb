# urls.py
from django.conf.urls import patterns, include, url
from tastypie.api import Api
from sensorimotordb.api import ExperimentResource, UnitResource, BrainRegionResource, RecordingTrialResource, \
    EventResource, GraspObservationConditionResource, SpeciesResource, GraspPerformanceConditionResource, \
    UnitRecordingResource, NomenclatureResource, UserResource, ConditionResource, FullRecordingTrialResource, \
    UnitClassificationResource, AnalysisResource,   AnalysisResultsResource, ANOVAResource, ANOVAFactorResource, \
    ANOVAFactorLevelResource, ANOVAEffectResource, UnitClassificationTypeResource, ClassificationAnalysisResultsResource, \
    ClassificationAnalysisResource, AnalysisSettingsResource, ClassificationAnalysisSettingsResource, \
    ClassificationAnalysisResultsLevelMappingResource, PenetrationResource, TimeWindowFactorLevelSettingsResource, SubjectResource, ClusterAnalysisResultsResource
from sensorimotordb.views import UnitDetailView, ConditionDetailView, ExperimentDetailView, SearchView, IndexView, \
    ExperimentExportRequestView, ExperimentExportRequestDenyView, ExperimentExportRequestApproveView, ExperimentExportView, \
    DeleteExperimentView, UpdateExperimentView, UpdateConditionView, DeleteConditionView, CreateANOVAView, ANOVADetailView, \
    DeleteANOVAView, ClassificationAnalysisDetailView, DeleteUnitClassificationConditionView, DeleteUnitClassificationTypeView, \
    CreateUnitClassificationTypeView, UpdateUnitClassificationTypeView, CreateClassificationAnalysisWizardView, \
    CLASSIFICATION_ANALYSIS_WIZARD_FORMS, AnalysisListDetailView, DeleteClassificationAnalysisView, RunAnalysisView, \
    RunClassificationAnalysisView, DeleteAnalysisResultsView, AnalysisResultsDetailView, ClassificationAnalysisResultsDetailView, \
    FullRecordingTrialApiProfileView, ExperimentApiProfileView, ConditionApiProfileView, ClusterAnalysisDetailView, RunClusterAnalysisView, CreateClusterAnalysisView, ClusterAnalysisResultsDetailView
from uscbp import settings

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
v1_api.register(ClassificationAnalysisResource())
v1_api.register(AnalysisResultsResource())
v1_api.register(ClassificationAnalysisResultsResource())
v1_api.register(UnitClassificationResource())
v1_api.register(UnitClassificationTypeResource())
v1_api.register(AnalysisSettingsResource())
v1_api.register(ClassificationAnalysisSettingsResource())
v1_api.register(ClassificationAnalysisResultsLevelMappingResource())
v1_api.register(TimeWindowFactorLevelSettingsResource())
v1_api.register(ANOVAResource())
v1_api.register(ANOVAFactorResource())
v1_api.register(ANOVAFactorLevelResource())
v1_api.register(ANOVAEffectResource())
v1_api.register(PenetrationResource())
v1_api.register(SubjectResource())
v1_api.register(ClusterAnalysisResultsResource())

urlpatterns = patterns('',
    (r'^analysis/$', AnalysisListDetailView.as_view(), {}, 'analysis_list'),
    (r'^analysis/(?P<pk>\d+)/run/$', RunAnalysisView.as_view(), {}, 'analysis_run'),
    (r'^analysis_results/(?P<pk>\d+)/$', AnalysisResultsDetailView.as_view(), {}, 'analysis_results_view'),
    (r'^analysis_results/(?P<pk>\d+)/delete/$', DeleteAnalysisResultsView.as_view(), {}, 'analysis_results_delete'),
    (r'^anova/(?P<pk>\d+)/$', ANOVADetailView.as_view(), {}, 'anova_view'),
    (r'^anova/(?P<pk>\d+)/delete/$', DeleteANOVAView.as_view(), {}, 'anova_delete'),
    (r'^anova/new/$', CreateANOVAView.as_view(), {}, 'anova_add'),
    (r'^api/', include(v1_api.urls)),
    (r'^classification_analysis/(?P<pk>\d+)/$', ClassificationAnalysisDetailView.as_view(), {}, 'classification_analysis_view'),
    (r'^classification_analysis/(?P<pk>\d+)/delete/$', DeleteClassificationAnalysisView.as_view(), {}, 'classification_analysis_delete'),
    (r'^classification_analysis/(?P<pk>\d+)/run/$', RunClassificationAnalysisView.as_view(), {}, 'classification_analysis_run'),
    (r'^classification_analysis/new/$', CreateClassificationAnalysisWizardView.as_view(CLASSIFICATION_ANALYSIS_WIZARD_FORMS), {}, 'classification_analysis_add'),
    (r'^classification_analysis_results/(?P<pk>\d+)/$', ClassificationAnalysisResultsDetailView.as_view(), {}, 'classification_analysis_results_view'),
    (r'^cluster_analysis/(?P<pk>\d+)/$', ClusterAnalysisDetailView.as_view(), {}, 'cluster_analysis_view'),
    (r'^cluster_analysis/(?P<pk>\d+)/run/$', RunClusterAnalysisView.as_view(), {}, 'cluster_analysis_run'),
    (r'^cluster_analysis/new/$', CreateClusterAnalysisView.as_view(), {}, 'cluster_analysis_add'),
    (r'^cluster_analysis_results/(?P<pk>\d+)/$', ClusterAnalysisResultsDetailView.as_view(), {}, 'cluster_analysis_results_view'),
    (r'^condition/(?P<pk>\d+)/$', ConditionDetailView.as_view(), {}, 'condition_view'),
    (r'^condition/(?P<pk>\d+)/delete/$', DeleteConditionView.as_view(), {}, 'condition_edit'),
    (r'^condition/(?P<pk>\d+)/edit/$', UpdateConditionView.as_view(), {}, 'condition_edit'),
    (r'^experiment/(?P<pk>\d+)/$', ExperimentDetailView.as_view(), {}, 'experiment_view'),
    (r'^experiment/(?P<pk>\d+)/delete/$', DeleteExperimentView.as_view(), {}, 'experiment_delete'),
    (r'^experiment/(?P<pk>\d+)/edit/$', UpdateExperimentView.as_view(), {}, 'experiment_edit'),
    (r'^experiment/(?P<pk>\d+)/export_request/$', ExperimentExportRequestView.as_view(), {}, 'experiment_export_request_view'),
    (r'^experiment/(?P<pk>\d+)/export_request/deny/(?P<activation_key>\w+)/$', ExperimentExportRequestDenyView.as_view(), {}, 'experiment_export_request_deny'),
    (r'^experiment/(?P<pk>\d+)/export_request/approve/(?P<activation_key>\w+)/$', ExperimentExportRequestApproveView.as_view(), {}, 'experiment_export_request_approve'),
    (r'^experiment/(?P<pk>\d+)/export/$', ExperimentExportView.as_view(), {}, 'experiment_export_view'),
    (r'^search/', SearchView.as_view(), {}, 'search_view'),
    (r'^unit/(?P<pk>\d+)/$', UnitDetailView.as_view(), {}, 'unit_view'),
    (r'^unit_classification_condition/(?P<pk>\d+)/delete/$', DeleteUnitClassificationConditionView.as_view(), {}, 'unit_classification_condition_delete'),
    (r'^unit_classification_type/(?P<pk>\d+)/delete/$', DeleteUnitClassificationTypeView.as_view(), {}, 'unit_classification_type_delete'),
    (r'^unit_classification_type/(?P<pk>\d+)/edit/$', UpdateUnitClassificationTypeView.as_view(), {}, 'unit_classification_type_edit'),
    (r'^unit_classification_type/new/$', CreateUnitClassificationTypeView.as_view(), {}, 'unit_classification_type_add'),
    (r'', IndexView.as_view(), {}, 'index'),
)
if settings.DEBUG:
    urlpatterns = [
                      url(r'^api_profile/full_recording_trial/$', FullRecordingTrialApiProfileView.as_view(), {}, 'full_recording_trial_api_profile'),
                      url(r'^api_profile/experiment/(?P<pk>\d+)/$', ExperimentApiProfileView.as_view(), {}, 'experiment_api_profile'),
                      url(r'^api_profile/condition/$', ConditionApiProfileView.as_view(), {}, 'condition_api_profile'),
                  ] + urlpatterns
