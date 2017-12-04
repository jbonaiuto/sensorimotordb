from django.db import models
from model_utils.managers import InheritanceManager
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
import numpy as np
import os
from rpy2 import robjects
from sensorimotordb.models import UnitRecording, Condition, Unit, Event
from uscbp import settings
from rpy2.robjects import pandas2ri
pandas2ri.activate()
import pandas as pd

# Load R functions
r_source = robjects.r['source']
r_source(os.path.join(settings.PROJECT_PATH,'../sensorimotordb/analysis/one_way_anova_repeated_measures.R'))
r_one_way_anova = robjects.globalenv['one_way_anova_repeated_measures']
r_source(os.path.join(settings.PROJECT_PATH,'../sensorimotordb/analysis/two_way_anova_repeated_measures.R'))
r_two_way_anova = robjects.globalenv['two_way_anova_repeated_measures']
r_source(os.path.join(settings.PROJECT_PATH,'../sensorimotordb/analysis/three_way_anova_repeated_measures.R'))
r_three_way_anova = robjects.globalenv['two_way_anova_repeated_measures']


class Analysis(models.Model):
    name=models.CharField(max_length=100, blank=False)
    description=models.TextField()
    objects = InheritanceManager()

    class Meta:
        app_label='sensorimotordb'

    def run(self, results, settings):
        pass


class ClassificationAnalysis(Analysis):
    MULT_COMP_CORRECTION_CHOICES = (
        ('tukey', 'tukey'),
        ('scheffe', 'scheffe'),
        ('sidak', 'sidak'),
        ('bonferroni', 'bonferroni'),
        ('dunnettx', 'dunnettx'),
        ('mvt', 'mvt'),
        ('none', 'none'),
        )

    multiple_comparison_correction=models.CharField(max_length=100, choices=MULT_COMP_CORRECTION_CHOICES, null=True, blank=True)

    class Meta:
        app_label='sensorimotordb'

    def run(self, results, analysis_settings):
        unit_ids=np.unique(UnitRecording.objects.filter(trial__condition__experiment=results.experiment).values_list('unit',
            flat=True))
        results.total_num_units=len(unit_ids)
        results.save()

        unit_classifications={}
        for type in UnitClassificationType.objects.filter(analysis=self):
            unit_classifications[type.label]=UnitClassification(type=type, analysis_results=results)
            unit_classifications[type.label].save()

        for unit_id in unit_ids:
            unit=Unit.objects.get(id=unit_id)
            print('testing unit %d' % unit.id)

            unit_results=UnitAnalysisResults(analysis_results=results, unit=unit, results_text='', pairwise_results_text='')
            all_anova_results={}
            for anova in self.analysis_anovas.all():
                try:
                    (results_text, pairwise_results_text, anova_results)=anova.run(analysis_settings, results, unit, self.multiple_comparison_correction)
                    print('anova %s:' % anova.name)
                    print(results_text)
                    print(pairwise_results_text)
                    unit_results.results_text='%s\n%s' % (unit_results.results_text, results_text)
                    unit_results.pairwise_results_text='%s\n%s' % (unit_results.pairwise_results_text, pairwise_results_text)
                    all_anova_results[anova.id]=anova_results
                except:
                    pass
            unit_results.save()

            classification_types=list(UnitClassificationType.objects.filter(analysis=self, children=None))
            # Need to order classification types so those with higher order interaction conditions come first
            classification_order=[]
            for classification_type in classification_types:
                order=0
                for condition in UnitClassificationCondition.objects.filter(classification_type=classification_type):
                    condition_order=0
                    for comparison in condition.comparisons.all():
                        if ANOVAEffect.objects.filter(id=comparison.id).exists():
                            effect=ANOVAEffect.objects.get(id=comparison.id)
                            condition_order += effect.factors.count() * 1000
                        elif ANOVAPairwiseComparison.objects.filter(id=comparison.id).exists():
                            condition_order += 1
                    if condition_order>order:
                        order=condition_order
                classification_order.append(order)
            sorted_classification_types=[x for _, x in sorted(zip(classification_order,classification_types), key=lambda pair: pair[0], reverse=True)]


            classified=False
            # Now classify - for each possible type
            for classification_type in sorted_classification_types:
                # Check if any of the conditions are true
                if not UnitClassificationCondition.objects.filter(classification_type=classification_type).order_by('id').exists():
                    print('classified as %s' % classification_type.label)
                    unit_classifications[classification_type.label].add_hierarchically(unit)
                    classified=True
                else:
                    classification_conditions=list(UnitClassificationCondition.objects.filter(classification_type=classification_type))
                    # Need to order classification types so those with higher order interaction conditions come first
                    classification_condition_order=[]
                    for classification_condition in classification_conditions:
                        order=0
                        for comparison in classification_condition.comparisons.all():
                            if ANOVAEffect.objects.filter(id=comparison.id).exists():
                                effect=ANOVAEffect.objects.get(id=comparison.id)
                                order += effect.factors.count() * 1000
                            elif ANOVAPairwiseComparison.objects.filter(id=comparison.id).exists():
                                order += 1
                        classification_condition_order.append(order)
                    sorted_classification_conditions=[x for _, x in sorted(zip(classification_condition_order,classification_conditions), key=lambda pair: pair[0], reverse=True)]
                    for condition in sorted_classification_conditions:
                        condition_true=condition.check_condition(all_anova_results)
                        if condition_true:
                            print('classified as %s' % classification_type.label)
                            unit_classifications[classification_type.label].add_hierarchically(unit)
                            classified=True
                            break
                if classified:
                    break


class AnalysisSettings(models.Model):
    analysis = models.ForeignKey('Analysis')
    objects = InheritanceManager()

    class Meta:
        app_label='sensorimotordb'


class ClassificationAnalysisSettings(AnalysisSettings):
    class Meta:
        app_label='sensorimotordb'


class TimeWindowFactorLevelSettings(models.Model):
    analysis_settings = models.ForeignKey('ClassificationAnalysisSettings', related_name='time_window_factor_level_settings')
    level=models.ForeignKey('ANOVAFactorLevel')
    rel_evt=models.CharField(max_length=1000, blank=False)
    rel_start=models.IntegerField(blank=True, null=True)
    rel_end=models.IntegerField(blank=True, null=True)
    rel_end_evt=models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        app_label='sensorimotordb'


class ClassificationAnalysisResultsLevelMapping(models.Model):
    level=models.ForeignKey('ANOVAFactorLevel')
    analysis_settings = models.ForeignKey('ClassificationAnalysisSettings', related_name='level_mappings')
    conditions=models.ManyToManyField(Condition, related_name='classification_analysis_level_mapping_conditions')

    class Meta:
        app_label='sensorimotordb'


class AnalysisResults(models.Model):
    analysis = models.ForeignKey('Analysis')
    analysis_settings = models.ForeignKey('AnalysisSettings')
    experiment = models.ForeignKey('Experiment')
    name=models.CharField(max_length=100, blank=False)
    description=models.TextField()
    date_run=models.DateTimeField(auto_now_add=True)
    objects = InheritanceManager()

    class Meta:
        app_label='sensorimotordb'


class ClassificationAnalysisResults(AnalysisResults):
    class Meta:
        app_label='sensorimotordb'


class UnitAnalysisResults(models.Model):
    analysis_results=models.ForeignKey('AnalysisResults', related_name='unit_analysis_results')
    unit=models.ForeignKey('Unit')
    results_text=models.TextField()
    pairwise_results_text=models.TextField()


    class Meta:
        app_label='sensorimotordb'


class ANOVA(models.Model):
    analysis=models.ForeignKey('ClassificationAnalysis', related_name='analysis_anovas')
    name=models.CharField(max_length=1000, blank=False)
    dependent_variable=models.CharField(max_length=1000, blank=False)

    class Meta:
        app_label='sensorimotordb'

    def run(self, analysis_settings, results, unit, multiple_comparison_correction):
        anova_results={}
        pairwise_results_text=''
        if self.anova_factors.count()==1:
            within_trial_factor=self.anova_factors.all()[0]
            trial_ids=[]
            rates=[]
            factor_values=[]
            all_rates={}
            for level in within_trial_factor.anova_factor_levels.all():
                all_rates[level.value]=[]

            unit_recordings=UnitRecording.objects.filter(trial__condition__experiment=results.experiment, unit=unit).select_related('trial')
            for trial_idx,unit_recording in enumerate(unit_recordings):
                trial_events=list(Event.objects.filter(trial=unit_recording.trial))
                trial_start_time=float(unit_recording.trial.start_time)
                for level in within_trial_factor.anova_factor_levels.all():
                    level_settings=TimeWindowFactorLevelSettings.objects.get(level=level, analysis_settings=analysis_settings)
                    rel_start=0
                    if level_settings.rel_start is not None:
                        rel_start=level_settings.rel_start/1000.0
                    rel_end=0
                    if level_settings.rel_end is not None:
                        rel_end=level_settings.rel_end/1000.0
                    rate = get_woi_firing_rate(unit_recording, trial_start_time, trial_events, level_settings.rel_evt,
                        rel_start, rel_end, level_settings.rel_end_evt)
                    trial_ids.append(trial_idx+1)
                    factor_values.append(level.value)
                    rates.append(rate)

                    all_rates[level.value].append(rate)

            within_trial_factor_name=within_trial_factor.name.replace(' ','_')
            df= pd.DataFrame({
                'trial': pd.Series(trial_ids),
                'rates': pd.Series(rates),
                within_trial_factor_name: pd.Series(factor_values),
                })
            #df.to_csv(path_or_buf='/home/jbonaiuto/%s.csv' % trial_type)
            (anova_results_trial, anova_results_within, within_trial_pairwise)=r_one_way_anova(df,"trial","rates",
                within_trial_factor_name, multiple_comparison_correction)

            anova_results={
                'anova_trial': pandas2ri.ri2py_dataframe(anova_results_trial[0]),
                'anova_within': pandas2ri.ri2py_dataframe(anova_results_within[0]),
                'within_trial_pairwise': pandas2ri.ri2py_dataframe(within_trial_pairwise),
                }
            pairwise_results_text='\n'.join(['<h2>%s</h2>' % self.name, str(anova_results['within_trial_pairwise'])])

        elif self.anova_factors.count()==2:
            trial_ids=[]
            between_trial_factor_values=[]
            between_trial_factor=None
            within_trial_factor_values=[]
            within_trial_factor=None
            rates=[]

            condition_ids=[]
            for factor in self.anova_factors.all():
                if factor.type=='condition':
                    for level in factor.anova_factor_levels.all():
                        conditions=ClassificationAnalysisResultsLevelMapping.objects.get(level=level, analysis_settings=analysis_settings).conditions.all()
                        for condition in conditions:
                            if not condition.id in condition_ids:
                                condition_ids.append(condition.id)
                    between_trial_factor=factor
                elif factor.type=='time window':
                    within_trial_factor=factor

            unit_recordings=UnitRecording.objects.filter(trial__condition__in=condition_ids, unit=unit).select_related('trial')
            for trial_idx,unit_recording in enumerate(unit_recordings):
                trial_events=list(Event.objects.filter(trial=unit_recording.trial))
                trial_start_time=float(unit_recording.trial.start_time)
                trial_condition_id=unit_recording.trial.condition.id

                for level in within_trial_factor.anova_factor_levels.all():
                    level_settings=TimeWindowFactorLevelSettings.objects.get(level=level, analysis_settings=analysis_settings)
                    rel_start=0
                    if level_settings.rel_start is not None:
                        rel_start=level_settings.rel_start/1000.0
                    rel_end=0
                    if level_settings.rel_end is not None:
                        rel_end=level_settings.rel_end/1000.0
                    rate = get_woi_firing_rate(unit_recording, trial_start_time, trial_events, level_settings.rel_evt,
                        rel_start, rel_end, level_settings.rel_end_evt)
                    within_trial_factor_values.append(level.value)
                    rates.append(rate)
                    trial_ids.append(trial_idx+1)

                    level_settings=ClassificationAnalysisResultsLevelMapping.objects.get(level__factor=between_trial_factor, analysis_settings=analysis_settings, conditions__id__exact=trial_condition_id)
                    between_trial_factor_values.append(level_settings.level.value)

            within_trial_factor_name=within_trial_factor.name.replace(' ','_')
            between_trial_factor_name=between_trial_factor.name.replace(' ','_')

            df= pd.DataFrame({
                'trial': pd.Series(trial_ids),
                within_trial_factor_name: pd.Series(within_trial_factor_values),
                between_trial_factor_name: pd.Series(between_trial_factor_values),
                'rate': pd.Series(rates)
            })

            #df=df.set_index(['trial'])
            #experiment_id=results.experiment.id
            #df.to_csv(path_or_buf='/home/jbonaiuto/experiment_%d.penetration_%s_unit_%s.csv' % (experiment_id, unit.penetration.label, unit.label))
            (anova_results_trial, anova_results_within, twoway_pairwise_factor1, twoway_pairwise_factor2, within_trial_pairwise, between_trial_pairwise)=r_two_way_anova(df,"trial",
                "rate",within_trial_factor_name,between_trial_factor_name, multiple_comparison_correction)

            anova_results={
                'anova_trial': pandas2ri.ri2py_dataframe(anova_results_trial[0]),
                'anova_within': pandas2ri.ri2py_dataframe(anova_results_within[0]),
                'twoway_pairwise_factor1': pandas2ri.ri2py_dataframe(twoway_pairwise_factor1),
                'twoway_pairwise_factor2': pandas2ri.ri2py_dataframe(twoway_pairwise_factor2),
                'within_trial_pairwise': pandas2ri.ri2py_dataframe(within_trial_pairwise),
                'between_trial_pairwise': pandas2ri.ri2py_dataframe(between_trial_pairwise),
                }
            pairwise_results_text='\n'.join(['<h2>%s</h2>' % self.name, str(anova_results['twoway_pairwise_factor1']),
                                             str(anova_results['twoway_pairwise_factor2']),
                                             str(anova_results['within_trial_pairwise']),
                                             str(anova_results['between_trial_pairwise'])])

        elif self.anova_factors.count()==3:
            trial_ids=[]
            between_trial_factor_values={}
            between_trial_factors=[]
            within_trial_factor_values=[]
            within_trial_factor=None
            rates=[]

            condition_ids=[]
            for factor in self.anova_factors.all().order_by('id'):
                if factor.type=='condition':
                    for level in factor.anova_factor_levels.all():
                        conditions=ClassificationAnalysisResultsLevelMapping.objects.get(level=level, analysis_settings=analysis_settings).conditions.all()
                        for condition in conditions:
                            if not condition.id in condition_ids:
                                condition_ids.append(condition.id)
                    between_trial_factors.append(factor)
                    between_trial_factor_values[factor.name.replace(' ','_')]=[]
                elif factor.type=='time window':
                    within_trial_factor=factor

            unit_recordings=UnitRecording.objects.filter(trial__condition__in=condition_ids, unit=unit).select_related('trial')
            for trial_idx,unit_recording in enumerate(unit_recordings):
                trial_events=list(Event.objects.filter(trial=unit_recording.trial))
                trial_start_time=float(unit_recording.trial.start_time)
                trial_condition_id=unit_recording.trial.condition.id

                for level in within_trial_factor.anova_factor_levels.all():
                    level_settings=TimeWindowFactorLevelSettings.objects.get(level=level, analysis_settings=analysis_settings)
                    rel_start=0
                    if level_settings.rel_start is not None:
                        rel_start=level_settings.rel_start/1000.0
                    rel_end=0
                    if level_settings.rel_end is not None:
                        rel_end=level_settings.rel_end/1000.0
                    rate = get_woi_firing_rate(unit_recording, trial_start_time, trial_events, level_settings.rel_evt,
                        rel_start, rel_end, level_settings.rel_end_evt)
                    within_trial_factor_values.append(level.value)
                    rates.append(rate)
                    trial_ids.append(trial_idx+1)

                    for between_trial_factor in between_trial_factors:
                        level_settings=ClassificationAnalysisResultsLevelMapping.objects.get(level__factor=between_trial_factor, analysis_settings=analysis_settings, conditions__id__exact=trial_condition_id)
                        between_trial_factor_values[between_trial_factor.name.replace(' ','_')].append(level_settings.level.value)

            within_trial_factor_name=within_trial_factor.name.replace(' ','_')
            df= pd.DataFrame({
                'trial': pd.Series(trial_ids),
                within_trial_factor_name: pd.Series(within_trial_factor_values),
                'rate': pd.Series(rates)
            })
            for between_trial_factor in between_trial_factors:
                df[between_trial_factor.name.replace(' ','_')]=pd.Series(between_trial_factor_values[between_trial_factor.name])

            #df=df.set_index(['trial'])

            (anova_results_trial, anova_results_within, threeway_pairwise, within_trial_between_trial1_pairwise,
             within_trial_between_trial2_pairwise, between_trial1_between_trial2_pairwise, within_trial_pairwise,
             between_trial1_pairwise, between_trial2_pairwise)=r_three_way_anova(df,"trial",
                "rate",within_trial_factor_name,between_trial_factors[0].name.replace(' ','_'),
                between_trial_factors[1].name.replace(' ','_'), multiple_comparison_correction)

            anova_results={
                'anova_trial': pandas2ri.ri2py_dataframe(anova_results_trial[0]),
                'anova_within': pandas2ri.ri2py_dataframe(anova_results_within[0]),
                'threeway_pairwise': pandas2ri.ri2py_dataframe(threeway_pairwise),
                'within_trial_between_trial1_pairwise': pandas2ri.ri2py_dataframe(within_trial_between_trial1_pairwise),
                'within_trial_between_trial2_pairwise': pandas2ri.ri2py_dataframe(within_trial_between_trial2_pairwise),
                'between_trial1_between_trial2_pairwise': pandas2ri.ri2py_dataframe(between_trial1_between_trial2_pairwise),
                'within_trial_pairwise': pandas2ri.ri2py_dataframe(within_trial_pairwise),
                'between_trial1_pairwise': pandas2ri.ri2py_dataframe(between_trial1_pairwise),
                'between_trial2_pairwise': pandas2ri.ri2py_dataframe(between_trial2_pairwise),
                }
            pairwise_results_text='\n'.join(['<h2>%s</h2>' % self.name, str(anova_results['threeway_pairwise']),
                                             str(anova_results['within_trial_between_trial1_pairwise']),
                                             str(anova_results['within_trial_between_trial2_pairwise']),
                                             str(anova_results['between_trial1_between_trial2_pairwise']),
                                             str(anova_results['within_trial_pairwise']),
                                             str(anova_results['between_trial1_pairwise']),
                                             str(anova_results['between_trial2_pairwise'])])

        results_text='<h2>%s</h2>\n%s\n%s' % (self.name, str(anova_results['anova_trial']),str(anova_results['anova_within']))
        return results_text, pairwise_results_text, anova_results

class ANOVAFactor(models.Model):
    ANOVA_FACTOR_TYPES = (
        ('time window', 'time window'),
        ('condition', 'condition'),
    )
    anova=models.ForeignKey('ANOVA', related_name='anova_factors')
    name=models.CharField(max_length=1000, blank=False)
    type = models.CharField(max_length=100, choices=ANOVA_FACTOR_TYPES)

    class Meta:
        app_label='sensorimotordb'


class ANOVAFactorLevel(models.Model):
    factor=models.ForeignKey('ANOVAFactor', related_name='anova_factor_levels')
    value=models.CharField(max_length=1000, blank=False)

    class Meta:
        app_label='sensorimotordb'


class ANOVAComparison(models.Model):
    anova=models.ForeignKey('ANOVA', related_name='anova_comparisons')
    objects = InheritanceManager()

    def check_results(self, anova_results):
        pass

    class Meta:
        app_label='sensorimotordb'


class ANOVAEffect(ANOVAComparison):
    factors=models.ManyToManyField('ANOVAFactor', related_name='anova_factor_interaction')

    def __unicode__(self):
        s=''
        for factor in self.factors.all():
            if len(s):
                s='%s x %s' % (s,factor.name)
            else:
                s=factor.name
        return s

    def check_results(self, anova_results):
        if self.anova.id in anova_results:
            if self.factors.count()==1:
                for idx in range(anova_results[self.anova.id]['anova_within'].axes[0].size):
                    if anova_results[self.anova.id]['anova_within'].axes[0][idx].strip()==self.factors.all()[0].name:
                        return anova_results[self.anova.id]['anova_within']['Pr(>F)'][idx]<0.05
                return False
            elif self.factors.count()==2:
                for idx in range(anova_results[self.anova.id]['anova_within'].axes[0].size):
                    row_name=anova_results[self.anova.id]['anova_within'].axes[0][idx].strip()
                    if row_name=='%s:%s' % (self.factors.all()[0].name,self.factors.all()[1].name) or row_name=='%s:%s' % (self.factors.all()[1].name,self.factors.all()[0].name):
                        return anova_results[self.anova.id]['anova_within']['Pr(>F)'][idx]<0.05
                return False
            elif self.factors.count()==3:
                pass
        return False

    class Meta:
        app_label='sensorimotordb'


PAIRWISE_RELATIONSHIP_CHOICES = (
    ('gt', '>'),
    ('lt', '<'),
    )


class ANOVAPairwiseComparison(ANOVAComparison):
    relationship = models.CharField(max_length=100, choices=PAIRWISE_RELATIONSHIP_CHOICES)
    objects = InheritanceManager()

    class Meta:
        app_label='sensorimotordb'


class ANOVAOneWayPairwiseComparison(ANOVAPairwiseComparison):
    factor=models.ForeignKey('ANOVAFactor', related_name='anova_oneway_pairwise')
    level1=models.ForeignKey('ANOVAFactorLevel', related_name='anova_oneway_pairwise_level1')
    level2=models.ForeignKey('ANOVAFactorLevel', related_name='anova_oneway_pairwise_level2')

    def __unicode__(self):
        return '%s: %s&%s;%s' % (self.factor.name, self.level1.value, self.relationship, self.level2.value)

    def check_results(self, anova_results):
        if self.anova.id in anova_results:
            for row_idx in range(anova_results[self.anova.id]['within_trial_pairwise'].shape[0]):
                contrast=anova_results[self.anova.id]['within_trial_pairwise'].contrast[row_idx+1]
                levels=contrast.split(' - ')
                level_diff=anova_results[self.anova.id]['within_trial_pairwise']['estimate'][row_idx+1]
                p_val=anova_results[self.anova.id]['within_trial_pairwise']['p.value'][row_idx+1]
                if p_val<0.05 and ((levels[0]==self.level1.value and levels[1]==self.level2.value) or (levels[0]==self.level2.value and levels[1]==self.level1.value)):
                    if levels[0]==self.level2.value and levels[1]==self.level1.value:
                        level_diff*=-1
                    if (level_diff>0 and self.relationship=='gt') or (level_diff<0 and self.relationship=='lt'):
                        return True
        return False


    class Meta:
        app_label='sensorimotordb'


class ANOVATwoWayPairwiseComparison(ANOVAPairwiseComparison):
    factor1=models.ForeignKey('ANOVAFactor', related_name='anova_twoway_pairwise_factor1')
    factor1_level=models.ForeignKey('ANOVAFactorLevel', related_name='anova_twoway_pairwise_factor1_level')
    factor2=models.ForeignKey('ANOVAFactor', related_name='anova_twoway_pairwise_factor2')
    factor2_level1=models.ForeignKey('ANOVAFactorLevel', related_name='anova_twoway_pairwise_factor2_level1')
    factor2_level2=models.ForeignKey('ANOVAFactorLevel', related_name='anova_twoway_pairwise_factor2_level2')

    def __unicode__(self):
        return '%s=%s, %s: %s&%s;%s' % (self.factor1.name, self.factor1_level.value, self.factor2.name, self.factor2_level1.value, self.relationship, self.factor2_level2.value);

    def check_results(self, anova_results):
        if self.anova.id in anova_results:
            pairwise_results=None
            if anova_results[self.anova.id]['twoway_pairwise_factor1'].columns[1]==self.factor1.name:
                pairwise_results=anova_results[self.anova.id]['twoway_pairwise_factor1']
            elif anova_results[self.anova.id]['twoway_pairwise_factor2'].columns[1]==self.factor1.name:
                pairwise_results=anova_results[self.anova.id]['twoway_pairwise_factor2']
            for row_idx in range(pairwise_results.shape[0]):
                contrast=pairwise_results.contrast[row_idx+1]
                levels=contrast.split(' - ')
                level_diff=pairwise_results['estimate'][row_idx+1]
                p_val=pairwise_results['p.value'][row_idx+1]
                if p_val<0.05 and pairwise_results[self.factor1.name][row_idx+1]==self.factor1_level.value:
                    if (levels[0]==self.factor2_level1.value and levels[1]==self.factor2_level2.value) or (levels[0]==self.factor2_level2.value and levels[1]==self.factor2_level1.value):
                        if levels[0]==self.factor2_level2.value and levels[1]==self.factor2_level1.value:
                            level_diff*=-1
                        if (level_diff>0 and self.relationship=='gt') or (level_diff<0 and self.relationship=='lt'):
                            return True
        return False

    class Meta:
        app_label='sensorimotordb'


class ANOVAThreeWayPairwiseComparison(ANOVAPairwiseComparison):
    factor1=models.ForeignKey('ANOVAFactor', related_name='anova_threeway_pairwise_factor1')
    factor1_level=models.ForeignKey('ANOVAFactorLevel', related_name='anova_threeway_pairwise_factor1_level')
    factor2=models.ForeignKey('ANOVAFactor', related_name='anova_threeway_pairwise_factor2')
    factor2_level=models.ForeignKey('ANOVAFactorLevel', related_name='anova_threeway_pairwise_factor2_level')
    factor3=models.ForeignKey('ANOVAFactor', related_name='anova_threeway_pairwise_factor3')
    factor3_level1=models.ForeignKey('ANOVAFactorLevel', related_name='anova_oneway_pairwise_factor3_level1')
    factor3_level2=models.ForeignKey('ANOVAFactorLevel', related_name='anova_oneway_pairwise_factor3_level2')

    def __unicode__(self):
        return '%s=%s, %s=%s, %s: %s&%s;%s' % (self.factor1.name, self.factor1_level.value, self.factor2.name, self.factor2_level.value, self.factor3.name, self.factor3_level1.value, self.relationship, self.factor3_level2.value);

    def check_results(self, anova_results):
       pass

    class Meta:
        app_label='sensorimotordb'


class UnitClassificationCondition(models.Model):
    classification_type=models.ForeignKey('UnitClassificationType', related_name='unit_classification_type_conditions')
    comparisons=models.ManyToManyField('ANOVAComparison', related_name='anova_comparison_conditions')

    def check_condition(self, all_anova_results):
        all_true=True
        for comparison in self.comparisons.all().select_subclasses():
            if not comparison.check_results(all_anova_results):
                all_true=False
                break
        return all_true

    class Meta:
        app_label='sensorimotordb'

class UnitClassificationType(MPTTModel,models.Model):
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    analysis=models.ForeignKey(ClassificationAnalysis, related_name='unit_classification_types')
    label=models.CharField(max_length=1000, blank=False)

    class Meta:
        app_label='sensorimotordb'


class UnitClassification(models.Model):
    analysis_results=models.ForeignKey(ClassificationAnalysisResults, related_name='unit_classifications')
    type=models.ForeignKey(UnitClassificationType)
    units=models.ManyToManyField(Unit)

    def add_hierarchically(self, unit):
        self.units.add(unit)
        if self.type.parent is not None:
            parent_classification=UnitClassification.objects.get(analysis_results=self.analysis_results, type=self.type.parent)
            parent_classification.add_hierarchically(unit)

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
        #try:
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
        #except:
        #    print('Exception')
        #    return None
    return rate


