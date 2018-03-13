from django.db import models
from model_utils.managers import InheritanceManager
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
import numpy as np
import os
from rpy2 import robjects
from sensorimotordb.models import UnitRecording, Condition, Unit, Event, RecordingTrial
from uscbp import settings
from rpy2.robjects import pandas2ri
pandas2ri.activate()
import pandas as pd
from rpy2.robjects.numpy2ri import numpy2ri

# Load R functions
r_source = robjects.r['source']
r_source(os.path.join(settings.PROJECT_PATH,'../sensorimotordb/analysis/kmeans_clustering.R'))
r_kmeans = robjects.globalenv['kmeans_clustering']
r_source(os.path.join(settings.PROJECT_PATH,'../sensorimotordb/analysis/classic_mds.R'))
r_classic_mds = robjects.globalenv['classic_mds']
r_source(os.path.join(settings.PROJECT_PATH,'../sensorimotordb/analysis/nonmetric_mds.R'))
r_nonmetric_mds = robjects.globalenv['nonmetric_mds']


class Analysis(models.Model):
    name=models.CharField(max_length=100, blank=False)
    description=models.TextField()
    objects = InheritanceManager()

    class Meta:
        app_label='sensorimotordb'

    def run(self, results, settings):
        pass


class ClassificationAnalysis(Analysis):
    script_name=models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        app_label='sensorimotordb'

    def run(self, results, analysis_settings):
        unit_ids=np.unique(UnitRecording.objects.filter(trial__condition__experiment=results.experiment).values_list('unit',
            flat=True))
        results.total_num_units=len(unit_ids)
        results.save()

        r_source(os.path.join(settings.MEDIA_ROOT,'scripts',self.script_name))
        r_classify_script = robjects.globalenv['classify_unit']


        unit_classifications={}
        for type in UnitClassificationType.objects.filter(analysis=self):
            unit_classifications[type.label]=UnitClassification(type=type, analysis_results=results)
            unit_classifications[type.label].save()

        for unit_id in unit_ids:
            unit=Unit.objects.get(id=unit_id)
            print('testing unit %d' % unit.id)

            unit_results=UnitAnalysisResults(analysis_results=results, unit=unit, results_text='')

            trial_ids = []
            rates = []
            spikes=[]
            factor_values={}

            condition_ids = []
            for factor in self.analysis_factors.all():
                if factor.type == 'condition':
                    for level in factor.factor_levels.all():
                        conditions = ClassificationAnalysisResultsLevelMapping.objects.get(level=level,
                                                                                           analysis_settings=analysis_settings).conditions.all()
                        for condition in conditions:
                            if not condition.id in condition_ids:
                                condition_ids.append(condition.id)
                factor_values[factor.name]=[]

            unit_recordings = UnitRecording.objects.filter(trial__condition__in=condition_ids,
                                                           unit=unit).select_related('trial')
            for trial_idx, unit_recording in enumerate(unit_recordings):
                trial_events = list(Event.objects.filter(trial=unit_recording.trial))
                trial_start_time = float(unit_recording.trial.start_time)
                trial_condition_id = unit_recording.trial.condition.id

                for factor in self.analysis_factors.all():
                    if factor.type == 'time window':
                        for level in factor.factor_levels.all():
                            level_settings = TimeWindowFactorLevelSettings.objects.get(level=level,
                                                                                       analysis_settings=analysis_settings)
                            rel_start = 0
                            if level_settings.rel_start is not None:
                                rel_start = level_settings.rel_start / 1000.0
                            rel_end = 0
                            if level_settings.rel_end is not None:
                                rel_end = level_settings.rel_end / 1000.0
                            rate = get_woi_firing_rate(unit_recording, trial_start_time, trial_events,
                                                       level_settings.rel_evt,
                                                       rel_start, rel_end, level_settings.rel_end_evt)
                            woi_spikes = get_woi_spikes(unit_recording, trial_start_time, trial_events,
                                                       level_settings.rel_evt,
                                                       rel_start, rel_end, level_settings.rel_end_evt)

                            factor_values[factor.name].append(level.value)
                            rates.append(rate)
                            spikes.append(woi_spikes)
                            trial_ids.append(trial_idx + 1)

                            for other_factor in self.analysis_factors.all():
                                if other_factor.type == 'condition':
                                    level_settings = ClassificationAnalysisResultsLevelMapping.objects.get(
                                        level__factor=other_factor, analysis_settings=analysis_settings,
                                        conditions__id__exact=trial_condition_id)
                                    factor_values[other_factor.name].append(level_settings.level.value)

            df = pd.DataFrame({
                'trial': pd.Series(trial_ids),
                'rate': pd.Series(rates),
                'spikes': pd.Series(spikes)
            })
            for factor_name,values in factor_values.iteritems():
                factor_name = factor_name.replace(' ', '_')
                df[factor_name]=pd.Series(values)

            df.to_csv('/home/bonaiuto/Dropbox/sensorimotordb/test.csv')

            (classification,stats) = r_classify_script(df)

            unit_results.results_text=stats[0]
            unit_results.save()

            unit_classifications[classification[0]].add_hierarchically(unit)


class AnalysisSettings(models.Model):
    analysis = models.ForeignKey('Analysis')
    objects = InheritanceManager()

    class Meta:
        app_label='sensorimotordb'


class ClassificationAnalysisSettings(AnalysisSettings):
    class Meta:
        app_label='sensorimotordb'


class Factor(models.Model):
    FACTOR_TYPES = (
        ('time window', 'time window'),
        ('condition', 'condition'),
    )
    analysis = models.ForeignKey('ClassificationAnalysis', related_name='analysis_factors')
    name=models.CharField(max_length=1000, blank=False)
    type = models.CharField(max_length=100, choices=FACTOR_TYPES)

    class Meta:
        app_label='sensorimotordb'


class FactorLevel(models.Model):
    factor=models.ForeignKey('Factor', related_name='factor_levels')
    value=models.CharField(max_length=1000, blank=False)

    class Meta:
        app_label='sensorimotordb'


class TimeWindowFactorLevelSettings(models.Model):
    analysis_settings = models.ForeignKey('ClassificationAnalysisSettings', related_name='time_window_factor_level_settings')
    level=models.ForeignKey('FactorLevel')
    rel_evt=models.CharField(max_length=1000, blank=False)
    rel_start=models.IntegerField(blank=True, null=True)
    rel_end=models.IntegerField(blank=True, null=True)
    rel_end_evt=models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        app_label='sensorimotordb'


class ClassificationAnalysisResultsLevelMapping(models.Model):
    level=models.ForeignKey('FactorLevel')
    analysis_settings = models.ForeignKey('ClassificationAnalysisSettings', related_name='level_mappings')
    conditions=models.ManyToManyField(Condition, related_name='classification_analysis_level_mapping_conditions')

    class Meta:
        app_label='sensorimotordb'


class AnalysisResults(models.Model):
    analysis = models.ForeignKey('Analysis')
    analysis_settings = models.ForeignKey('AnalysisSettings',null=True)
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
    spikes = None
    if len(rel_end_evt) == 0:
        woi_time_zero = trial_start_time
        found = True
        if not rel_evt == 'start':
            found = False
            for trial_evt in trial_events:
                if trial_evt.name == rel_evt:
                    woi_time_zero = float(trial_evt.time)
                    found = True
                    break
        if found:
            spikes = len(unit_recording.get_spikes_relative(woi_time_zero, [rel_start_ms, rel_end_ms]))
    else:
        # try:
        woi_time_start = trial_start_time
        found_start = True
        if not rel_evt == 'start':
            found_start = False
            for trial_evt in trial_events:
                if trial_evt.name == rel_evt:
                    woi_time_start = float(trial_evt.time)
                    found_start = True
                    break
        woi_time_end = trial_start_time
        found_end = True
        if not rel_end_evt == 'start':
            found_end = False
            for trial_evt in trial_events:
                if trial_evt.name == rel_end_evt:
                    woi_time_end = float(trial_evt.time)
                    found_end = True
                    break
        if found_start and found_end:
            spikes = len(unit_recording.get_spikes_fixed([woi_time_start, woi_time_end]))
    return spikes


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


class ClusterAnalysis(Analysis):
    MDS_TYPE_CHOICES = (
        ('classic', 'classic'),
        ('nonmetric', 'nonmetric'),
    )
    mds_type=models.CharField(max_length=100, choices=MDS_TYPE_CHOICES, null=True, blank=True)

    class Meta:
        app_label='sensorimotordb'

    def run(self, results, analysis_settings):
        unit_ids=np.unique(UnitRecording.objects.filter(trial__condition__experiment=results.experiment).values_list('unit',
            flat=True))
        condition_ids=np.unique(TimeWindowConditionSettings.objects.filter(analysis_settings=analysis_settings).values_list('condition', flat=True))

        rate_matrix=[]

        for unit_id in unit_ids:
            unit=Unit.objects.get(id=unit_id)

            unit_condition_rates={}
            unit_rate_matrix=[]

            rate_maxes=[]

            # For each unit - compute the average firing rate in each condition, aligned to rel event from settings
            for timewindow_settings in TimeWindowConditionSettings.objects.filter(analysis_settings=analysis_settings):

                # Histogram all spikes in all trials
                num_trials=RecordingTrial.objects.filter(condition=timewindow_settings.condition, unit_recordings__unit=unit).count()
                unit_recordings=UnitRecording.objects.filter(trial__condition=timewindow_settings.condition, unit=unit).select_related('trial')
                all_trial_spikes=[]
                all_baseline_spikes=[]
                for trial_idx,unit_recording in enumerate(unit_recordings):
                    trial_events=Event.objects.filter(trial=unit_recording.trial)
                    trial_start_time=float(unit_recording.trial.start_time)

                    trial_spikes = get_woi_spikes(unit_recording, trial_start_time, trial_events, timewindow_settings.rel_evt,
                        timewindow_settings.rel_start, timewindow_settings.rel_end, timewindow_settings.rel_end_evt)
                    baseline_spikes = get_woi_spikes(unit_recording, trial_start_time, trial_events, timewindow_settings.rel_evt,
                        timewindow_settings.baseline_start, timewindow_settings.baseline_end, timewindow_settings.baseline_end_evt)
                    all_trial_spikes.extend(trial_spikes)
                    all_baseline_spikes.extend(baseline_spikes)

                # Compute spike density
                bins=range(timewindow_settings.rel_start,timewindow_settings.rel_end,analysis_settings.bin_width)
                [hist,bin_edges]=np.histogram(all_trial_spikes, bins=bins)
                hist=hist/float(num_trials)/analysis_settings.bin_width/1000.0

                # Compute baseline spike density
                bins=range(timewindow_settings.baseline_start,timewindow_settings.baseline_end,analysis_settings.bin_width)
                [baseline_hist,bin_edges]=np.histogram(all_baseline_spikes, bins=bins)
                baseline_hist=baseline_hist/float(num_trials)/analysis_settings.bin_width/1000.0

                # Baseline correct
                hist=hist-np.mean(baseline_hist)

                # Convolve with Guassian
                variance=analysis_settings.kernel_width/analysis_settings.bin_width
                window=[]
                for i in range(-2*analysis_settings.bin_width,2*analysis_settings.bin_width+1):
                    window.append(np.exp(-(i**2)*(1/(2*(variance**2)))))
                windowSum=np.sum(window)
                for i in range(len(window)):
                    window[i]=window[i]*(1.0/windowSum)
                rate=np.convolve(hist, window)

                unit_condition_rates[timewindow_settings.condition.id]=rate
                rate_maxes.append(np.max(rate))

            # Normalize across conditions
            overall_max=np.max(rate_maxes)

            for condition_id in condition_ids:
                normalized_rate=unit_condition_rates[condition_id]/overall_max
                unit_rate_matrix.extend(normalized_rate)
            rate_matrix.append(unit_rate_matrix)

        rate_matrix=np.array(rate_matrix)
        rate_matrix=np.nan_to_num(rate_matrix)

        clusters=r_kmeans(numpy2ri(rate_matrix), analysis_settings.num_clusters)
        if self.mds_type=='classic':
            points=np.array(r_classic_mds(numpy2ri(rate_matrix), 2))
        elif self.mds_type=='nonmetric':
            points=np.array(r_nonmetric_mds(numpy2ri(rate_matrix), 2))

        results.save()

        for i in range(analysis_settings.num_clusters):
            cluster_neurons=np.where(np.array(clusters[0])==(i+1))[0]
            cluster_results=UnitCluster(analysis_results=results)
            cluster_results.save()
            for unit_idx in cluster_neurons:
                cluster_results.units.add(Unit.objects.get(id=unit_ids[unit_idx]))
            cluster_results.save()

            for unit_idx in cluster_neurons:
                cluster_projection=UnitClusterProjection(cluster=cluster_results,
                    unit=Unit.objects.get(id=unit_ids[unit_idx]), point_x=points[unit_idx,0], point_y=points[unit_idx,1])
                cluster_projection.save()


class ClusterAnalysisSettings(AnalysisSettings):
    num_clusters=models.IntegerField(blank=True, null=True)
    bin_width=models.IntegerField(blank=True, null=True)
    kernel_width=models.IntegerField(blank=True, null=True)

    class Meta:
        app_label='sensorimotordb'


class TimeWindowConditionSettings(models.Model):
    analysis_settings = models.ForeignKey('ClusterAnalysisSettings', related_name='time_window_condition_settings')
    condition=models.ForeignKey('Condition')
    rel_evt=models.CharField(max_length=100, blank=False)
    rel_start=models.IntegerField(blank=True, null=True)
    rel_end=models.IntegerField(blank=True, null=True)
    rel_end_evt=models.CharField(max_length=100, blank=True, null=True)
    baseline_evt=models.CharField(max_length=100, blank=False)
    baseline_start=models.IntegerField(blank=True, null=True)
    baseline_end=models.IntegerField(blank=True, null=True)
    baseline_end_evt=models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        app_label='sensorimotordb'


class ClusterAnalysisResults(AnalysisResults):
    class Meta:
        app_label='sensorimotordb'


class UnitCluster(models.Model):
    analysis_results=models.ForeignKey(ClusterAnalysisResults, related_name='unit_clusters')
    units=models.ManyToManyField(Unit)
    class Meta:
        app_label='sensorimotordb'


class UnitClusterProjection(models.Model):
    cluster=models.ForeignKey(UnitCluster, related_name='cluster_projections')
    unit=models.ForeignKey(Unit, related_name='cluster_projection')
    point_x=models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=6)
    point_y=models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=6)
    class Meta:
        app_label='sensorimotordb'