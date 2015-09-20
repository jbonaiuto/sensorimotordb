from haystack import indexes
from mirrordb.models import Experiment, Unit, BrainRegion, RecordingTrial, Event, GraspObservationCondition, Species, GraspPerformanceCondition, Condition, UnitRecording, Nomenclature

class GraspObservationConditionIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    demonstrator_species = indexes.CharField(model_attr='demonstrator_species__species_name')
    demonstration_type = indexes.CharField(model_attr='demonstration_type')
    viewing_angle = indexes.DecimalField(model_attr='viewing_angle')
    whole_body_visible = indexes.BooleanField(model_attr='whole_body_visible')
    object=indexes.CharField(model_attr='object')
    object_distance=indexes.DecimalField(model_attr='object_distance')
    grasp=indexes.CharField(model_attr='grasp')
#    experiment_title=indexes.CharField(model_attr='experiment__title')
#    experiment_brief_description=indexes.CharField(model_attr='experiment__brief_description')
#    collator_last_name=indexes.CharField(model_attr='experiment__collator__last_name')
#    collator_first_name=indexes.CharField(model_attr='experiment__collator__first_name')
#    collator_username=indexes.CharField(model_attr='experiment__collator__username')

    def get_model(self):
        return GraspObservationCondition
        
    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()

class GraspPerformanceConditionIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    hand_visible = indexes.BooleanField(model_attr='hand_visible')
    object_visible = indexes.BooleanField(model_attr='object_visible')
    object=indexes.CharField(model_attr='object')
    object_distance=indexes.DecimalField(model_attr='object_distance')
    grasp=indexes.CharField(model_attr='grasp')
#    experiment_title=indexes.CharField(model_attr='experiment__title')
#    experiment_brief_description=indexes.CharField(model_attr='experiment__brief_description')
#    collator_last_name=indexes.CharField(model_attr='experiment__collator__last_name')
#    collator_first_name=indexes.CharField(model_attr='experiment__collator__first_name')
#    collator_username=indexes.CharField(model_attr='experiment__collator__username')

    def get_model(self):
        return GraspPerformanceCondition

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()


class ConditionIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
#    experiment_title=indexes.CharField(model_attr='experiment__title')
#    experiment_brief_description=indexes.CharField(model_attr='experiment__brief_description')
#    collator_last_name=indexes.CharField(model_attr='experiment__collator__last_name')
#    collator_first_name=indexes.CharField(model_attr='experiment__collator__first_name')
#    collator_username=indexes.CharField(model_attr='experiment__collator__username')

    def get_model(self):
        return Condition

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()


class ExperimentIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title=indexes.CharField(model_attr='title')
    brief_description=indexes.CharField(model_attr='brief_description')
#    collator_last_name=indexes.CharField(model_attr='collator__last_name')
#    collator_first_name=indexes.CharField(model_attr='collator__first_name')
#    collator_username=indexes.CharField(model_attr='collator__username')

    def get_model(self):
        return Experiment

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()


class UnitIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    type=indexes.CharField(model_attr='type')

    def get_model(self):
        return Unit

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()