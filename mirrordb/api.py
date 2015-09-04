from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from mirrordb.models import Experiment, Unit, BrainRegion, RecordingTrial, Event, GraspObservationCondition, Species, GraspPerformanceCondition, Condition, UnitRecording, Nomenclature


class SpeciesResource(ModelResource):
    class Meta:
        queryset = Species.objects.all()
        resource_name = 'species'
        authorization= Authorization()


class BrainRegionResource(ModelResource):
    class Meta:
        queryset = BrainRegion.objects.all()
        resource_name = 'brain_region'
        authorization= Authorization()


class NomenclatureResource(ModelResource):
    species=fields.ManyToManyField(SpeciesResource, 'species')

    class Meta:
        queryset=Nomenclature.objects.all()
        resource_name='nomenclature'
        authorization=Authorization()


class ExperimentResource(ModelResource):
    class Meta:
        queryset = Experiment.objects.all()
        resource_name = 'experiment'
        authorization= Authorization()


class UnitResource(ModelResource):
    area = fields.ForeignKey(BrainRegionResource, 'area')

    class Meta:
        queryset = Unit.objects.all()
        resource_name = 'unit'
        authorization= Authorization()


class UnitRecordingResource(ModelResource):
    unit = fields.ForeignKey(UnitResource, 'unit', full=True)
    class Meta:
        queryset = UnitRecording.objects.all()
        resource_name = 'unit_recording'
        authorization= Authorization()


class EventResource(ModelResource):
    class Meta:
        queryset = Event.objects.all()
        resource_name = 'event'
        authorization= Authorization()


class RecordingTrialResource(ModelResource):
    unit_recordings= fields.ToManyField(UnitRecordingResource, 'unit_recordings', full=True, null=True)
    events=fields.ToManyField(EventResource, 'events', full=True, null=True)
    class Meta:
        queryset = RecordingTrial.objects.all()
        resource_name = 'recording_trial'
        authorization= Authorization()


class GraspObservationConditionResource(ModelResource):
    recording_trials=fields.ToManyField(RecordingTrialResource, 'recording_trials', full=True, null=True)
    class Meta:
        queryset = GraspObservationCondition.objects.all()
        resource_name = 'grasp_observation_condition'
        authorization= Authorization()


class GraspPerformanceConditionResource(ModelResource):
    class Meta:
        queryset = GraspPerformanceCondition.objects.all()
        resource_name = 'grasp_performance_condition'
        authorization= Authorization()


