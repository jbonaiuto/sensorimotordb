from django.contrib.auth.models import User
from tastypie import fields
from tastypie.authentication import SessionAuthentication
from tastypie.cache import SimpleCache
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.resources import ModelResource
from tastypie.authorization import DjangoAuthorization
from tastypie.paginator import Paginator
from sensorimotordb.models import Experiment, Unit, BrainRegion, RecordingTrial, Event, GraspObservationCondition, Species, GraspPerformanceCondition, Condition, UnitRecording, Nomenclature

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
        authorization = DjangoAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)


class SpeciesResource(ModelResource):
    class Meta:
        queryset = Species.objects.all()
        resource_name = 'species'
        authorization= DjangoAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)


class BrainRegionResource(ModelResource):
    class Meta:
        queryset = BrainRegion.objects.all()
        resource_name = 'brain_region'
        authorization= DjangoAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)


class NomenclatureResource(ModelResource):
    species=fields.ManyToManyField(SpeciesResource, 'species')

    class Meta:
        queryset=Nomenclature.objects.all().prefetch_related('species')
        resource_name='nomenclature'
        authorization=DjangoAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)


class ExperimentResource(SearchResourceMixin, ModelResource):
    collator=fields.ForeignKey(UserResource, 'collator', full=True)
    class Meta:
        queryset = Experiment.objects.all().prefetch_related('collator')
        resource_name = 'experiment'
        authorization = DjangoAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)


class UnitResource(SearchResourceMixin, ModelResource):
    area = fields.ForeignKey(BrainRegionResource, 'area',full=True)

    class Meta:
        queryset = Unit.objects.all().prefetch_related('area')
        resource_name = 'unit'
        authorization= DjangoAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)


class ConditionResource(SearchResourceMixin, ModelResource):
    experiment=fields.ForeignKey(ExperimentResource, 'experiment', full=True)
    recording_trials=fields.ToManyField('sensorimotordb.api.RecordingTrialResource', 'recording_trials', null=False)
    class Meta:
        queryset = Condition.objects.all().prefetch_related('experiment','recording_trials')
        resource_name = 'condition'
        authorization= DjangoAuthorization()
        authentication = SessionAuthentication()
        filtering={
            'recording_trials': ALL_WITH_RELATIONS,
            'experiment': ALL_WITH_RELATIONS
        }
        cache = SimpleCache(timeout=10)


class GraspPerformanceConditionResource(ConditionResource):
    class Meta:
        queryset = GraspPerformanceCondition.objects.all().prefetch_related('experiment','recording_trials')
        resource_name = 'grasp_performance_condition'
        authorization= DjangoAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)


class GraspObservationConditionResource(ConditionResource):
    demonstrator_species=fields.ForeignKey(SpeciesResource, 'demonstrator_species', full=True)
    class Meta:
        queryset = GraspObservationCondition.objects.all().prefetch_related('experiment','recording_trials','demonstrator_species')
        resource_name = 'grasp_observation_condition'
        authorization= DjangoAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)


class EventResource(ModelResource):
    class Meta:
        queryset = Event.objects.all()
        resource_name = 'event'
        authorization= DjangoAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)


class RecordingTrialResource(ModelResource):
    events=fields.ToManyField(EventResource, 'events', full=True, null=True)
    condition=fields.ForeignKey(ConditionResource, 'condition')
    unit_recordings=fields.ToManyField('sensorimotordb.api.UnitRecordingResource', 'unit_recordings', null=False)
    class Meta:
        queryset = RecordingTrial.objects.all().prefetch_related('events','condition','unit_recordings')
        resource_name = 'recording_trial'
        authorization= DjangoAuthorization()
        authentication = SessionAuthentication()
        filtering={
            'unit_recordings': ALL_WITH_RELATIONS,
            'condition': ALL_WITH_RELATIONS
        }
        cache = SimpleCache(timeout=10)


class UnitRecordingResource(ModelResource):
    unit = fields.ForeignKey(UnitResource, 'unit', full=True, null=False)
    trial = fields.ForeignKey(RecordingTrialResource, 'trial')
    class Meta:
        queryset = UnitRecording.objects.all().prefetch_related('unit','trial')
        resource_name = 'unit_recording'
        authorization= DjangoAuthorization()
        authentication = SessionAuthentication()
        filtering={
            'unit': ALL_WITH_RELATIONS,
            'trial': ALL_WITH_RELATIONS
        }
        cache = SimpleCache(timeout=10)

class FullRecordingTrialResource(ModelResource):
    events=fields.ToManyField(EventResource, 'events', full=True, null=True)
    condition=fields.ForeignKey(ConditionResource, 'condition')
    unit_recordings=fields.ToManyField('sensorimotordb.api.UnitRecordingResource', 'unit_recordings', null=False, full=True)
    class Meta:
        queryset = RecordingTrial.objects.all().prefetch_related('events','condition','unit_recordings')
        resource_name = 'full_recording_trial'
        authorization= DjangoAuthorization()
        authentication = SessionAuthentication()
        filtering={
            'unit_recordings': ALL_WITH_RELATIONS,
            'condition': ALL_WITH_RELATIONS
        }
        cache = SimpleCache(timeout=10)