import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uscbp.settings")
from sensorimotordb.models import Experiment, ClassificationAnalysis, ClassificationAnalysisSettings, ClassificationAnalysisResults


def test_analysis(experiment_id, analysis_id, analysis_settings_id):
    experiment=Experiment.objects.get(id=experiment_id)
    analysis=ClassificationAnalysis.objects.get(id=analysis_id)
    settings=ClassificationAnalysisSettings.objects.get(id=analysis_settings_id)
    results=ClassificationAnalysisResults(analysis = analysis, analysis_settings = settings, experiment = experiment, name='test', description='testing')
    analysis.run(results, settings)

if __name__=='__main__':
    django.setup()
    test_analysis(75,55,13)