from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from tastypie import fields
from tastypie.authentication import SessionAuthentication, MultiAuthentication, ApiKeyAuthentication
from tastypie.cache import SimpleCache
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.http import HttpForbidden, HttpUnauthorized
from tastypie.resources import ModelResource
from tastypie.authorization import DjangoAuthorization
from tastypie.paginator import Paginator
from tastypie.utils import trailing_slash
from sensorimotordb.models import Experiment, Unit, BrainRegion, RecordingTrial, Event, GraspObservationCondition,\
    Species, GraspPerformanceCondition, Condition, UnitRecording, Nomenclature, AnalysisResults, UnitClassification,\
    Analysis, UnitAnalysisResults, FactorLevel, Factor, UnitClassificationType, ClassificationAnalysis, \
    ClassificationAnalysisResults, ClassificationAnalysisResultsLevelMapping, AnalysisSettings, \
    ClassificationAnalysisSettings, Penetration, TimeWindowFactorLevelSettings, Subject, ClusterAnalysisResults, \
    UnitClusterProjection, ClusterAnalysisSettings, TimeWindowConditionSettings, UnitCluster

from django.conf.urls import url
from haystack.query import SearchQuerySet, EmptySearchQuerySet

class SearchResourceMixin:
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/search/?$" % (self._meta.resource_name), self.wrap_view('get_search'), name="api_get_search"),
            ]

    def get_search(self, request, **kwargs):
        '''
        Custom endpoint for search
        '''

        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        query = request.GET.get('q', '')

        results = SearchQuerySet().models(self._meta.queryset.model).auto_query(query)
        if not results:
            results = EmptySearchQuerySet()

        paginator = Paginator(request.GET, results, resource_uri='/sensorimotordb/api/v1/%s/search/' % self._meta.resource_name)

        bundles = []
        for result in paginator.page()['objects']:
            bundle = self.build_bundle(obj=result.object, request=request)
            bundles.append(self.full_dehydrate(bundle))

        object_list = {
            'meta': paginator.page()['meta'],
            'objects': bundles
        }
        object_list['meta']['search_query'] = query

        self.log_throttled_access(request)
        return self.create_response(request, object_list)


class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        excludes = ['email','password','is_active','is_staff','is_superuser']
        authorization = DjangoAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/login%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('login'), name="api_login"),
            url(r'^(?P<resource_name>%s)/logout%s$' %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('logout'), name='api_logout'),
            ]

    def login(self, request, **kwargs):
        self.method_check(request, allowed=['post'])

        data = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))

        username = data.get('username', '')
        password = data.get('password', '')

        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return self.create_response(request, {
                    'success': True
                })
            else:
                return self.create_response(request, {
                    'success': False,
                    'reason': 'disabled',
                    }, HttpForbidden )
        else:
            return self.create_response(request, {
                'success': False,
                'reason': 'incorrect',
                }, HttpUnauthorized )

    def logout(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        if request.user and request.user.is_authenticated():
            logout(request)
            return self.create_response(request, { 'success': True })
        else:
            return self.create_response(request, { 'success': False }, HttpUnauthorized)


class SpeciesResource(ModelResource):
    class Meta:
        queryset = Species.objects.all()
        resource_name = 'species'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class BrainRegionResource(ModelResource):
    nomenclature=fields.ToOneField('sensorimotordb.api.NomenclatureResource','nomenclature', full=True)
    class Meta:
        queryset = BrainRegion.objects.all()
        resource_name = 'brain_region'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class NomenclatureResource(ModelResource):
    species=fields.ManyToManyField(SpeciesResource, 'species')

    class Meta:
        queryset=Nomenclature.objects.all().prefetch_related('species')
        resource_name='nomenclature'
        authorization=DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class SubjectResource(ModelResource):

    class Meta:
        queryset=Subject.objects.all()
        resource_name='subject'
        authorization=DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class ExperimentResource(SearchResourceMixin, ModelResource):
    collator=fields.ForeignKey(UserResource, 'collator', full=True)
    class Meta:
        queryset = Experiment.objects.all().select_related('collator')
        resource_name = 'experiment'
        authorization = DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class PenetrationResource(ModelResource):
    subject=fields.ForeignKey(SubjectResource, 'subject', full=True)
    class Meta:
        queryset=Penetration.objects.all().select_related('subject')
        resource_name = 'penetration'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class BasicUnitResource(SearchResourceMixin, ModelResource):
    penetration=fields=fields.ToOneField(PenetrationResource,'penetration',full=True)
    class Meta:
        queryset = Unit.objects.all().select_related('penetration')
        resource_name = 'unit'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class UnitResource(BasicUnitResource):
    area = fields.ToOneField(BrainRegionResource, 'area',full=True)
    penetration=fields=fields.ToOneField(PenetrationResource,'penetration',full=True, null=False)

    class Meta:
        queryset = Unit.objects.all().select_related('area','penetration')
        resource_name = 'unit'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class BasicConditionResource(SearchResourceMixin, ModelResource):

    class Meta:
        queryset = Condition.objects.all()
        resource_name = 'condition'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class ConditionResource(BasicConditionResource):
    experiment=fields.ToOneField(ExperimentResource, 'experiment', full=True)
    recording_trials=fields.ToManyField('sensorimotordb.api.RecordingTrialResource', 'recording_trials', null=False)
    class Meta:
        queryset = Condition.objects.all().select_related('experiment').prefetch_related('recording_trials').distinct()
        resource_name = 'condition'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        filtering={
            'recording_trials': ALL_WITH_RELATIONS,
            'experiment': ALL_WITH_RELATIONS
        }
        cache = SimpleCache(timeout=10)



class GraspPerformanceConditionResource(ConditionResource):
    class Meta:
        queryset = GraspPerformanceCondition.objects.all().select_related('experiment').prefetch_related('recording_trials')
        resource_name = 'grasp_performance_condition'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class GraspObservationConditionResource(ConditionResource):
    demonstrator_species=fields.ToOneField(SpeciesResource, 'demonstrator_species', full=True)
    class Meta:
        queryset = GraspObservationCondition.objects.all().select_related('experiment','demonstrator_species').prefetch_related('recording_trials')
        resource_name = 'grasp_observation_condition'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class BasicEventResource(ModelResource):
    class Meta:
        queryset = Event.objects.all()
        resource_name = 'basic_event'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)
        filtering={
            'trial': ALL_WITH_RELATIONS,
        }

class EventResource(ModelResource):
    trial=fields.ToOneField('sensorimotordb.api.BasicRecordingTrialResource', 'trial', full=True)
    class Meta:
        queryset = Event.objects.all().prefetch_related('trial__condition__experiment')
        resource_name = 'event'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)
        filtering={
            'trial': ALL_WITH_RELATIONS,
        }

class RecordingTrialResource(ModelResource):
    events=fields.ToManyField(BasicEventResource, 'events', full=True, null=True)
    #condition=fields.ToOneField(BasicConditionResource, 'condition')
    unit_recordings=fields.ToManyField('sensorimotordb.api.UnitRecordingResource', 'unit_recordings', null=False)
    class Meta:
        queryset = RecordingTrial.objects.all().select_related('condition').prefetch_related('unit_recordings').distinct()
        resource_name = 'recording_trial'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        filtering={
            'unit_recordings': ALL_WITH_RELATIONS,
            'condition': ALL_WITH_RELATIONS
        }
        cache = SimpleCache(timeout=10)

class BasicRecordingTrialResource(ModelResource):
    condition=fields.ToOneField(ConditionResource, 'condition')
    class Meta:
        queryset = RecordingTrial.objects.all().select_related('condition').prefetch_related('unit_recordings').distinct()
        resource_name = 'recording_trial'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        filtering={
            'condition': ALL_WITH_RELATIONS
        }
        cache = SimpleCache(timeout=10)


class UnitRecordingResource(ModelResource):
    unit = fields.ToOneField(BasicUnitResource, 'unit', null=False, full=True)
    #trial = fields.ToOneField(RecordingTrialResource, 'trial')
    class Meta:
        queryset = UnitRecording.objects.all().select_related('unit').distinct()#,'unit__area')#,'trial')
        resource_name = 'unit_recording'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        filtering={
            'unit': ALL_WITH_RELATIONS,
#            'trial': ALL_WITH_RELATIONS
        }
        cache = SimpleCache(timeout=10)

class FullRecordingTrialResource(ModelResource):
    events=fields.ToManyField(BasicEventResource, 'events', full=True, null=True)
    condition=fields.ToOneField(BasicConditionResource, 'condition')
    unit_recordings=fields.ToManyField('sensorimotordb.api.UnitRecordingResource', 'unit_recordings', null=False, full=True)
    class Meta:
        queryset = RecordingTrial.objects.all().select_related('condition').prefetch_related('unit_recordings__unit','events').distinct()
        resource_name = 'full_recording_trial'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        filtering={
            'unit_recordings': ALL_WITH_RELATIONS,
            'condition': ALL_WITH_RELATIONS
        }
        cache = SimpleCache(timeout=10)


class UnitClassificationTypeResource(ModelResource):
    parent=fields.ToOneField('sensorimotordb.api.UnitClassificationTypeResource', 'parent', null=True, full=False)
    children=fields.ToManyField('sensorimotordb.api.UnitClassificationTypeResource','children',null=True,full=True)
    analysis=fields.ToOneField('sensorimotordb.api.ClassificationAnalysisResource','analysis',null=False,full=False)
    conditions=fields.ToManyField('sensorimotordb.api.UnitClassificationConditionResource','unit_classification_type_conditions',null=True,full=True)
    class Meta:
        queryset=UnitClassificationType.objects.all()
        resource_name='unit_classification_type'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)
        filtering={
            'parent': ALL_WITH_RELATIONS,
            'analysis': ALL_WITH_RELATIONS,
        }


class UnitClassificationResource(ModelResource):
    units=fields.ManyToManyField(UnitResource, 'units', null=False, full=True)
    type=fields.ToOneField('sensorimotordb.api.UnitClassificationTypeResource', 'type', null=False, full=True)
    class Meta:
        queryset=UnitClassification.objects.all().prefetch_related('units')
        resource_name='unit_classification'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class FactorLevelResource(ModelResource):
    class Meta:
        queryset=FactorLevel.objects.all()
        resource_name='factor_level'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class FactorResource(ModelResource):
    levels=fields.ToManyField(FactorLevelResource, 'factor_levels', related_name='factor_levels',null=True,full=True)
    class Meta:
        queryset=Factor.objects.all().prefetch_related('factor_levels')
        resource_name='factor'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class AnalysisResource(ModelResource):
    class Meta:
        queryset=Analysis.objects.all().prefetch_related('factors')
        resource_name='analysis'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)

    def dehydrate(self, bundle):
        if ClassificationAnalysis.objects.filter(id=bundle.obj.id).count() and not isinstance(bundle.obj,ClassificationAnalysis):
            analysis_res = ClassificationAnalysisResource()
            analysis_bundle = analysis_res.build_bundle(obj=ClassificationAnalysis.objects.get(id=bundle.obj.id), request=bundle.request)
            bundle.data = analysis_res.full_dehydrate(analysis_bundle).data
        return bundle


class ClassificationAnalysisResource(ModelResource):
    analysis_factors=fields.ToManyField(FactorResource,'analysis_factors', related_name='analysis_factors',null=False,full=True)
    class Meta:
        queryset=ClassificationAnalysis.objects.all().prefetch_related('analysis_factors')
        resource_name='classification_analysis'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class ClassificationAnalysisResultsLevelMappingResource(ModelResource):
    level=fields.ToOneField(FactorLevelResource, 'level')
    conditions=fields.ToManyField(BasicConditionResource, 'conditions', related_name='conditions', full=True)
    class Meta:
        queryset=ClassificationAnalysisResultsLevelMapping.objects.all()
        resource_name='classification_analysis_results_level_mapping'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class TimeWindowFactorLevelSettingsResource(ModelResource):
    level=fields.ToOneField(FactorLevelResource, 'level')
    class Meta:
        queryset=TimeWindowFactorLevelSettings.objects.all()
        resource_name='time_window_factor_level_settings'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class AnalysisSettingsResource(ModelResource):
    class Meta:
        queryset=AnalysisSettings.objects.all()
        resource_name='analysis_settings'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)

    def dehydrate(self, bundle):
        if ClassificationAnalysisSettings.objects.filter(id=bundle.obj.id).count() and not isinstance(bundle.obj,ClassificationAnalysisSettings):
            results_res = ClassificationAnalysisSettingsResource()
            results_bundle = results_res.build_bundle(obj=ClassificationAnalysisSettings.objects.get(id=bundle.obj.id), request=bundle.request)
            bundle.data = results_res.full_dehydrate(results_bundle).data
        elif ClusterAnalysisSettings.objects.filter(id=bundle.obj.id).count() and not isinstance(bundle.obj,ClusterAnalysisSettings):
            results_res = ClusterAnalysisSettingsResource()
            results_bundle = results_res.build_bundle(obj=ClusterAnalysisSettings.objects.get(id=bundle.obj.id), request=bundle.request)
            bundle.data = results_res.full_dehydrate(results_bundle).data
        return bundle


class ClassificationAnalysisSettingsResource(AnalysisSettingsResource):
    level_mappings=fields.ToManyField(ClassificationAnalysisResultsLevelMappingResource, 'level_mappings', related_name='level_mappings', full=True)
    time_window_factor_level_settings = fields.ToManyField(TimeWindowFactorLevelSettingsResource, 'time_window_factor_level_settings', related_name='time_window_factor_level_settings', full=True)
    class Meta:
        queryset=ClassificationAnalysisSettings.objects.all()
        resource_name='classification_analysis_settings'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class TimeWindowConditionSettingsResource(ModelResource):
    condition=fields.ToOneField(BasicConditionResource, 'condition', full=True)
    class Meta:
        queryset=TimeWindowConditionSettings.objects.all()
        resource_name='time_window_condition_settings'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class ClusterAnalysisSettingsResource(AnalysisSettingsResource):
    time_window_condition_settings = fields.ToManyField(TimeWindowConditionSettingsResource, 'time_window_condition_settings', related_name='time_window_condition_settings', full=True)
    class Meta:
        queryset=ClusterAnalysisSettings.objects.all()
        resource_name='cluster_analysis_settings'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class AnalysisResultsResource(ModelResource):
    analysis=fields.ToOneField(AnalysisResource, 'analysis', null=False, full=True)
    experiment=fields.ToOneField(ExperimentResource, 'experiment')
    settings=fields.ToOneField(AnalysisSettingsResource, 'analysis_settings', null=False, full=True)
    class Meta:
        queryset=AnalysisResults.objects.all().select_related('analysis','experiment').prefetch_related('unit_analysis_results')
        resource_name='analysis_results'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)
        filtering={
            'analysis': ALL_WITH_RELATIONS,
            'experiment': ALL_WITH_RELATIONS,
            }

    def dehydrate(self, bundle):
        if ClassificationAnalysisResults.objects.filter(id=bundle.obj.id).count() and not isinstance(bundle.obj,ClassificationAnalysisResults):
            results_res = ClassificationAnalysisResultsResource()
            results_bundle = results_res.build_bundle(obj=ClassificationAnalysisResults.objects.get(id=bundle.obj.id), request=bundle.request)
            bundle.data = results_res.full_dehydrate(results_bundle).data
        elif ClusterAnalysisResults.objects.filter(id=bundle.obj.id).count() and not isinstance(bundle.obj,ClusterAnalysisResults):
            results_res = ClusterAnalysisResultsResource()
            results_bundle = results_res.build_bundle(obj=ClusterAnalysisResults.objects.get(id=bundle.obj.id), request=bundle.request)
            bundle.data = results_res.full_dehydrate(results_bundle).data
        return bundle


class ClassificationAnalysisResultsResource(AnalysisResultsResource):
    unit_analysis_results=fields.ToManyField('sensorimotordb.api.UnitAnalysisResultsResource', 'unit_analysis_results', related_name='unit_analysis_results',full=True)
    unit_classifications=fields.ToManyField(UnitClassificationResource,'unit_classifications', full=True)
    class Meta:
        queryset=ClassificationAnalysisResults.objects.all().select_related('analysis','experiment').prefetch_related('unit_analysis_results','unit_classifications')
        resource_name='classification_analysis_results'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        filtering={
            'analysis': ALL_WITH_RELATIONS,
            'experiment': ALL_WITH_RELATIONS,
        }
        cache = SimpleCache(timeout=10)


class UnitAnalysisResultsResource(ModelResource):
    unit=fields.ToOneField(UnitResource, 'unit', full=True)
    class Meta:
        queryset=UnitAnalysisResults.objects.all().select_related('unit')
        resource_name='unit_analysis_results'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache(timeout=10)


class ClusterAnalysisResultsResource(AnalysisResultsResource):
    unit_clusters=fields.ToManyField('sensorimotordb.api.UnitClusterResource', 'unit_clusters', related_name='unit_clusters',full=True)
    class Meta:
        queryset=ClusterAnalysisResults.objects.all().select_related('analysis','experiment').prefetch_related('unit_clusters')
        resource_name='cluster_analysis_results'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        filtering={
            'analysis': ALL_WITH_RELATIONS,
            'experiment': ALL_WITH_RELATIONS,
            }
        cache = SimpleCache(timeout=10)


class UnitClusterResource(ModelResource):
    units=fields.ToManyField(UnitResource, 'units', full=True)
    cluster_projection=fields.ToManyField('sensorimotordb.api.UnitClusterProjectionResource', 'cluster_projections', full=True)
    class Meta:
        queryset=UnitCluster.objects.all().prefetch_related('units')
        resource_name='unit_cluster'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        filtering={
            'analysis': ALL_WITH_RELATIONS,
            'experiment': ALL_WITH_RELATIONS,
            }
        cache = SimpleCache(timeout=10)


class UnitClusterProjectionResource(ModelResource):
    unit=fields.ToOneField(UnitResource, 'unit')
    class Meta:
        queryset=UnitClusterProjection.objects.all().select_related('unit')
        resource_name='unit_cluster_projection'
        authorization= DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        filtering={
            'analysis': ALL_WITH_RELATIONS,
            'experiment': ALL_WITH_RELATIONS,
            }
        cache = SimpleCache(timeout=10)