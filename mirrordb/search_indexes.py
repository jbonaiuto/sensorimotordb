from haystack import indexes
from mirrordb.models import Experiment, Unit, BrainRegion, RecordingTrial, Event, GraspObservationCondition, Species, GraspPerformanceCondition, Condition, UnitRecording, Nomenclature

class GraspObservationConditionIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True)
    #demonstrator_species = indexes.CharField(model_attr='species')
    demonstration_type = indexes.CharField(model_attr='demonstration_type')
    #viewing_angle = indexes.DecimalField(model_attr='viewing_angle')
    #whole_body_visible = indexes.BooleanField(model_attr='whole_body_visible')

    def get_model(self):
        return GraspObservationCondition
        
    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
