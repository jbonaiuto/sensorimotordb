from django.db import models
from model_utils.managers import InheritanceManager
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
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


class UnitClassification(MPTTModel,models.Model):
    # parent BOP
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    analysis_results=models.ForeignKey(VisuomotorClassificationAnalysisResults, related_name='unit_classifications')
    label=models.CharField(max_length=1000, blank=False)
    units=models.ManyToManyField(Unit)

    class Meta:
        app_label='sensorimotordb'


class VisuomotorClassificationAnalysis(Analysis):
    baseline_rel_evt=models.CharField(max_length=1000, blank=False)
    baseline_rel_start=models.IntegerField()
    baseline_rel_end=models.IntegerField()
    obj_view_woi_rel_evt=models.CharField(max_length=1000, blank=False)
    obj_view_woi_rel_start=models.IntegerField()
    obj_view_woi_rel_end=models.IntegerField()
    grasp_woi_rel_evt=models.CharField(max_length=1000, blank=False)
    grasp_woi_rel_start=models.IntegerField()
    grasp_woi_rel_end=models.IntegerField()

    class Meta:
        app_label='sensorimotordb'

    def get_objectgrasp_pref(self, objectgrasp_pairwise):
        pref='nonselective'
        if(isinstance(objectgrasp_pairwise, pd.DataFrame)):
            largeconewhole_ringhook = objectgrasp_pairwise['estimate'][1]
            largeconewhole_ringhook_p = objectgrasp_pairwise['p.value'][1]
            largeconewhole_smallconeside = objectgrasp_pairwise['estimate'][2]
            largeconewhole_smallconeside_p = objectgrasp_pairwise['p.value'][2]
            ringhook_smallconeside = objectgrasp_pairwise['estimate'][3]
            ringhook_smallconeside_p = objectgrasp_pairwise['p.value'][3]
        else:
            grasp_pairwise = str(objectgrasp_pairwise[1]).split('\n')
            line = grasp_pairwise[1].split()
            largeconewhole_ringhook = float(line[3])
            if(line[7][0] == '<'):
                largeconewhole_ringhook_p = float(line[7][1:]) / 2
            else:
                largeconewhole_ringhook_p = float(line[7]) / 2
            line = grasp_pairwise[2].split()
            largeconewhole_smallconeside = float(line[3])
            if(line[7][0] == '<'):
                largeconewhole_smallconeside_p = float(line[7][1:]) / 2
            else:
                largeconewhole_smallconeside_p = float(line[7]) / 2
            line = grasp_pairwise[3].split()
            ringhook_smallconeside = float(line[3])
            if(line[7][0] == '<'):
                ringhook_smallconeside_p = float(line[7][1:]) / 2
            else:
                ringhook_smallconeside_p = float(line[7]) / 2
        if largeconewhole_ringhook_p >= 0.05 and largeconewhole_smallconeside_p >= 0.05 and ringhook_smallconeside_p >= 0.05:
            pref = 'nonselective'
            print('should not get here!')
        elif largeconewhole_ringhook_p < 0.05 and largeconewhole_smallconeside_p >= 0.05 and ringhook_smallconeside_p >= 0.05:
            print('should not get here!')
        elif largeconewhole_ringhook_p >= 0.05 and largeconewhole_smallconeside_p < 0.05 and ringhook_smallconeside_p >= 0.05:
            print('should not get here!')
        elif largeconewhole_ringhook_p < 0.05 and largeconewhole_smallconeside_p < 0.05 and ringhook_smallconeside_p >= 0.05:
            if largeconewhole_ringhook < 0 and largeconewhole_smallconeside < 0:
                pref = 'ringhook_smallconeside'
            elif largeconewhole_ringhook > 0 and largeconewhole_smallconeside > 0:
                pref = 'largeconewhole'
            else:
                print('should not get here!')
        elif largeconewhole_ringhook_p >= 0.05 and largeconewhole_smallconeside_p >= 0.05 and ringhook_smallconeside_p < 0.05:
            print('should not get here!')
        elif largeconewhole_ringhook_p < 0.05 and largeconewhole_smallconeside_p >= 0.05 and ringhook_smallconeside_p < 0.05:
            if largeconewhole_ringhook > 0 and ringhook_smallconeside < 0:
                pref = 'smallconeside_largeconewhole'
            elif largeconewhole_ringhook < 0 and ringhook_smallconeside > 0:
                pref = 'ringhook'
            else:
                print('should not get here!')
        elif largeconewhole_ringhook_p >= 0.05 and largeconewhole_smallconeside_p < 0.05 and ringhook_smallconeside_p < 0.05:
            if largeconewhole_smallconeside > 0 and ringhook_smallconeside > 0:
                pref = 'ringhook_largeconewhole'
            elif largeconewhole_smallconeside < 0 and ringhook_smallconeside < 0:
                pref = 'smallconeside'
            else:
                print('should not get here!')
        elif largeconewhole_ringhook_p < 0.05 and largeconewhole_smallconeside_p < 0.05 and ringhook_smallconeside_p < 0.05:
            # S L R
            if largeconewhole_ringhook < 0 and largeconewhole_smallconeside > 0 and ringhook_smallconeside > 0:
                pref = 'ringhook'
            # S R L
            elif largeconewhole_ringhook > 0 and largeconewhole_smallconeside > 0 and ringhook_smallconeside > 0:
                pref = 'largeconewhole'
            # L S R
            elif largeconewhole_ringhook < 0 and largeconewhole_smallconeside < 0 and ringhook_smallconeside > 0:
                pref = 'ringhook'
            # L R S
            elif largeconewhole_ringhook < 0 and largeconewhole_smallconeside < 0 and ringhook_smallconeside < 0:
                pref = 'smallconeside'
            # R S L
            elif largeconewhole_ringhook > 0 and largeconewhole_smallconeside > 0 and ringhook_smallconeside < 0:
                pref = 'largeconewhole'
            # R L S
            elif largeconewhole_ringhook > 0 and largeconewhole_smallconeside < 0 and ringhook_smallconeside < 0:
                pref = 'smallconeside'
            else:
                print('should not get here!')
        return pref

    def run(self, res_name, res_description):
        unit_ids=np.unique(UnitRecording.objects.filter(trial__condition__experiment__id=self.experiment.id).values_list('unit',
            flat=True))

        results=VisuomotorClassificationAnalysisResults(name=res_name, description=res_description, analysis=self,
            total_num_units=len(unit_ids))
        results.save()

        unit_classifications={
            "motor":UnitClassification(analysis_results=results, label='motor'),
            "visual":UnitClassification(analysis_results=results, label='visual'),
            "visuomotor":UnitClassification(analysis_results=results, label='visuomotor'),
            "other":UnitClassification(analysis_results=results, label='other')
        }
        for label, classification in unit_classifications.iteritems():
            classification.save()
        unit_classifications['canonical']=UnitClassification(parent=unit_classifications['visuomotor'],analysis_results=results,label='canonical')
        unit_classifications['canonical'].save()
        unit_classifications['mirror']=UnitClassification(parent=unit_classifications['visuomotor'],analysis_results=results,label='mirror')
        unit_classifications['mirror'].save()
        unit_classifications['canonical mirror']=UnitClassification(parent=unit_classifications['visuomotor'],analysis_results=results,label='canonical mirror')
        unit_classifications['canonical mirror'].save()

        unit_classifications['motor - ringhook']=UnitClassification(parent=unit_classifications['motor'],analysis_results=results,label='ringhook selective')
        unit_classifications['motor - ringhook'].save()
        unit_classifications['motor - smallconeside']=UnitClassification(parent=unit_classifications['motor'],analysis_results=results,label='smallconeside selective')
        unit_classifications['motor - smallconeside'].save()
        unit_classifications['motor - largeconewhole']=UnitClassification(parent=unit_classifications['motor'],analysis_results=results,label='largeconewhole selective')
        unit_classifications['motor - largeconewhole'].save()
        unit_classifications['motor - ringhook_smallconeside']=UnitClassification(parent=unit_classifications['motor'],analysis_results=results,label='ringhook_smallconeside selective')
        unit_classifications['motor - ringhook_smallconeside'].save()
        unit_classifications['motor - ringhook_largeconewhole']=UnitClassification(parent=unit_classifications['motor'],analysis_results=results,label='ringhook_largeconewhole selective')
        unit_classifications['motor - ringhook_largeconewhole'].save()
        unit_classifications['motor - smallconeside_largeconewhole']=UnitClassification(parent=unit_classifications['motor'],analysis_results=results,label='smallconeside_largeconewhole selective')
        unit_classifications['motor - smallconeside_largeconewhole'].save()
        unit_classifications['motor - nonselective']=UnitClassification(parent=unit_classifications['motor'],analysis_results=results,label='nonselective')
        unit_classifications['motor - nonselective'].save()

        for unit_id in unit_ids:
            unit=Unit.objects.get(id=unit_id)
            (motor_anova_results,motor_visibility_pairwise,motor_objectgrasp_pairwise,motor_visibilityobjectgrasp_pairwise,
                motor_objectgraspvisibility_pairwise)=self.test_unit_motor(results, unit)
            (objpres_anova_results,objpres_trialtype_pairwise,objpres_objectgrasp_pairwise,
                objpres_trialtypeobjectgrasp_pairwise,objpres_objectgrasptrialtype_pairwise)=self.test_unit_obj_pres(results, unit)
            (obs_grasp_anova_results,obs_grasp_objectgrasp_pairwise)=self.test_unit_obs_grasp(results, unit)

            unit_results=VisuomotorClassificationUnitAnalysisResults(analysis_results=results,
                results_text='\n'.join(['<h2>Motor</h2>',str(motor_anova_results),
                                        '<h2>Object Presentation</h2>',str(objpres_anova_results),
                                        '<h2>Observation - Object Grasp</h2>',str(obs_grasp_anova_results)]),
                pairwise_results_text='\n'.join(['<h2>Motor</h2>',
                                                 str(motor_visibility_pairwise),
                                                 str(motor_objectgrasp_pairwise),
                                                 str(motor_visibilityobjectgrasp_pairwise),
                                                 str(motor_objectgraspvisibility_pairwise),
                                                 '<h2>Object Presentation</h2>',
                                                 str(objpres_trialtype_pairwise),
                                                 str(objpres_objectgrasp_pairwise),
                                                 str(objpres_trialtypeobjectgrasp_pairwise),
                                                 str(objpres_objectgrasptrialtype_pairwise),
                                                 '<h2>Observation - Object Grasp</h2>',
                                                 str(obs_grasp_objectgrasp_pairwise)]),
                unit=unit)
            unit_results.save()


            motor_properties=False
            motor_pref='nonselective'
            if motor_anova_results['Pr(>F)']['visibility']>=0.05 and motor_anova_results['Pr(>F)']['visibility:objectgrasp']>=0.05 and motor_anova_results['Pr(>F)']['objectgrasp']<0.05:
                motor_properties=True
                motor_pref = self.get_objectgrasp_pref(motor_objectgrasp_pairwise)

            obj_pres=False
            obj_pref='nonselective'
            if objpres_anova_results['Pr(>F)']['trial_type']>=0.05 and objpres_anova_results['Pr(>F)']['trial_type:objectgrasp']>=0.05 and objpres_anova_results['Pr(>F)']['objectgrasp']<0.05:
                obj_pres=True
                obj_pref=self.get_objectgrasp_pref(objpres_objectgrasp_pairwise)

            action_obs=False
            obs_pref='nonselective'
            if obs_grasp_anova_results['Pr(>F)']['objectgrasp']<0.05:
                action_obs=True
                obs_pref=self.get_objectgrasp_pref(obs_grasp_objectgrasp_pairwise)

            if motor_properties and (obj_pres or action_obs):
                unit_classifications['visuomotor'].units.add(Unit.objects.get(id=unit_id))
                if obj_pres and action_obs:
                    unit_classifications['canonical mirror'].units.add(Unit.objects.get(id=unit_id))
                elif obj_pres:
                    unit_classifications['canonical'].units.add(Unit.objects.get(id=unit_id))
                else:
                    unit_classifications['mirror'].units.add(Unit.objects.get(id=unit_id))

            elif motor_properties:
                unit_classifications['motor'].units.add(Unit.objects.get(id=unit_id))
                unit_classifications['motor - %s' % motor_pref].units.add(Unit.objects.get(id=unit_id))
            elif (obj_pres or action_obs):
                unit_classifications['visual'].units.add(Unit.objects.get(id=unit_id))
            else:
                unit_classifications['other'].units.add(Unit.objects.get(id=unit_id))

        print('%.4f %% motor cells' % (unit_classifications['motor'].units.count()/float(len(unit_ids))*100.0))
        print('%.4f %% visual cells' % (unit_classifications['visual'].units.count()/float(len(unit_ids))*100.0))
        print('%.4f %% visuomotor cells' % (unit_classifications['visuomotor'].units.count()/float(len(unit_ids))*100.0))
        print('%.4f %% other cells' % (unit_classifications['other'].units.count()/float(len(unit_ids))*100.0))


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



    def test_unit_motor(self, results, unit):
        trial_ids=[]
        visibilities=[]
        objectgrasps=[]
        num_spikes_diff=[]
        condition_ids=[]
        for factor_name in ['Grasp Execution: Visibility','Grasp Execution: Object/Grasp']:
            factor=Factor.objects.get(analysis=results.analysis, name=factor_name)
            for level in factor.levels.all():
                for condition in level.conditions.all():
                    if not condition.id in condition_ids:
                        condition_ids.append(condition.id)
        conditions=Condition.objects.filter(id__in=condition_ids)
        for condition in conditions:
            recording_trials=RecordingTrial.objects.filter(condition=condition)
            for trial in recording_trials:

                baseline_time_zero=float(trial.start_time)
                if not self.baseline_rel_evt=='start':
                    baseline_evt=Event.objects.get(name=self.baseline_rel_evt,trial=trial)
                    baseline_time_zero=float(baseline_evt.time)
                woi_time_zero=float(trial.start_time)
                if not self.grasp_woi_rel_evt=='start':
                    woi_evt=Event.objects.get(name=self.grasp_woi_rel_evt, trial=trial)
                    woi_time_zero=float(woi_evt.time)
                if UnitRecording.objects.filter(trial=trial, unit=unit).count():
                    unit_recording=UnitRecording.objects.get(trial=trial, unit=unit)
                    baseline_spikes=unit_recording.get_spikes(baseline_time_zero,[self.baseline_rel_start/1000.0,
                                                                                  self.baseline_rel_end/1000.0])
                    woi_spikes=unit_recording.get_spikes(woi_time_zero, [self.grasp_woi_rel_start/1000.0,
                                                                         self.grasp_woi_rel_end/1000.0])

                    visibility=Level.objects.get(factor__analysis=self,factor__name='Grasp Execution: Visibility',conditions=condition).value
                    objectgrasp=Level.objects.get(factor__analysis=self,factor__name='Grasp Execution: Object/Grasp',conditions=condition).value

                    trial_ids.append(trial.id)
                    visibilities.append(visibility)
                    objectgrasps.append(objectgrasp)
                    num_spikes_diff.append(len(woi_spikes)-len(baseline_spikes))

        df= pd.DataFrame({
            'trial': pd.Series(trial_ids),
            'visibility': pd.Series(visibilities),
            'objectgrasp': pd.Series(objectgrasps),
            'num_spikes_diff': pd.Series(num_spikes_diff)
        })

        df=df.set_index(['trial'])

        r_source = robjects.r['source']
        r_source(os.path.join(settings.PROJECT_PATH,'../sensorimotordb/analysis/two_way_anova.R'))
        r_two_way_anova = robjects.globalenv['two_way_anova']
        (anova_results,visibility_pairwise, objectgrasp_pairwise, visibilityobjectgrasp_pairwise,objectgraspvisibility_pairwise)=r_two_way_anova(df,"num_spikes_diff",
            "visibility","objectgrasp")

        anova_results=pandas2ri.ri2py_dataframe(anova_results)
        visibility_pairwise=pandas2ri.ri2py_listvector(visibility_pairwise)
        objectgrasp_pairwise=pandas2ri.ri2py_listvector(objectgrasp_pairwise)
        visibilityobjectgrasp_pairwise=pandas2ri.ri2py_dataframe(visibilityobjectgrasp_pairwise)
        objectgraspvisibility_pairwise=pandas2ri.ri2py_dataframe(objectgraspvisibility_pairwise)

        return anova_results,visibility_pairwise,objectgrasp_pairwise,visibilityobjectgrasp_pairwise,objectgraspvisibility_pairwise


    def test_unit_obj_pres(self, results, unit):
        trial_ids=[]
        trial_types=[]
        objectgrasps=[]
        num_spikes_diff=[]
        condition_ids=[]
        for factor_name in ['Object Presentation - Trial Type','Object Presentation - Object']:
            factor=Factor.objects.get(analysis=results.analysis, name=factor_name)
            for level in factor.levels.all():
                for condition in level.conditions.all():
                    if not condition.id in condition_ids:
                        condition_ids.append(condition.id)
        conditions=Condition.objects.filter(id__in=condition_ids)
        for condition in conditions:
            recording_trials=RecordingTrial.objects.filter(condition=condition)
            for trial in recording_trials:

                baseline_time_zero=float(trial.start_time)
                if not self.baseline_rel_evt=='start':
                    baseline_evt=Event.objects.get(name=self.baseline_rel_evt,trial=trial)
                    baseline_time_zero=float(baseline_evt.time)
                woi_time_zero=float(trial.start_time)
                if not self.grasp_woi_rel_evt=='start':
                    woi_evt=Event.objects.get(name=self.obj_view_woi_rel_evt, trial=trial)
                    woi_time_zero=float(woi_evt.time)
                if UnitRecording.objects.filter(trial=trial, unit=unit).count():
                    unit_recording=UnitRecording.objects.get(trial=trial, unit=unit)
                    baseline_spikes=unit_recording.get_spikes(baseline_time_zero,[self.baseline_rel_start/1000.0,
                                                                                  self.baseline_rel_end/1000.0])
                    woi_spikes=unit_recording.get_spikes(woi_time_zero, [self.obj_view_woi_rel_start/1000.0,
                                                                         self.obj_view_woi_rel_end/1000.0])

                    trial_type=Level.objects.get(factor__analysis=self,factor__name='Object Presentation - Trial Type',conditions=condition).value
                    objectgrasp=Level.objects.get(factor__analysis=self,factor__name='Object Presentation - Object',conditions=condition).value

                    trial_ids.append(trial.id)
                    trial_types.append(trial_type)
                    objectgrasps.append(objectgrasp)
                    num_spikes_diff.append(len(woi_spikes)-len(baseline_spikes))

        df= pd.DataFrame({
            'trial': pd.Series(trial_ids),
            'trial_type': pd.Series(trial_types),
            'objectgrasp': pd.Series(objectgrasps),
            'num_spikes_diff': pd.Series(num_spikes_diff)
        })

        df=df.set_index(['trial'])

        r_source = robjects.r['source']
        r_source(os.path.join(settings.PROJECT_PATH,'../sensorimotordb/analysis/two_way_anova.R'))
        r_two_way_anova = robjects.globalenv['two_way_anova']
        (anova_results,trialtype_pairwise,objectgrasp_pairwise,trialtypeobjectgrasp_pairwise,objectgrasptrialtype_pairwise)=r_two_way_anova(df,"num_spikes_diff",
            "trial_type","objectgrasp")

        anova_results=pandas2ri.ri2py_dataframe(anova_results)
        trialtype_pairwise=pandas2ri.ri2py_listvector(trialtype_pairwise)
        objectgrasp_pairwise=pandas2ri.ri2py_listvector(objectgrasp_pairwise)
        trialtypeobjectgrasp_pairwise=pandas2ri.ri2py_dataframe(trialtypeobjectgrasp_pairwise)
        objectgrasptrialtype_pairwise=pandas2ri.ri2py_dataframe(objectgrasptrialtype_pairwise)

        return anova_results,trialtype_pairwise,objectgrasp_pairwise,trialtypeobjectgrasp_pairwise,objectgrasptrialtype_pairwise


    def test_unit_obs_grasp(self, results, unit):
        trial_ids=[]
        objectgrasps=[]
        num_spikes_diff=[]
        condition_ids=[]
        for factor_name in ['Grasp Observation: Object/Grasp']:
            factor=Factor.objects.get(analysis=results.analysis, name=factor_name)
            for level in factor.levels.all():
                for condition in level.conditions.all():
                    if not condition.id in condition_ids:
                        condition_ids.append(condition.id)
        conditions=Condition.objects.filter(id__in=condition_ids)
        for condition in conditions:
            recording_trials=RecordingTrial.objects.filter(condition=condition)
            for trial in recording_trials:

                baseline_time_zero=float(trial.start_time)
                if not self.baseline_rel_evt=='start':
                    baseline_evt=Event.objects.get(name=self.baseline_rel_evt,trial=trial)
                    baseline_time_zero=float(baseline_evt.time)
                woi_time_zero=float(trial.start_time)
                if not self.grasp_woi_rel_evt=='start':
                    woi_evt=Event.objects.get(name=self.grasp_woi_rel_evt, trial=trial)
                    woi_time_zero=float(woi_evt.time)
                if UnitRecording.objects.filter(trial=trial, unit=unit).count():
                    unit_recording=UnitRecording.objects.get(trial=trial, unit=unit)
                    baseline_spikes=unit_recording.get_spikes(baseline_time_zero,[self.baseline_rel_start/1000.0,
                                                                                  self.baseline_rel_end/1000.0])
                    woi_spikes=unit_recording.get_spikes(woi_time_zero, [self.grasp_woi_rel_start/1000.0,
                                                                         self.grasp_woi_rel_end/1000.0])

                    objectgrasp=Level.objects.get(factor__analysis=self,factor__name='Grasp Observation: Object/Grasp',conditions=condition).value

                    trial_ids.append(trial.id)
                    objectgrasps.append(objectgrasp)
                    num_spikes_diff.append(len(woi_spikes)-len(baseline_spikes))

        df= pd.DataFrame({
            'trial': pd.Series(trial_ids),
            'objectgrasp': pd.Series(objectgrasps),
            'num_spikes_diff': pd.Series(num_spikes_diff)
        })

        df=df.set_index(['trial'])

        r_source = robjects.r['source']
        r_source(os.path.join(settings.PROJECT_PATH,'../sensorimotordb/analysis/one_way_anova.R'))
        r_one_way_anova = robjects.globalenv['one_way_anova']
        (anova_results,objectgrasp_pairwise)=r_one_way_anova(df,"num_spikes_diff","objectgrasp")

        anova_results=pandas2ri.ri2py_dataframe(anova_results)
        objectgrasp_pairwise=pandas2ri.ri2py_dataframe(objectgrasp_pairwise)

        return anova_results,objectgrasp_pairwise

