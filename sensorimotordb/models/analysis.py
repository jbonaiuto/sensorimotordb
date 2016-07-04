from django.db import models
from model_utils.managers import InheritanceManager
import numpy as np
import os
from rpy2 import robjects
from sensorimotordb.models import UnitRecording, Condition, Unit, RecordingTrial, Event
from uscbp import settings
from rpy2.robjects import pandas2ri
pandas2ri.activate()
import pandas as pd


class Analysis(models.Model):
    experiment = models.ForeignKey('Experiment')

    objects = InheritanceManager()
    class Meta:
        app_label='sensorimotordb'


class AnalysisResults(models.Model):
    analysis = models.ForeignKey('Analysis')
    name=models.CharField(max_length=100, blank=False)
    description=models.TextField()
    date_run=models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label='sensorimotordb'


class UnitAnalysisResults(models.Model):
    analysis_results=models.ForeignKey('AnalysisResults', related_name='unit_analysis_results')
    unit=models.ForeignKey('Unit')
    results_text=models.TextField()

    class Meta:
        app_label='sensorimotordb'


class Factor(models.Model):
    analysis=models.ForeignKey('Analysis', related_name='factors')
    name=models.CharField(max_length=1000, blank=False)

    class Meta:
        app_label='sensorimotordb'


class Level(models.Model):
    factor=models.ForeignKey('Factor', related_name='levels')
    value=models.CharField(max_length=1000, blank=False)
    conditions=models.ManyToManyField(Condition)

    class Meta:
        app_label='sensorimotordb'


class VisuomotorClassificationAnalysisResults(AnalysisResults):
    total_num_units=models.IntegerField()

    class Meta:
        app_label='sensorimotordb'


class VisuomotorClassificationUnitAnalysisResults(UnitAnalysisResults):
    pairwise_results_text=models.TextField()

    class Meta:
        app_label='sensorimotordb'


class UnitClassification(models.Model):
    analysis_results=models.ForeignKey(VisuomotorClassificationAnalysisResults, related_name='unit_classifications')
    label=models.CharField(max_length=1000, blank=False)
    units=models.ManyToManyField(Unit)

    class Meta:
        app_label='sensorimotordb'


class VisuomotorClassificationAnalysis(Analysis):
    baseline_rel_evt=models.CharField(max_length=1000, blank=False)
    baseline_rel_start=models.IntegerField()
    baseline_rel_end=models.IntegerField()
    woi_rel_evt=models.CharField(max_length=1000, blank=False)
    woi_rel_start=models.IntegerField()
    woi_rel_end=models.IntegerField()

    class Meta:
        app_label='sensorimotordb'

    def run(self):
        unit_ids=np.unique(UnitRecording.objects.filter(trial__condition__experiment__id=self.experiment.id).values_list('unit',
            flat=True))

        results=VisuomotorClassificationAnalysisResults(analysis=self, total_num_units=len(unit_ids))
        results.save()

        unit_classifications={
            "motor":UnitClassification(analysis_results=results, label='motor'),
            "visual":UnitClassification(analysis_results=results, label='visual'),
            "visuomotor":UnitClassification(analysis_results=results, label='visuomotor'),
        }
        for label, classification in unit_classifications.iteritems():
            classification.save()

        for unit_id in unit_ids:
            (anova_results,objectgraspmodality_pairwise,modalityobjectgrasp_pairwise)=self.test_unit(results, unit_id)

            anova_results=pandas2ri.ri2py_dataframe(anova_results)
            objectgraspmodality_pairwise=pandas2ri.ri2py_dataframe(objectgraspmodality_pairwise)
            modalityobjectgrasp_pairwise=pandas2ri.ri2py_dataframe(modalityobjectgrasp_pairwise)
            print(anova_results)
            if anova_results['Pr(>F)']['modality']<0.05 and anova_results['Pr(>F)']['modality:objectgrasp']>=0.05:
                for row in modalityobjectgrasp_pairwise.iterrows():
                    if row[1]['p.value']<0.05 and row[1]['estimate']>0:
                        unit_classifications['motor'].units.add(Unit.objects.get(id=unit_id))
                        break
                    elif row[1]['p.value']<0.05 and row[1]['estimate']<0:
                        unit_classifications['visual'].units.add(Unit.objects.get(id=unit_id))
                        break
            else:
                unit_classifications['visuomotor'].units.add(Unit.objects.get(id=unit_id))

        print('%.4f %% motor cells' % (len(unit_classifications['motor'].units.count())/float(len(unit_ids))*100.0))
        print('%.4f %% visual cells' % (len(unit_classifications['visual'].units.count())/float(len(unit_ids))*100.0))
        print('%.4f %% visuomotor cells' % (len(unit_classifications['visuomotor'].units.count())/float(len(unit_ids))*100.0))


    def test_unit(self, results, unit_id):
        conditions=Condition.objects.filter(experiment__id=self.experiment.id)
        unit=Unit.objects.get(id=unit_id)
        trial_ids=[]
        modalities=[]
        objectgrasps=[]
        num_spikes_diff=[]
        for condition in conditions:
            recording_trials=RecordingTrial.objects.filter(condition=condition)
            for trial in recording_trials:

                if (self.baseline_rel_evt=='start' or Event.objects.filter(name=self.baseline_rel_evt,trial=trial).count()) and\
                   (self.woi_rel_evt=='start' or Event.objects.filter(name=self.woi_rel_evt,trial=trial).count()):
                    baseline_time_zero=float(trial.start_time)
                    if not self.baseline_rel_evt=='start':
                        baseline_evt=Event.objects.get(name=self.baseline_rel_evt,trial=trial)
                        baseline_time_zero=float(baseline_evt.time)
                    woi_time_zero=float(trial.start_time)
                    if not self.woi_rel_evt=='start':
                        woi_evt=Event.objects.get(name=self.woi_rel_evt, trial=trial)
                        woi_time_zero=float(woi_evt.time)
                    if UnitRecording.objects.filter(trial=trial, unit=unit).count():
                        unit_recording=UnitRecording.objects.get(trial=trial, unit=unit)
                        baseline_spikes=unit_recording.get_spikes(baseline_time_zero,[self.baseline_rel_start, self.baseline_rel_end])
                        woi_spikes=unit_recording.get_spikes(woi_time_zero, [self.woi_rel_start, self.woi_rel_end])

                        modality=Level.objects.get(factor__analysis=self,factor__name='modality',conditions=condition).value
                        objectgrasp=Level.objects.get(factor__analysis=self,factor__name='objectgrasp',conditions=condition).value

                        trial_ids.append(trial.id)
                        modalities.append(modality)
                        objectgrasps.append(objectgrasp)
                        num_spikes_diff.append(len(woi_spikes)-len(baseline_spikes))

        df= pd.DataFrame({
            'trial': pd.Series(trial_ids),
            'modality': pd.Series(modalities),
            'objectgrasp': pd.Series(objectgrasps),
            'num_spikes_diff': pd.Series(num_spikes_diff)
        })

        df=df.set_index(['trial'])

        r_source = robjects.r['source']
        r_source(os.path.join(settings.PROJECT_PATH,'../sensorimotordb/analysis/two_way_anova.R'))
        r_two_way_anova = robjects.globalenv['two_way_anova']
        (anova_results,objectgraspmodality_pairwise,modalityobjectgrasp_pairwise)=r_two_way_anova(df,"num_spikes_diff",
            "modality","objectgrasp")

        unit_results=VisuomotorClassificationUnitAnalysisResults(analysis_results=results, results_text=anova_results,
            pairwise_results_text='%s\n%s' % (str(modalityobjectgrasp_pairwise), str(objectgraspmodality_pairwise)),
            unit=unit)
        unit_results.save()

        return anova_results,objectgraspmodality_pairwise,modalityobjectgrasp_pairwise



