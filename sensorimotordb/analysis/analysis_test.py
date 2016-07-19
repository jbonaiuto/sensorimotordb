import django
import os
from sensorimotordb.models import VisuomotorClassificationAnalysis, VisuomotorClassificationAnalysisResults, UnitClassification, VisuomotorClassificationUnitAnalysisResults

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uscbp.settings")

def reset_results(analysis_id):
    for result in VisuomotorClassificationAnalysisResults.objects.filter(analysis__id=analysis_id):
        for classification in UnitClassification.objects.filter(analysis_results=result):
            classification.delete()
        for unit_results in VisuomotorClassificationUnitAnalysisResults.objects.filter(analysis_results=result):
            unit_results.delete()
        result.delete()

def test_analysis(analysis_id, reset=False):

    if reset:
        reset_results(analysis_id)
    analysis=VisuomotorClassificationAnalysis.objects.get(id=analysis_id)
    analysis.run("Mirror classification", "Classification of cells into motor, visual and visuomotor")

if __name__=='__main__':
    django.setup()
    test_analysis(1, reset=True)