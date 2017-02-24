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
    name=models.CharField(max_length=100, blank=False)
    description=models.TextField()

    objects = InheritanceManager()
    class Meta:
        app_label='sensorimotordb'

    def run(self, results):
        pass

class AnalysisResults(models.Model):
    analysis = models.ForeignKey('Analysis')
    experiment = models.ForeignKey('Experiment')
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

    class Meta:
        app_label='sensorimotordb'


class AnalysisResultsLevelMapping(models.Model):
    level=models.ForeignKey('Level')
    analysis_results=models.ForeignKey(AnalysisResults, related_name='level_mappings')
    conditions=models.ManyToManyField(Condition)

    class Meta:
        app_label='sensorimotordb'


class UnitClassification(MPTTModel,models.Model):
    # parent BOP
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    analysis_results=models.ForeignKey(AnalysisResults, related_name='unit_classifications')
    label=models.CharField(max_length=1000, blank=False)
    units=models.ManyToManyField(Unit)

    class Meta:
        app_label='sensorimotordb'


def get_woi_spikes(unit_recording, trial_start_time, trial_events, rel_evt, rel_start_ms, rel_end_ms, rel_end_evt):
    if len(rel_end_evt) == 0:
        woi_time_zero = float(trial_start_time)
        if not rel_evt == 'start':
            if trial_events.filter(name=rel_evt).exists():
                woi_evt = trial_events.get(name=rel_evt)
                woi_time_zero = float(woi_evt.time)
            else:
                return None
        woi_spikes = unit_recording.get_spikes_relative(woi_time_zero, [rel_start_ms, rel_end_ms])
    else:
        if trial_events.filter(name=rel_evt).exists() and trial_events.filter(name=rel_end_evt).exists():
            woi_time_start = float(trial_start_time)
            if not rel_evt == 'start':
                woi_start_evt = trial_events.get(name=rel_evt)
                woi_time_start = float(woi_start_evt.time)
            woi_time_end = float(unit_recording.trial.start_time)
            if not rel_end_evt == 'start':
                woi_end_evt = trial_events.get(name=rel_end_evt)
                woi_time_end = float(woi_end_evt.time)
            woi_spikes = unit_recording.get_spikes_fixed([woi_time_start, woi_time_end])
        else:
            return None
    return woi_spikes

def get_woi_firing_rate(unit_recording, trial_start_time, trial_events, rel_evt, rel_start_ms, rel_end_ms, rel_end_evt):
    rate=None
    if len(rel_end_evt) == 0:
        woi_time_zero = trial_start_time
        found=True
        if not rel_evt == 'start':
            found=False
            for trial_evt in trial_events:
                if trial_evt.name==rel_evt:
                    woi_time_zero = float(trial_evt.time)
                    found=True
                    break
        if found:
            woi_spikes = unit_recording.get_spikes_relative(woi_time_zero, [rel_start_ms, rel_end_ms])
            rate=len(woi_spikes)/(rel_end_ms-rel_start_ms)
    else:
        try:
            woi_time_start = trial_start_time
            found_start=True
            if not rel_evt == 'start':
                found_start=False
                for trial_evt in trial_events:
                    if trial_evt.name==rel_evt:
                        woi_time_start = float(trial_evt.time)
                        found_start=True
                        break
            woi_time_end = trial_start_time
            found_end=True
            if not rel_end_evt == 'start':
                found_end=False
                for trial_evt in trial_events:
                    if trial_evt.name==rel_end_evt:
                        woi_time_end = float(trial_evt.time)
                        found_end=True
                        break
            if found_start and found_end:
                woi_spikes = unit_recording.get_spikes_fixed([woi_time_start, woi_time_end])
                rate=len(woi_spikes)/(woi_time_end-woi_time_start)
        except:
            print('Exception')
            return None
    return rate


class VisuomotorClassificationAnalysisResults(AnalysisResults):
    baseline_rel_evt=models.CharField(max_length=1000, blank=False)
    baseline_rel_start=models.IntegerField(blank=True, null=True)
    baseline_rel_end=models.IntegerField(blank=True, null=True)
    baseline_rel_end_evt=models.CharField(max_length=1000, blank=True, null=True)
    obj_view_woi_rel_evt=models.CharField(max_length=1000, blank=False)
    obj_view_woi_rel_start=models.IntegerField(blank=True, null=True)
    obj_view_woi_rel_end=models.IntegerField(blank=True, null=True)
    obj_view_woi_rel_end_evt=models.CharField(max_length=1000, blank=True, null=True)
    grasp_woi_rel_evt=models.CharField(max_length=1000, blank=False)
    grasp_woi_rel_start=models.IntegerField(blank=True, null=True)
    grasp_woi_rel_end=models.IntegerField(blank=True, null=True)
    grasp_woi_rel_end_evt=models.CharField(max_length=1000, blank=True, null=True)
    total_num_units=models.IntegerField(blank=True, null=True)

    class Meta:
        app_label='sensorimotordb'


class VisuomotorClassificationUnitAnalysisResults(UnitAnalysisResults):
    pairwise_results_text=models.TextField()

    class Meta:
        app_label='sensorimotordb'


class VisuomotorClassificationAnalysis(Analysis):

    class Meta:
        app_label='sensorimotordb'

    def check_motor_properties(self, visuomotor_motor_results):
        motor_properties = False
        # If threeway interaction - check that grasp>baseline for at least one objectgrasp/visibility condition
        if visuomotor_motor_results['anova_within']['Pr(>F)'][3]<0.05:
            for index in visuomotor_motor_results['threeway_pairwise'].index:
                if visuomotor_motor_results['threeway_pairwise']['p.value'][index] < 0.05:
                    contrast = visuomotor_motor_results['threeway_pairwise']['contrast'][index]
                    cond_one = contrast.split(' - ')[0]
                    cond_two = contrast.split(' - ')[1]

                    cond_one_epoch = cond_one.split(',')[0]
                    cond_one_objgrasp = cond_one.split(',')[1]
                    cond_one_visibility = cond_one.split(',')[2]

                    cond_two_epoch = cond_two.split(',')[0]
                    cond_two_objgrasp = cond_two.split(',')[1]
                    cond_two_visibility = cond_two.split(',')[2]

                    # If comparing same objectgrasp/visibility combination
                    if cond_one_objgrasp == cond_two_objgrasp and cond_one_visibility == cond_two_visibility:
                        # If baseline<grasp
                        if (cond_one_epoch == 'baseline' and cond_two_epoch == 'grasping' and
                            visuomotor_motor_results['threeway_pairwise']['estimate'][index] < 0) or\
                           (cond_one_epoch == 'grasping' and cond_two_epoch == 'baseline' and
                            visuomotor_motor_results['threeway_pairwise']['estimate'][index] > 0):
                            motor_properties = True
                            break
        # If epoch x objectgrasp interaction - check that grasp>baseline for at least one object/grasp
        elif visuomotor_motor_results['anova_within']['Pr(>F)'][1]<0.05:
            for index in visuomotor_motor_results['epoch_objectgrasp_pairwise'].index:
                if visuomotor_motor_results['epoch_objectgrasp_pairwise']['p.value'][index] < 0.05:
                    contrast = visuomotor_motor_results['epoch_objectgrasp_pairwise']['contrast'][index]
                    cond_one = contrast.split(' - ')[0]
                    cond_two = contrast.split(' - ')[1]

                    cond_one_epoch = cond_one.split(',')[0]
                    cond_one_objgrasp = cond_one.split(',')[1]

                    cond_two_epoch = cond_two.split(',')[0]
                    cond_two_objgrasp = cond_two.split(',')[1]

                    # If comparing same objectgrasp/visibility combination
                    if cond_one_objgrasp == cond_two_objgrasp:
                        # If baseline<grasp
                        if (cond_one_epoch == 'baseline' and cond_two_epoch == 'grasping' and
                            visuomotor_motor_results['epoch_objectgrasp_pairwise']['estimate'][index] < 0) or\
                           (cond_one_epoch == 'grasping' and cond_two_epoch == 'baseline' and
                            visuomotor_motor_results['epoch_objectgrasp_pairwise']['estimate'][index] > 0):
                            motor_properties = True
                            break
        # If epoch x visibility interaction - checkt that grasp>baseline for at least one visibility condition
        elif visuomotor_motor_results['anova_within']['Pr(>F)'][2]<.05:
            for index in visuomotor_motor_results['epoch_visibility_pairwise'].index:
                if visuomotor_motor_results['epoch_visibility_pairwise']['p.value'][index] < 0.05:
                    contrast = visuomotor_motor_results['epoch_visibility_pairwise']['contrast'][index]
                    cond_one = contrast.split(' - ')[0]
                    cond_two = contrast.split(' - ')[1]

                    cond_one_epoch = cond_one.split(',')[0]
                    cond_one_visibility = cond_one.split(',')[1]

                    cond_two_epoch = cond_two.split(',')[0]
                    cond_two_visibility = cond_two.split(',')[1]

                    # If comparing same objectgrasp/visibility combination
                    if cond_one_visibility == cond_two_visibility:
                        # If baseline<grasp
                        if (cond_one_epoch == 'baseline' and cond_two_epoch == 'grasping' and
                            visuomotor_motor_results['epoch_visibility_pairwise']['estimate'][index] < 0) or\
                           (cond_one_epoch == 'grasping' and cond_two_epoch == 'baseline' and
                            visuomotor_motor_results['epoch_visibility_pairwise']['estimate'][index] > 0):
                            motor_properties = True
                            break

        # If main effect f epoch - check that grasp>baseline
        elif visuomotor_motor_results['anova_within']['Pr(>F)'][0]<0.05:
            index = visuomotor_motor_results['epoch_pairwise'].index[0]
            if visuomotor_motor_results['epoch_pairwise']['p.value'][index] < 0.05 and \
               visuomotor_motor_results['epoch_pairwise']['estimate'][index] < 0:
                motor_properties = True

        grasp_selective = False
        if motor_properties:
            # Grasp selective if epoch:objectgrasp:visibility or epoch:objectgrasp or objectgrasp:visibility or objectgrasp
            if visuomotor_motor_results['anova_within']['Pr(>F)'][3]<0.05 or \
               visuomotor_motor_results['anova_within']['Pr(>F)'][1]<0.05 or \
               visuomotor_motor_results['anova_trial']['Pr(>F)'][2]<0.05 or \
               visuomotor_motor_results['anova_trial']['Pr(>F)'][0]<0.05:
                grasp_selective=True

        return motor_properties, grasp_selective


    def check_objpres_properties(self, objpres_results):
        objpres_properties = False
        # If threeway interaction - check that grasp>baseline for at least one objectgrasp/visibility condition
        if objpres_results['anova_within']['Pr(>F)'][3]<0.05:
            for index in objpres_results['threeway_pairwise'].index:
                if objpres_results['threeway_pairwise']['p.value'][index] < 0.05:
                    contrast = objpres_results['threeway_pairwise']['contrast'][index]
                    cond_one = contrast.split(' - ')[0]
                    cond_two = contrast.split(' - ')[1]

                    cond_one_epoch = cond_one.split(',')[0]
                    cond_one_objgrasp = cond_one.split(',')[1]
                    cond_one_trialtype = cond_one.split(',')[2]

                    cond_two_epoch = cond_two.split(',')[0]
                    cond_two_objgrasp = cond_two.split(',')[1]
                    cond_two_trialtype = cond_two.split(',')[2]

                    # If comparing same objectgrasp/visibility combination
                    if cond_one_objgrasp == cond_two_objgrasp and cond_one_trialtype == cond_two_trialtype:
                        # If baseline<grasp
                        if (cond_one_epoch == 'baseline' and cond_two_epoch == 'fixation' and
                            objpres_results['threeway_pairwise']['estimate'][index] < 0) or\
                           (cond_one_epoch == 'fixation' and cond_two_epoch == 'baseline' and
                            objpres_results['threeway_pairwise']['estimate'][index] > 0):
                            objpres_properties = True
                            break
        # If epoch x objectgrasp interaction - check that grasp>baseline for at least one object/grasp
        elif objpres_results['anova_within']['Pr(>F)'][1]<0.05:
            for index in objpres_results['epoch_objectgrasp_pairwise'].index:
                if objpres_results['epoch_objectgrasp_pairwise']['p.value'][index] < 0.05:
                    contrast = objpres_results['epoch_objectgrasp_pairwise']['contrast'][index]
                    cond_one = contrast.split(' - ')[0]
                    cond_two = contrast.split(' - ')[1]

                    cond_one_epoch = cond_one.split(',')[0]
                    cond_one_objgrasp = cond_one.split(',')[1]

                    cond_two_epoch = cond_two.split(',')[0]
                    cond_two_objgrasp = cond_two.split(',')[1]

                    # If comparing same objectgrasp/visibility combination
                    if cond_one_objgrasp == cond_two_objgrasp:
                        # If baseline<grasp
                        if (cond_one_epoch == 'baseline' and cond_two_epoch == 'fixation' and
                            objpres_results['epoch_objectgrasp_pairwise']['estimate'][index] < 0) or\
                           (cond_one_epoch == 'fixation' and cond_two_epoch == 'baseline' and
                            objpres_results['epoch_objectgrasp_pairwise']['estimate'][index] > 0):
                            objpres_properties = True
                            break
        # If epoch x trialtype interaction - checkt that grasp>baseline for at least one visibility condition
        elif objpres_results['anova_within']['Pr(>F)'][2]<0.05:
            for index in objpres_results['epoch_trialtype_pairwise'].index:
                if objpres_results['epoch_trialtype_pairwise']['p.value'][index] < 0.05:
                    contrast = objpres_results['epoch_trialtype_pairwise']['contrast'][index]
                    cond_one = contrast.split(' - ')[0]
                    cond_two = contrast.split(' - ')[1]

                    cond_one_epoch = cond_one.split(',')[0]
                    cond_one_trialtype = cond_one.split(',')[1]

                    cond_two_epoch = cond_two.split(',')[0]
                    cond_two_trialtype = cond_two.split(',')[1]

                    # If comparing same objectgrasp/visibility combination
                    if cond_one_trialtype == cond_two_trialtype:
                        # If baseline<grasp
                        if (cond_one_epoch == 'baseline' and cond_two_epoch == 'fixation' and
                            objpres_results['epoch_trialtype_pairwise']['estimate'][index] < 0) or\
                           (cond_one_epoch == 'fixation' and cond_two_epoch == 'baseline' and
                            objpres_results['epoch_trialtype_pairwise']['estimate'][index] > 0):
                            objpres_properties = True
                            break

        # If main effect f epoch - check that grasp>baseline
        elif objpres_results['anova_within']['Pr(>F)'][0]<0.05:
            index = objpres_results['epoch_pairwise'].index[0]
            if objpres_results['epoch_pairwise']['p.value'][index] < 0.05 and\
               objpres_results['epoch_pairwise']['estimate'][index] < 0:
                objpres_properties = True

        return objpres_properties


    def check_observation_properties(self, obs_results):
        obs_properties = False
        # If twoway interaction - check that grasp>baseline for at least one objectgrasp condition
        if obs_results['anova_within']['Pr(>F)'][1]<0.05:
            for index in obs_results['twoway_pairwise'].index:
                if obs_results['twoway_pairwise']['p.value'][index] < 0.05:
                    contrast = obs_results['twoway_pairwise']['contrast'][index]
                    cond_one = contrast.split(' - ')[0]
                    cond_two = contrast.split(' - ')[1]

                    cond_one_epoch = cond_one.split(',')[0]
                    cond_one_objgrasp = cond_one.split(',')[1]

                    cond_two_epoch = cond_two.split(',')[0]
                    cond_two_objgrasp = cond_two.split(',')[1]

                    # If comparing same objectgrasp/visibility combination
                    if cond_one_objgrasp == cond_two_objgrasp:
                        # If baseline<grasp
                        if (cond_one_epoch == 'baseline' and cond_two_epoch == 'grasping' and
                            obs_results['twoway_pairwise']['estimate'][index] < 0) or\
                           (cond_one_epoch == 'grasping' and cond_two_epoch == 'baseline' and
                            obs_results['twoway_pairwise']['estimate'][index] > 0):
                            obs_properties = True
                            break
        # If main effect f epoch - check that grasp>baseline
        elif obs_results['anova_within']['Pr(>F)'][0]<0.05:
            index = obs_results['epoch_pairwise'].index[0]
            if obs_results['epoch_pairwise']['p.value'][index] < 0.05 and\
               obs_results['epoch_pairwise']['estimate'][index] < 0:
                obs_properties = True

        grasp_selective = False
        if obs_properties:
            # Grasp selective if epoch:objectgrasp or objectgrasp
            if obs_results['anova_within']['Pr(>F)'][1]<0.05 or\
               obs_results['anova_trial']['Pr(>F)'][0]<0.05:
                grasp_selective=True

        return obs_properties, grasp_selective


    def run(self, results):
        unit_ids=np.unique(UnitRecording.objects.filter(trial__condition__experiment=results.experiment).values_list('unit',
            flat=True))
        results.total_num_units=len(unit_ids)
        results.save()

        unit_classifications={
            "motor":UnitClassification(analysis_results=results, label='motor'),
            "visual":UnitClassification(analysis_results=results, label='visual'),
            "visuomotor":UnitClassification(analysis_results=results, label='visuomotor'),
            "other":UnitClassification(analysis_results=results, label='other')
        }
        for label, classification in unit_classifications.iteritems():
            classification.save()
        unit_classifications['motor - grasp selective']=UnitClassification(parent=unit_classifications['motor'],analysis_results=results,label='motor - grasp selective')
        unit_classifications['motor - grasp selective'].save()
        unit_classifications['motor - grasp unselective']=UnitClassification(parent=unit_classifications['motor'],analysis_results=results,label='motor - grasp unselective')
        unit_classifications['motor - grasp unselective'].save()
        unit_classifications['canonical']=UnitClassification(parent=unit_classifications['visuomotor'],analysis_results=results,label='canonical')
        unit_classifications['canonical'].save()
        unit_classifications['mirror']=UnitClassification(parent=unit_classifications['visuomotor'],analysis_results=results,label='mirror')
        unit_classifications['mirror'].save()
        unit_classifications['mirror - grasp selective']=UnitClassification(parent=unit_classifications['mirror'],analysis_results=results,label='mirror - grasp unselective')
        unit_classifications['mirror - grasp selective'].save()
        unit_classifications['mirror - grasp unselective']=UnitClassification(parent=unit_classifications['mirror'],analysis_results=results,label='mirror - grasp unselective')
        unit_classifications['mirror - grasp unselective'].save()
        unit_classifications['canonical mirror']=UnitClassification(parent=unit_classifications['visuomotor'],analysis_results=results,label='canonical mirror')
        unit_classifications['canonical mirror'].save()
        unit_classifications['visuomotor other']=UnitClassification(parent=unit_classifications['visuomotor'],analysis_results=results,label='visuomotor other')
        unit_classifications['visuomotor other'].save()

        for unit_id in unit_ids:
            unit=Unit.objects.get(id=unit_id)
            visuomotor_motor_results=self.test_unit_motor(results, unit)
            visuomotor_objpres_results=self.test_unit_obj_pres(results, unit, 'Visuomotor')

            obs_grasp_results=self.test_unit_obs_grasp(results, unit)
            obs_objpres_results=self.test_unit_obj_pres(results, unit, 'Observation')

            unit_results=VisuomotorClassificationUnitAnalysisResults(analysis_results=results,
                results_text='\n'.join(['<h2>Motor</h2>',str(visuomotor_motor_results['anova_trial']),str(visuomotor_motor_results['anova_within']),
                                        '<h2>Visuomotor: Object Presentation</h2>',str(visuomotor_objpres_results['anova_trial']), str(visuomotor_objpres_results['anova_within']),
                                        '<h2>Observation</h2>',str(obs_grasp_results['anova_trial']), str(obs_grasp_results['anova_within']),
                                        '<h2>Observation: Object Presentation</h2>',str(obs_objpres_results['anova_trial']), str(obs_objpres_results['anova_within']),

                ]),
                pairwise_results_text='\n'.join(['<h2>Motor</h2>',
                                                 str(visuomotor_motor_results['threeway_pairwise']),
                                                 str(visuomotor_motor_results['epoch_objectgrasp_pairwise']),
                                                 str(visuomotor_motor_results['epoch_visibility_pairwise']),
                                                 str(visuomotor_motor_results['objectgrasp_visibility_pairwise']),
                                                 str(visuomotor_motor_results['epoch_pairwise']),
                                                 str(visuomotor_motor_results['objectgrasp_pairwise']),
                                                 str(visuomotor_motor_results['visibility_pairwise']),
                                                 '<h2>Visuomotor: Object Presentation</h2>',
                                                 str(visuomotor_objpres_results['threeway_pairwise']),
                                                 str(visuomotor_objpres_results['epoch_objectgrasp_pairwise']),
                                                 str(visuomotor_objpres_results['epoch_trialtype_pairwise']),
                                                 str(visuomotor_objpres_results['objectgrasp_trialtype_pairwise']),
                                                 str(visuomotor_objpres_results['epoch_pairwise']),
                                                 str(visuomotor_objpres_results['objectgrasp_pairwise']),
                                                 str(visuomotor_objpres_results['trialtype_pairwise']),
                                                 '<h2>Observation</h2>',
                                                 str(obs_grasp_results['twoway_pairwise']),
                                                 str(obs_grasp_results['epoch_pairwise']),
                                                 str(obs_grasp_results['objectgrasp_pairwise']),
                                                 '<h2>Observation: Object Presentation</h2>',
                                                 str(obs_objpres_results['threeway_pairwise']),
                                                 str(obs_objpres_results['epoch_objectgrasp_pairwise']),
                                                 str(obs_objpres_results['epoch_trialtype_pairwise']),
                                                 str(obs_objpres_results['objectgrasp_trialtype_pairwise']),
                                                 str(obs_objpres_results['epoch_pairwise']),
                                                 str(obs_objpres_results['objectgrasp_pairwise']),
                                                 str(obs_objpres_results['trialtype_pairwise'])
                ]),
                unit=unit)
            unit_results.save()

            (motor_properties,motor_grasp_selective) = self.check_motor_properties(visuomotor_motor_results)
            visuomotor_objpres_properties = self.check_objpres_properties(visuomotor_objpres_results)

            observation_objpres_properties = self.check_objpres_properties(obs_objpres_results)
            (observation_properties,obs_grasp_selective) = self.check_observation_properties(obs_grasp_results)

            visual_properties = visuomotor_objpres_properties or observation_objpres_properties or observation_properties

            # If cell has motor and visual properties -> visomotor
            if motor_properties and visual_properties:
                unit_classifications['visuomotor'].units.add(unit)

                # If fires for object presentation and action observation -> canonical mirror
                if visuomotor_objpres_properties and not (observation_objpres_properties or observation_properties):
                    unit_classifications['canonical'].units.add(unit)
                # If fires only for object presentation -> canonical
                elif observation_properties and (visuomotor_objpres_properties or observation_objpres_properties):
                    unit_classifications['canonical mirror'].units.add(unit)
                # If fires only during action observation -> mirror
                elif observation_properties:
                    unit_classifications['mirror'].units.add(unit)
                    if obs_grasp_selective:
                        unit_classifications['mirror - grasp selective'].units.add(unit)
                    else:
                        unit_classifications['mirror - grasp unselective'].units.add(unit)
                else:
                    unit_classifications['visuomotor other'].units.add(unit)

            # If only has motor properties -> motor
            elif motor_properties :
                unit_classifications['motor'].units.add(unit)

                if motor_grasp_selective:
                    unit_classifications['motor - grasp selective'].units.add(unit)
                else:
                    unit_classifications['motor - grasp unselective'].units.add(unit)

            # If only has visual properties -> visual
            elif visual_properties:
                unit_classifications['visual'].units.add(unit)
            # Otherwise other
            else:
                unit_classifications['other'].units.add(unit)

        print('%.4f %% motor cells' % (unit_classifications['motor'].units.count()/float(len(unit_ids))*100.0))
        print('%.4f %% visual cells' % (unit_classifications['visual'].units.count()/float(len(unit_ids))*100.0))
        print('%.4f %% visuomotor cells' % (unit_classifications['visuomotor'].units.count()/float(len(unit_ids))*100.0))
        print('%.4f %% other cells' % (unit_classifications['other'].units.count()/float(len(unit_ids))*100.0))


    def test_unit_motor(self, results, unit):
        trial_ids=[]
        visibilities=[]
        objectgrasps=[]
        epochs=[]
        rates=[]
        condition_ids=[]
        for factor_name in ['Visuomotor Grasp Execution: Visibility','Visuomotor Grasp Execution: Object/Grasp']:
            factor=Factor.objects.get(analysis=results.analysis, name=factor_name)
            for level in factor.levels.all():
                conditions=AnalysisResultsLevelMapping.objects.get(level=level,analysis_results=results).conditions.all()
                for condition in conditions:
                    if not condition.id in condition_ids:
                        condition_ids.append(condition.id)
        conditions=Condition.objects.filter(id__in=condition_ids)
        for condition in conditions:
            recording_trials=RecordingTrial.objects.filter(condition=condition)
            for trial in recording_trials:
                trial_events=list(Event.objects.filter(trial=trial))
                trial_start_time=float(trial.start_time)
                if UnitRecording.objects.filter(trial=trial, unit=unit).count():
                    unit_recording=UnitRecording.objects.get(trial=trial, unit=unit)

                    baseline_rel_start=0
                    if results.baseline_rel_start is not None:
                        baseline_rel_start=results.baseline_rel_start/1000.0
                    baseline_rel_end=0
                    if results.baseline_rel_end is not None:
                        baseline_rel_end=results.baseline_rel_end/1000.0
                    baseline_rate = get_woi_firing_rate(unit_recording, trial_start_time, trial_events, results.baseline_rel_evt,
                        baseline_rel_start, baseline_rel_end, results.baseline_rel_end_evt)

                    grasp_woi_rel_start=0
                    if results.grasp_woi_rel_start is not None:
                        grasp_woi_rel_start=results.grasp_woi_rel_start/1000.0
                    grasp_woi_rel_end=0
                    if results.grasp_woi_rel_end is not None:
                        grasp_woi_rel_end=results.grasp_woi_rel_end/1000.0
                    woi_rate = get_woi_firing_rate(unit_recording, trial_start_time, trial_events, results.grasp_woi_rel_evt,
                        grasp_woi_rel_start, grasp_woi_rel_end, results.grasp_woi_rel_end_evt)

                    if baseline_rate is not None and woi_rate is not None:
                        visibility=Level.objects.get(factor__analysis=self,factor__name='Visuomotor Grasp Execution: Visibility',
                            analysisresultslevelmapping__conditions=condition,
                            analysisresultslevelmapping__analysis_results=results).value
                        objectgrasp=Level.objects.get(factor__analysis=self,factor__name='Visuomotor Grasp Execution: Object/Grasp',
                            analysisresultslevelmapping__conditions=condition,
                            analysisresultslevelmapping__analysis_results=results).value

                        trial_ids.append(trial.id)
                        visibilities.append(visibility)
                        objectgrasps.append(objectgrasp)
                        epochs.append('baseline')
                        rates.append(baseline_rate)

                        trial_ids.append(trial.id)
                        visibilities.append(visibility)
                        objectgrasps.append(objectgrasp)
                        epochs.append('grasping')
                        rates.append(woi_rate)


        df= pd.DataFrame({
            'trial': pd.Series(trial_ids),
            'visibility': pd.Series(visibilities),
            'objectgrasp': pd.Series(objectgrasps),
            'epoch': pd.Series(epochs),
            'rate': pd.Series(rates)
        })

        #df=df.set_index(['trial'])

        r_source = robjects.r['source']
        r_source(os.path.join(settings.PROJECT_PATH,'../sensorimotordb/analysis/three_way_anova_repeated_measures.R'))
        r_three_way_anova = robjects.globalenv['three_way_anova_repeated_measures']
        (anova_results_trial, anova_results_within, threeway_pairwise, epoch_objectgrasp_pairwise,
            epoch_visibility_pairwise, objectgrasp_visibility_pairwise, epoch_pairwise, objectgrasp_pairwise,
            visibility_pairwise)=r_three_way_anova(df,"trial","rate","epoch","objectgrasp","visibility")
        stats_results={
            'anova_trial': pandas2ri.ri2py_dataframe(anova_results_trial[0]),
            'anova_within': pandas2ri.ri2py_dataframe(anova_results_within[0]),
            'threeway_pairwise': pandas2ri.ri2py_dataframe(threeway_pairwise),
            'epoch_objectgrasp_pairwise': pandas2ri.ri2py_dataframe(epoch_objectgrasp_pairwise),
            'epoch_visibility_pairwise': pandas2ri.ri2py_dataframe(epoch_visibility_pairwise),
            'objectgrasp_visibility_pairwise': pandas2ri.ri2py_dataframe(objectgrasp_visibility_pairwise),
            'epoch_pairwise': pandas2ri.ri2py_dataframe(epoch_pairwise),
            'objectgrasp_pairwise': pandas2ri.ri2py_dataframe(objectgrasp_pairwise),
            'visibility_pairwise': pandas2ri.ri2py_dataframe(visibility_pairwise)
        }
        return stats_results


    def test_unit_obj_pres(self, results, unit, task):
        trial_ids=[]
        trial_types=[]
        objectgrasps=[]
        epochs=[]
        rates=[]
        condition_ids=[]
        for factor_name in ['%s Object Presentation - Trial Type' % task, '%s Object Presentation - Object' % task]:
            factor=Factor.objects.get(analysis=results.analysis, name=factor_name)
            for level in factor.levels.all():
                conditions=AnalysisResultsLevelMapping.objects.get(level=level,analysis_results=results).conditions.all()
                for condition in conditions:
                    if not condition.id in condition_ids:
                        condition_ids.append(condition.id)
        conditions=Condition.objects.filter(id__in=condition_ids)
        for condition in conditions:
            recording_trials=RecordingTrial.objects.filter(condition=condition)
            for trial in recording_trials:
                trial_events=list(Event.objects.filter(trial=trial))
                trial_start_time=float(trial.start_time)
                if UnitRecording.objects.filter(trial=trial, unit=unit).count():
                    unit_recording=UnitRecording.objects.get(trial=trial, unit=unit)

                    baseline_rel_start=0
                    if results.baseline_rel_start is not None:
                        baseline_rel_start=results.baseline_rel_start/1000.0
                    baseline_rel_end=0
                    if results.baseline_rel_end is not None:
                        baseline_rel_end=results.baseline_rel_end/1000.0
                    baseline_rate = get_woi_firing_rate(unit_recording, trial_start_time, trial_events, results.baseline_rel_evt,
                        baseline_rel_start, baseline_rel_end, results.baseline_rel_end_evt)

                    obj_view_woi_rel_start=0
                    if results.obj_view_woi_rel_start is not None:
                        obj_view_woi_rel_start=results.obj_view_woi_rel_start/1000.0
                    obj_view_woi_rel_end=0
                    if results.obj_view_woi_rel_end is not None:
                        obj_view_woi_rel_end=results.obj_view_woi_rel_end/1000.0
                    woi_rate = get_woi_firing_rate(unit_recording, trial_start_time, trial_events, results.obj_view_woi_rel_evt,
                        obj_view_woi_rel_start, obj_view_woi_rel_end, results.obj_view_woi_rel_end_evt)

                    if baseline_rate is not None and woi_rate is not None:
                        trial_type=Level.objects.get(factor__analysis=self,factor__name='%s Object Presentation - Trial Type' % task,
                            analysisresultslevelmapping__conditions=condition,
                            analysisresultslevelmapping__analysis_results=results).value
                        objectgrasp=Level.objects.get(factor__analysis=self,factor__name='%s Object Presentation - Object' % task,
                            analysisresultslevelmapping__conditions=condition,
                            analysisresultslevelmapping__analysis_results=results).value

                        trial_ids.append(trial.id)
                        trial_types.append(trial_type)
                        objectgrasps.append(objectgrasp)
                        epochs.append('baseline')
                        rates.append(baseline_rate)

                        trial_ids.append(trial.id)
                        trial_types.append(trial_type)
                        objectgrasps.append(objectgrasp)
                        epochs.append('fixation')
                        rates.append(woi_rate)


        df= pd.DataFrame({
            'trial': pd.Series(trial_ids),
            'trial_type': pd.Series(trial_types),
            'objectgrasp': pd.Series(objectgrasps),
            'epoch': pd.Series(epochs),
            'rate': pd.Series(rates)
        })

        #df=df.set_index(['trial'])

        r_source = robjects.r['source']
        r_source(os.path.join(settings.PROJECT_PATH,'../sensorimotordb/analysis/three_way_anova_repeated_measures.R'))
        r_three_way_anova = robjects.globalenv['three_way_anova_repeated_measures']
        (anova_results_trial, anova_results_within, threeway_pairwise, epoch_objectgrasp_pairwise,
             epoch_visibility_pairwise, objectgrasp_visibility_pairwise, epoch_pairwise, objectgrasp_pairwise,
            visibility_pairwise)=r_three_way_anova(df,"trial","rate","epoch","objectgrasp","trial_type")
        stats_results={
            'anova_trial': pandas2ri.ri2py_dataframe(anova_results_trial[0]),
            'anova_within': pandas2ri.ri2py_dataframe(anova_results_within[0]),
            'threeway_pairwise': pandas2ri.ri2py_dataframe(threeway_pairwise),
            'epoch_objectgrasp_pairwise': pandas2ri.ri2py_dataframe(epoch_objectgrasp_pairwise),
            'epoch_trialtype_pairwise': pandas2ri.ri2py_dataframe(epoch_visibility_pairwise),
            'objectgrasp_trialtype_pairwise': pandas2ri.ri2py_dataframe(objectgrasp_visibility_pairwise),
            'epoch_pairwise': pandas2ri.ri2py_dataframe(epoch_pairwise),
            'objectgrasp_pairwise': pandas2ri.ri2py_dataframe(objectgrasp_pairwise),
            'trialtype_pairwise': pandas2ri.ri2py_dataframe(visibility_pairwise)
        }
        return stats_results


    def test_unit_obs_grasp(self, results, unit):
        trial_ids=[]
        objectgrasps=[]
        epochs=[]
        rates=[]
        condition_ids=[]
        for factor_name in ['Observation: Object/Grasp']:
            factor=Factor.objects.get(analysis=results.analysis, name=factor_name)
            for level in factor.levels.all():
                conditions=AnalysisResultsLevelMapping.objects.get(level=level,analysis_results=results).conditions.all()
                for condition in conditions:
                    if not condition.id in condition_ids:
                        condition_ids.append(condition.id)
        conditions=Condition.objects.filter(id__in=condition_ids)
        for condition in conditions:
            recording_trials=RecordingTrial.objects.filter(condition=condition)
            for trial in recording_trials:
                trial_events=list(Event.objects.filter(trial=trial))
                trial_start_time=float(trial.start_time)
                if UnitRecording.objects.filter(trial=trial, unit=unit).count():
                    unit_recording=UnitRecording.objects.get(trial=trial, unit=unit)

                    baseline_rel_start=0
                    if results.baseline_rel_start is not None:
                        baseline_rel_start=results.baseline_rel_start/1000.0
                    baseline_rel_end=0
                    if results.baseline_rel_end is not None:
                        baseline_rel_end=results.baseline_rel_end/1000.0
                    baseline_rate = get_woi_firing_rate(unit_recording, trial_start_time, trial_events, results.baseline_rel_evt,
                        baseline_rel_start, baseline_rel_end, results.baseline_rel_end_evt)

                    grasp_woi_rel_start=0
                    if results.grasp_woi_rel_start is not None:
                        grasp_woi_rel_start=results.grasp_woi_rel_start/1000.0
                    grasp_woi_rel_end=0
                    if results.grasp_woi_rel_end is not None:
                        grasp_woi_rel_end=results.grasp_woi_rel_end/1000.0
                    woi_rate = get_woi_firing_rate(unit_recording, trial_start_time, trial_events, results.grasp_woi_rel_evt,
                        grasp_woi_rel_start, grasp_woi_rel_end, results.grasp_woi_rel_end_evt)

                    if baseline_rate is not None and woi_rate is not None:
                        objectgrasp=Level.objects.get(factor__analysis=self,factor__name='Observation: Object/Grasp',
                            analysisresultslevelmapping__conditions=condition,
                            analysisresultslevelmapping__analysis_results=results).value

                        trial_ids.append(trial.id)
                        objectgrasps.append(objectgrasp)
                        epochs.append('baseline')
                        rates.append(baseline_rate)

                        trial_ids.append(trial.id)
                        objectgrasps.append(objectgrasp)
                        epochs.append('grasping')
                        rates.append(woi_rate)

        df= pd.DataFrame({
            'trial': pd.Series(trial_ids),
            'objectgrasp': pd.Series(objectgrasps),
            'epoch': pd.Series(epochs),
            'rate': pd.Series(rates)
        })

        #df=df.set_index(['trial'])

        r_source = robjects.r['source']
        r_source(os.path.join(settings.PROJECT_PATH,'../sensorimotordb/analysis/two_way_anova_repeated_measures.R'))
        r_two_way_anova = robjects.globalenv['two_way_anova_repeated_measures']
        (anova_results_trial, anova_results_within, twoway_pairwise, epoch_pairwise, objectgrasp_pairwise)=r_two_way_anova(df,"trial","rate","epoch","objectgrasp")
        stats_results={
            'anova_trial': pandas2ri.ri2py_dataframe(anova_results_trial[0]),
            'anova_within': pandas2ri.ri2py_dataframe(anova_results_within[0]),
            'twoway_pairwise': pandas2ri.ri2py_dataframe(twoway_pairwise),
            'epoch_pairwise': pandas2ri.ri2py_dataframe(epoch_pairwise),
            'objectgrasp_pairwise': pandas2ri.ri2py_dataframe(objectgrasp_pairwise),
        }
        return stats_results


class MirrorTypeClassificationAnalysisResults(AnalysisResults):
    baseline_rel_evt=models.CharField(max_length=1000, blank=False)
    baseline_rel_start=models.IntegerField(blank=True, null=True)
    baseline_rel_end=models.IntegerField(blank=True, null=True)
    baseline_rel_end_evt=models.CharField(max_length=1000, blank=True, null=True)
    reach_woi_rel_evt=models.CharField(max_length=1000, blank=False)
    reach_woi_rel_start=models.IntegerField(blank=True, null=True)
    reach_woi_rel_end=models.IntegerField(blank=True, null=True)
    reach_woi_rel_end_evt=models.CharField(max_length=1000, blank=True, null=True)
    hold_woi_rel_evt=models.CharField(max_length=1000, blank=False)
    hold_woi_rel_start=models.IntegerField(blank=True, null=True)
    hold_woi_rel_end=models.IntegerField(blank=True, null=True)
    hold_woi_rel_end_evt=models.CharField(max_length=1000, blank=True, null=True)
    total_num_units=models.IntegerField(blank=True, null=True)

    class Meta:
        app_label='sensorimotordb'


class MirrorTypeClassificationUnitAnalysisResults(UnitAnalysisResults):
    pairwise_results_text=models.TextField()

    class Meta:
        app_label='sensorimotordb'


class MirrorTypeClassificationAnalysis(Analysis):

    class Meta:
        app_label='sensorimotordb'

    def run(self, results):
        unit_ids=np.unique(UnitRecording.objects.filter(trial__condition__experiment=results.experiment).values_list('unit',
            flat=True))
        results.total_num_units=len(unit_ids)
        results.save()

        unit_classifications={
            'F-F':UnitClassification(analysis_results=results, label='F-F'),
            'F-S':UnitClassification(analysis_results=results, label='F-S'),
            'F-ns':UnitClassification(analysis_results=results, label='F-ns'),
            'S-F':UnitClassification(analysis_results=results, label='S-F'),
            'S-S':UnitClassification(analysis_results=results, label='S-S'),
            'S-ns':UnitClassification(analysis_results=results, label='S-ns'),
            'ns-F':UnitClassification(analysis_results=results, label='ns-F'),
            'ns-S':UnitClassification(analysis_results=results, label='ns-S'),
            'ns-ns':UnitClassification(analysis_results=results, label='ns-ns')
        }
        for label, classification in unit_classifications.iteritems():
            classification.save()

        r_source = robjects.r['source']
        r_source(os.path.join(settings.PROJECT_PATH,'../sensorimotordb/analysis/one_way_anova_repeated_measures.R'))
        r_one_way_anova = robjects.globalenv['one_way_anova_repeated_measures']

        for unit_id in unit_ids:
            print('testing %d' % unit_id)
            unit=Unit.objects.get(id=unit_id)
            (exe_anova_results,exe_pairwise,exe_rates)=self.test_unit(r_one_way_anova, results, unit, 'execution')
            (obs_anova_results,obs_pairwise,obs_rates)=self.test_unit(r_one_way_anova, results, unit, 'observation')

            unit_results=VisuomotorClassificationUnitAnalysisResults(analysis_results=results,
                results_text='\n'.join(['<h2>Execution</h2>',str(exe_anova_results),
                                        '<h2>Observation</h2>',str(obs_anova_results)]),
                pairwise_results_text='\n'.join(['<h2>Execution</h2>',
                                                 str(exe_pairwise),
                                                 '<h2>Observation</h2>',
                                                 str(obs_pairwise)]),
                unit=unit)
            unit_results.save()

            exe_classification='ns'
            exe_anova_results=pandas2ri.ri2py_dataframe(exe_anova_results[1])
            if exe_anova_results[4][0][0]<0.05:
                # Reach compared to baseline
                if exe_pairwise[1]<0.05:
                    if np.mean(exe_rates['reach'])>np.mean(exe_rates['baseline']):
                        exe_classification='F'
                    else:
                        exe_classification='S'
                # Hold compared to baseline
                elif exe_pairwise[0]<0.05:
                    if np.mean(exe_rates['hold'])>np.mean(exe_rates['baseline']):
                        exe_classification='F'
                    else:
                        exe_classification='S'
            obs_classification='ns'
            obs_anova_results=pandas2ri.ri2py_dataframe(obs_anova_results[1])
            if obs_anova_results[4][0][0]<0.05:
                if obs_pairwise[1]<0.05:
                    if np.mean(obs_rates['reach'])>np.mean(obs_rates['baseline']):
                        obs_classification='F'
                    else:
                        obs_classification='S'
                elif obs_pairwise[0]<0.05:
                    if np.mean(obs_rates['hold'])>np.mean(exe_rates['baseline']):
                        obs_classification='F'
                    else:
                        obs_classification='S'
            unit_classifications['%s-%s' % (exe_classification,obs_classification)].units.add(Unit.objects.get(id=unit_id))

        print('%.4f %% F-F cells' % (unit_classifications['F-F'].units.count()/float(len(unit_ids))*100.0))
        print('%.4f %% F-S cells' % (unit_classifications['F-S'].units.count()/float(len(unit_ids))*100.0))
        print('%.4f %% F-ns cells' % (unit_classifications['F-ns'].units.count()/float(len(unit_ids))*100.0))
        print('%.4f %% S-F cells' % (unit_classifications['S-F'].units.count()/float(len(unit_ids))*100.0))
        print('%.4f %% S-S cells' % (unit_classifications['S-S'].units.count()/float(len(unit_ids))*100.0))
        print('%.4f %% S-ns cells' % (unit_classifications['S-ns'].units.count()/float(len(unit_ids))*100.0))
        print('%.4f %% ns-F cells' % (unit_classifications['ns-F'].units.count()/float(len(unit_ids))*100.0))
        print('%.4f %% ns-S cells' % (unit_classifications['ns-S'].units.count()/float(len(unit_ids))*100.0))
        print('%.4f %% ns-ns cells' % (unit_classifications['ns-ns'].units.count()/float(len(unit_ids))*100.0))

    def test_unit(self, r_one_way_anova, results, unit, trial_type):
        trial_ids=[]
        rates=[]
        wois=[]
        all_rates={
            'baseline':[],
            'reach':[],
            'hold':[]
        }

        condition_ids=[]
        factor=Factor.objects.get(analysis=results.analysis, name='Trial type')
        level=Level.objects.get(factor=factor, value=trial_type)
        conditions=AnalysisResultsLevelMapping.objects.get(level=level,analysis_results=results).conditions.all()
        for condition in conditions:
            if not condition.id in condition_ids:
                condition_ids.append(condition.id)

        unit_recordings=UnitRecording.objects.filter(trial__condition__id__in=condition_ids, unit=unit).select_related('trial')
        for trial_idx,unit_recording in enumerate(unit_recordings):
            trial_events=list(Event.objects.filter(trial=unit_recording.trial))
            trial_start_time=float(unit_recording.trial.start_time)

            baseline_rel_start=0
            if results.baseline_rel_start is not None:
                baseline_rel_start=results.baseline_rel_start/1000.0
            baseline_rel_end=0
            if results.baseline_rel_end is not None:
                baseline_rel_end=results.baseline_rel_end/1000.0
            baseline_rate = get_woi_firing_rate(unit_recording, trial_start_time, trial_events, results.baseline_rel_evt,
                baseline_rel_start, baseline_rel_end, results.baseline_rel_end_evt)

            reach_woi_rel_start=0
            if results.reach_woi_rel_start is not None:
                reach_woi_rel_start=results.reach_woi_rel_start/1000.0
            reach_woi_rel_end=0
            if results.reach_woi_rel_end is not None:
                reach_woi_rel_end=results.reach_woi_rel_end/1000.0
            reach_woi_rate = get_woi_firing_rate(unit_recording, trial_start_time, trial_events, results.reach_woi_rel_evt,
                reach_woi_rel_start, reach_woi_rel_end, results.reach_woi_rel_end_evt)

            hold_woi_rel_start=0
            if results.hold_woi_rel_start is not None:
                hold_woi_rel_start=results.hold_woi_rel_start/1000.0
            hold_woi_rel_end=0
            if results.hold_woi_rel_end is not None:
                hold_woi_rel_end=results.hold_woi_rel_end/1000.0
            hold_woi_rate = get_woi_firing_rate(unit_recording, trial_start_time, trial_events, results.hold_woi_rel_evt,
                hold_woi_rel_start, hold_woi_rel_end, results.hold_woi_rel_end_evt)

            if baseline_rate is not None and reach_woi_rate is not None and hold_woi_rate is not None:

                trial_ids.append(trial_idx+1)
                rates.append(baseline_rate)
                wois.append('baseline')

                trial_ids.append(trial_idx+1)
                rates.append(reach_woi_rate)
                wois.append('reach')

                trial_ids.append(trial_idx+1)
                rates.append(hold_woi_rate)
                wois.append('hold')

                all_rates['baseline'].append(baseline_rate)
                all_rates['reach'].append(reach_woi_rate)
                all_rates['hold'].append(hold_woi_rate)

        df= pd.DataFrame({
            'trial': pd.Series(trial_ids),
            'rates': pd.Series(rates),
            'woi': pd.Series(wois),
        })
        #df.to_csv(path_or_buf='/home/jbonaiuto/%s.csv' % trial_type)

        (anova_results,pairwise)=r_one_way_anova(df,"trial","rates","woi")

        print(anova_results)
        #anova_results=pandas2ri.ri2py_dataframe(anova_results)
        #print(anova_results)
        #pairwise=pandas2ri.ri2py_dataframe(pairwise)
        return anova_results,pairwise,all_rates
