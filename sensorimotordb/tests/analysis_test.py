import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uscbp.settings")
from sensorimotordb.models import Experiment, ClassificationAnalysis, ClassificationAnalysisSettings, ClassificationAnalysisResults, ClusterAnalysis, ClusterAnalysisSettings, ClusterAnalysisResults


def test_classification_analysis(experiment_id, analysis_id, analysis_settings_id):
    experiment=Experiment.objects.get(id=experiment_id)
    analysis=ClassificationAnalysis.objects.get(id=analysis_id)
    settings=ClassificationAnalysisSettings.objects.get(id=analysis_settings_id)
    results=ClassificationAnalysisResults(analysis = analysis, analysis_settings = settings, experiment = experiment,
        name='test', description='testing')
    analysis.run(results, settings)

def test_cluster_analysis(experiment_id, analysis_id, analysis_settings_id):
    experiment=Experiment.objects.get(id=experiment_id)
    analysis=ClusterAnalysis.objects.get(id=analysis_id)
    settings=ClusterAnalysisSettings.objects.get(id=analysis_settings_id)
    results=ClusterAnalysisResults(analysis = analysis, analysis_settings = settings, experiment = experiment,
        name='test', description='testing')
    analysis.run(results, settings)

if __name__=='__main__':
    django.setup()
    #test_classification_analysis(120,69,32)
    test_cluster_analysis(125,70,44)