import django
import os
from sensorimotordb.models import VisuomotorClassificationAnalysis, VisuomotorClassificationAnalysisResults, UnitClassification, VisuomotorClassificationUnitAnalysisResults, Experiment, AnalysisResultsLevelMapping, Level, Condition

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uscbp.settings")

def reset_results(analysis_id):
    for result in VisuomotorClassificationAnalysisResults.objects.filter(analysis__id=analysis_id):
        for classification in UnitClassification.objects.filter(analysis_results=result):
            classification.delete()
        for unit_results in VisuomotorClassificationUnitAnalysisResults.objects.filter(analysis_results=result):
            unit_results.delete()
        for level_mapping in AnalysisResultsLevelMapping.objects.filter(analysis_results=result):
            level_mapping.delete()
        result.delete()

def test_analysis(analysis_id, reset=False):

    if reset:
        reset_results(analysis_id)
    analysis=VisuomotorClassificationAnalysis.objects.get(id=analysis_id)
    experiment=Experiment.objects.get(id=75)
    results=VisuomotorClassificationAnalysisResults(name="Mirror classification",
        description="Classification of cells into motor, visual and visuomotor", analysis=analysis,
        experiment=experiment)
    results.baseline_rel_evt="lon"
    results.baseline_rel_start=-500
    results.baseline_rel_end=0
    results.obj_view_woi_rel_evt="lon"
    results.obj_view_woi_rel_start=50
    results.obj_view_woi_rel_end=450
    results.grasp_woi_rel_evt="do"
    results.grasp_woi_rel_start=-500
    results.grasp_woi_rel_end=0
    results.save()

    level_mapping=AnalysisResultsLevelMapping(analysis_results=results, level=Level.objects.get(id=1))
    level_mapping.save()
    for cond_id in [432,433,437,438,442,443,430,435,440]:
        level_mapping.conditions.add(Condition.objects.get(id=cond_id))

    level_mapping=AnalysisResultsLevelMapping(analysis_results=results, level=Level.objects.get(id=2))
    level_mapping.save()
    for cond_id in [434,439,444,431,436,441]:
        level_mapping.conditions.add(Condition.objects.get(id=cond_id))

    level_mapping=AnalysisResultsLevelMapping(analysis_results=results, level=Level.objects.get(id=3))
    level_mapping.save()
    for cond_id in [432,433,434,430,431]:
        level_mapping.conditions.add(Condition.objects.get(id=cond_id))

    level_mapping=AnalysisResultsLevelMapping(analysis_results=results, level=Level.objects.get(id=4))
    level_mapping.save()
    for cond_id in [437,438,439,435,436]:
        level_mapping.conditions.add(Condition.objects.get(id=cond_id))

    level_mapping=AnalysisResultsLevelMapping(analysis_results=results, level=Level.objects.get(id=5))
    level_mapping.save()
    for cond_id in [442,443,444,440,441]:
        level_mapping.conditions.add(Condition.objects.get(id=cond_id))

    level_mapping=AnalysisResultsLevelMapping(analysis_results=results, level=Level.objects.get(id=8))
    level_mapping.save()
    for cond_id in [432,433]:
        level_mapping.conditions.add(Condition.objects.get(id=cond_id))

    level_mapping=AnalysisResultsLevelMapping(analysis_results=results, level=Level.objects.get(id=9))
    level_mapping.save()
    for cond_id in [437,438]:
        level_mapping.conditions.add(Condition.objects.get(id=cond_id))

    level_mapping=AnalysisResultsLevelMapping(analysis_results=results, level=Level.objects.get(id=10))
    level_mapping.save()
    for cond_id in [442,443]:
        level_mapping.conditions.add(Condition.objects.get(id=cond_id))

    level_mapping=AnalysisResultsLevelMapping(analysis_results=results, level=Level.objects.get(id=11))
    level_mapping.save()
    for cond_id in [432,437,442]:
        level_mapping.conditions.add(Condition.objects.get(id=cond_id))

    level_mapping=AnalysisResultsLevelMapping(analysis_results=results, level=Level.objects.get(id=12))
    level_mapping.save()
    for cond_id in [433,438,443]:
        level_mapping.conditions.add(Condition.objects.get(id=cond_id))

    level_mapping=AnalysisResultsLevelMapping(analysis_results=results, level=Level.objects.get(id=13))
    level_mapping.save()
    for cond_id in [430]:
        level_mapping.conditions.add(Condition.objects.get(id=cond_id))

    level_mapping=AnalysisResultsLevelMapping(analysis_results=results, level=Level.objects.get(id=14))
    level_mapping.save()
    for cond_id in [435]:
        level_mapping.conditions.add(Condition.objects.get(id=cond_id))

    level_mapping=AnalysisResultsLevelMapping(analysis_results=results, level=Level.objects.get(id=15))
    level_mapping.save()
    for cond_id in [440]:
        level_mapping.conditions.add(Condition.objects.get(id=cond_id))

    analysis.run(results)

if __name__=='__main__':
    django.setup()
    test_analysis(1, reset=True)