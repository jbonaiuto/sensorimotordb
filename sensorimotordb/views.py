import json
import shutil
from django.db.models import Q
from h5py import h5
from wsgiref.util import FileWrapper
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.views.generic import DetailView, TemplateView, CreateView, UpdateView, View
from django.views.generic.detail import SingleObjectMixin, BaseDetailView
from django.views.generic.edit import ModelFormMixin
import h5py
from neo import io
from haystack.management.commands import rebuild_index
import os
from registration.forms import User
from tastypie.models import ApiKey
from sensorimotordb.forms import ExperimentExportRequestForm, ExperimentExportRequestDenyForm, ExperimentExportRequestApproveForm, UserProfileForm, VisuomotorClassificationAnalysisResultsForm, ExperimentImportForm, GraspConditionFormSet, ExperimentForm, \
    MirrorTypeClassificationAnalysisResultsForm
from sensorimotordb.models import Condition, GraspObservationCondition, GraspPerformanceCondition, Unit, Experiment, ExperimentExportRequest, ConditionVideoEvent, AnalysisResults, VisuomotorClassificationAnalysisResults, Factor, VisuomotorClassificationAnalysis, Event, AnalysisResultsLevelMapping, Level, UnitClassification, VisuomotorClassificationUnitAnalysisResults, GraspCondition, Species, BrainRegion, RecordingTrial, UnitRecording, \
    MirrorTypeClassificationAnalysisResults, MirrorTypeClassificationUnitAnalysisResults, \
    MirrorTypeClassificationAnalysis, UnitAnalysisResults
from uscbp import settings
from uscbp.settings import MEDIA_ROOT, PROJECT_PATH

class LoginRequiredMixin(object):
    redirect_field_name = 'next'
    login_url = '/accounts/login/'

    def dispatch(self, request, *args, **kwargs):
        return login_required(redirect_field_name=self.redirect_field_name,
            login_url=self.login_url)(
            super(LoginRequiredMixin, self).dispatch
        )(request, *args, **kwargs)


class JSONResponseMixin(object):

    def post(self, request, *args, **kwargs):
        self.request=request
        return self.render_to_response(self.get_context_data(**kwargs))

    def render_to_response(self, context):
        "Returns a JSON response containing 'context' as payload"
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        "Construct an `HttpResponse` object."
        return HttpResponse(content,
            content_type='application/json',
            **httpresponse_kwargs)

    def convert_context_to_json(self, context):
        "Convert the context dictionary into a JSON object"
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or querysets
        # -- can be serialized as JSON.
        return json.dumps(context)


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'sensorimotordb/index.html'


class ExperimentImportView(LoginRequiredMixin, UpdateView):
    model=Experiment
    form_class = ExperimentImportForm
    template_name = 'sensorimotordb/experiment/experiment_import_final_detail.html'

    def get_context_data(self, **kwargs):
        context = super(ExperimentImportView,self).get_context_data(**kwargs)
        context['condition_formset']=GraspConditionFormSet(self.request.POST or None, instance=self.object,
            queryset=GraspCondition.objects.filter(experiment=self.object).order_by('id'), prefix='condition')
        if self.request.method.lower()=='get':
            init_data=[]
            for condition in GraspCondition.objects.filter(experiment=self.object).order_by('id'):
                parts=condition.name.split(',')
                epochtype_part=parts[0]
                epoch_type=epochtype_part.split(' ')[2]
                ttype_part=parts[1]
                trial_type=ttype_part.split(' ')[3]
                obj_part=parts[2]
                object=obj_part.split(' ')[2]
                init_data.append({
                    'id':condition.id,
                    'condition_ptr':condition.id,
                    'name':condition.name,
                    'epoch_type':epoch_type,
                    'trial_type':trial_type,
                    'object':object,
                    'hand_visible':True,
                    'object_visible':True,
                    'demonstrator_species':Species.objects.get(genus_name='Homo',species_name='sapiens'),
                    'demonstration_type':'live',
                    'viewing_angle':180.0,
                    'whole_body_visible':True
                })
            for subform,data in zip(context['condition_formset'].forms,init_data):
                subform.initial=data

        #context['event_types']=self.request.GET['event_types'].split(',')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        condition_formset = context['condition_formset']

        self.object=form.save(commit=False)
        self.object.last_modified_by=self.request.user
        self.object.save()

        condition_map={}
        if condition_formset.is_valid():
            for condition_form in condition_formset.forms:
                grasp_condition=condition_form.save(commit=False)
                print(grasp_condition.type)
                if grasp_condition.type=='grasp_performance':
                    grasp_perf_cond=GraspPerformanceCondition(graspcondition_ptr=grasp_condition)
                    grasp_perf_cond.__dict__.update(grasp_condition.__dict__)
                    grasp_perf_cond.hand_visible=condition_form.cleaned_data['hand_visible']
                    grasp_perf_cond.object_visible=condition_form.cleaned_data['object_visible']
                    grasp_perf_cond.save()
                    print(grasp_perf_cond.name)
                elif grasp_condition.type=='grasp_observation':
                    grasp_obs_cond=GraspObservationCondition(graspcondition_ptr=grasp_condition)
                    grasp_obs_cond.__dict__.update(grasp_condition.__dict__)
                    grasp_obs_cond.demonstrator_species=condition_form.cleaned_data['demonstrator_species']
                    grasp_obs_cond.demonstration_type=condition_form.cleaned_data['demonstration_type']
                    grasp_obs_cond.viewing_angle=condition_form.cleaned_data['viewing_angle']
                    grasp_obs_cond.whole_body_visible=condition_form.cleaned_data['whole_body_visible']
                    grasp_obs_cond.save()
                    print(grasp_obs_cond.name)

                condition_map[(condition_form.cleaned_data['epoch_type'],condition_form.cleaned_data['trial_type'],condition_form.cleaned_data['object'])]=grasp_condition
        else:
            return self.form_invalid(form)
        self.import_bonini_data(condition_map)
        try:
            rebuild_index.Command().handle(interactive=False)
        except:
            pass
        return redirect('/sensorimotordb/experiment/%d/' % self.object.id)

    def import_bonini_data(self, condition_map):
        event_map={
            'ev_01_LightON_visualCOR_RNG':('lon','light on'),
            'ev_02_LightON_motorCORc1_RNG':('lon','light on'),
            'ev_03_Pull_CORc1_RNG': ('do','object displacement onset'),
            'ev_04_Pull_CORc2_RNG': ('do','object displacement onset'),
            'ev_05_LightON_visualCOR_SML': ('lon','light on'),
            'ev_06_LightON_motorCORc1_SML': ('lon','light on'),
            'ev_07_Pull_CORc1_SML': ('do','object displacement onset'),
            'ev_08_Pull_CORc2_SML': ('do','object displacement onset'),
            'ev_09_LightON_visualCOR_BIG': ('lon','light on'),
            'ev_10_LightON_motorCORc1_BIG': ('lon','light on'),
            'ev_11_Pull_CORc1_BIG': ('do','object displacement onset'),
            'ev_12_Pull_CORc2_BIG': ('do','object displacement onset'),
            'LightON_motorCORc2_RNG': ('lon','light on'),
            'LightON_motorCORc2_SML': ('lon','light on'),
            'LightON_motorCORc2_BIG': ('lon','light on'),
            # Object contact events are not reliable
            #        'EVT02': ('co','object contact'),
            #        'EVT03': ('co','object contact'),
            #        'EVT04': ('co','object contact'),
            'EVT07': ('rew','reward onset'),
            'EVT09': ('fix','fixation onset'),
            'EVT17': ('mo','movement onset'),
            'EVT23': ('loff','light off'),
            'EVT28': ('mo','movement onset'),
        }
        pretrial_padding=0.25
        posttrial_padding=0.25

        data_path=os.path.join(settings.MEDIA_ROOT,'experiment_data','%s' % self.object.id)
        for nex_idx, nex_file in enumerate(os.listdir(data_path)):
            r=io.NeuroExplorerIO(filename=os.path.join(data_path, nex_file))
            block=r.read(cascade=True, lazy=False)[0]
            for seg_idx, seg in enumerate(block.segments):
                print('importing segment %d' % seg_idx)
                events={}
                for idx,event_array in enumerate(seg.eventarrays):
                    events[event_array.annotations['channel_name']]=idx

                units=[]
                for unit_idx,st in enumerate(seg.spiketrains):
                    print('importing unit %s' % st.name)
                    unit=Unit()
                    area='F5'
                    region=BrainRegion.objects.filter(Q(Q(name=area) | Q(abbreviation=area)))
                    unit.area=region[0]
                    unit.type='UID'
                    unit.save()
                    units.append(unit)

                # Iterate through epochs:
                for epoch_idx, epocharray in enumerate(seg.epocharrays):
                    print('importing epoch %d' % epoch_idx)
                    epoch_type=epocharray.annotations['channel_name']
                    if not epoch_type=='AllFile':
                        trial_start_times=[]
                        trial_end_times=[]

                        epoch_start=epocharray.times[0]
                        epoch_end=epoch_start+epocharray.durations[0]

                        # nogo ring trials
                        for time_idx,time in enumerate(seg.eventarrays[events['ev_01_LightON_visualCOR_RNG']].times):
                            if epoch_start <= time <= epoch_end:
                                nearest_fixation=find_nearest_event_before(time, seg.eventarrays[events['EVT09']],
                                    epoch_start, epoch_end)
                                nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                    epoch_start, epoch_end)
                                if nearest_fixation is not None and time.rescale('s').magnitude.item(0)-nearest_fixation<1.5 and nearest_reward is not None:
                                    trial_start_times.append(nearest_fixation-pretrial_padding)
                                    trial_end_times.append(nearest_reward+posttrial_padding)

                        # Grasp in light ring trials - look for correctly performed (pull event)
                        for time in seg.eventarrays[events['ev_03_Pull_CORc1_RNG']].times:
                            if epoch_start <= time <= epoch_end:
                                nearest_light_on=find_nearest_event_before(time,
                                    seg.eventarrays[events['ev_02_LightON_motorCORc1_RNG']], epoch_start, epoch_end)
                                if time.rescale('s').magnitude.item(0)-nearest_light_on<2:
                                    nearest_fixation=find_nearest_event_before(nearest_light_on,
                                        seg.eventarrays[events['EVT09']], epoch_start, epoch_end)
                                    nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                        epoch_start, epoch_end)
                                    if nearest_fixation is not None and nearest_light_on-nearest_fixation<1.5 and nearest_reward is not None:
                                        trial_start_times.append(nearest_fixation-pretrial_padding)
                                        trial_end_times.append(nearest_reward+posttrial_padding)

                        # Grasp in dark ring trials - look for correctly performed (pull event)
                        for time in seg.eventarrays[events['ev_04_Pull_CORc2_RNG']].times:
                            if epoch_start <= time <= epoch_end:
                                nearest_light_on=find_nearest_event_before(time,
                                    seg.eventarrays[events['LightON_motorCORc2_RNG']], epoch_start, epoch_end)
                                if time.rescale('s').magnitude.item(0)-nearest_light_on<2:
                                    nearest_fixation=find_nearest_event_before(nearest_light_on, seg.eventarrays[events['EVT09']],
                                        epoch_start, epoch_end)
                                    nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                        epoch_start, epoch_end)
                                    if nearest_fixation is not None and nearest_light_on-nearest_fixation<1.5 and nearest_reward is not None:
                                        trial_start_times.append(nearest_fixation-pretrial_padding)
                                        trial_end_times.append(nearest_reward+posttrial_padding)

                        # nogo small cone trials
                        for time_idx,time in enumerate(seg.eventarrays[events['ev_05_LightON_visualCOR_SML']].times):
                            if epoch_start <= time <= epoch_end:
                                nearest_fixation=find_nearest_event_before(time, seg.eventarrays[events['EVT09']],
                                    epoch_start, epoch_end)
                                nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                    epoch_start, epoch_end)
                                if nearest_fixation is not None and time.rescale('s').magnitude.item(0)-nearest_fixation<1.5 and nearest_reward is not None:
                                    trial_start_times.append(nearest_fixation-pretrial_padding)
                                    trial_end_times.append(nearest_reward+posttrial_padding)

                        # Grasp in light small cone trials - look for correctly performed (pull event)
                        for time in seg.eventarrays[events['ev_07_Pull_CORc1_SML']].times:
                            if epoch_start <= time <= epoch_end:
                                nearest_light_on=find_nearest_event_before(time,
                                    seg.eventarrays[events['ev_06_LightON_motorCORc1_SML']], epoch_start, epoch_end)
                                if time.rescale('s').magnitude.item(0)-nearest_light_on<2:
                                    nearest_fixation=find_nearest_event_before(nearest_light_on, seg.eventarrays[events['EVT09']],
                                        epoch_start, epoch_end)
                                    nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                        epoch_start, epoch_end)
                                    if nearest_fixation is not None and nearest_light_on-nearest_fixation<1.5 and nearest_reward is not None:
                                        trial_start_times.append(nearest_fixation-pretrial_padding)
                                        trial_end_times.append(nearest_reward+posttrial_padding)

                        # Grasp in dark small cone trials - look for correctly performed (pull event)
                        for time in seg.eventarrays[events['ev_08_Pull_CORc2_SML']].times:
                            if epoch_start <= time <= epoch_end:
                                nearest_light_on=find_nearest_event_before(time,
                                    seg.eventarrays[events['LightON_motorCORc2_SML']], epoch_start, epoch_end)
                                if time.rescale('s').magnitude.item(0)-nearest_light_on<2:
                                    nearest_fixation=find_nearest_event_before(nearest_light_on, seg.eventarrays[events['EVT09']],
                                        epoch_start, epoch_end)
                                    nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                        epoch_start, epoch_end)
                                    if nearest_fixation is not None and nearest_light_on-nearest_fixation<1.5 and nearest_reward is not None:
                                        trial_start_times.append(nearest_fixation-pretrial_padding)
                                        trial_end_times.append(nearest_reward+posttrial_padding)

                        # nogo large cone trials
                        for time_idx,time in enumerate(seg.eventarrays[events['ev_09_LightON_visualCOR_BIG']].times):
                            if epoch_start <= time <= epoch_end:
                                nearest_fixation=find_nearest_event_before(time, seg.eventarrays[events['EVT09']],
                                    epoch_start, epoch_end)
                                nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                    epoch_start, epoch_end)
                                if nearest_fixation is not None and time.rescale('s').magnitude.item(0)-nearest_fixation<1.5 and nearest_reward is not None:
                                    trial_start_times.append(nearest_fixation-pretrial_padding)
                                    trial_end_times.append(nearest_reward+posttrial_padding)

                        # Grasp in light large cone trials - look for correctly performed (pull event)
                        for time in seg.eventarrays[events['ev_11_Pull_CORc1_BIG']].times:
                            if epoch_start <= time <= epoch_end:
                                nearest_light_on=find_nearest_event_before(time,
                                    seg.eventarrays[events['ev_10_LightON_motorCORc1_BIG']], epoch_start, epoch_end)
                                if time.rescale('s').magnitude.item(0)-nearest_light_on<2:
                                    nearest_fixation=find_nearest_event_before(nearest_light_on, seg.eventarrays[events['EVT09']],
                                        epoch_start, epoch_end)
                                    nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                        epoch_start, epoch_end)
                                    if nearest_fixation is not None and nearest_light_on-nearest_fixation<1.5 and nearest_reward is not None:
                                        trial_start_times.append(nearest_fixation-pretrial_padding)
                                        trial_end_times.append(nearest_reward+posttrial_padding)

                        # Grasp in dark large cone trials - look for correctly performed (pull event)
                        for time in seg.eventarrays[events['ev_12_Pull_CORc2_BIG']].times:
                            if epoch_start <= time <= epoch_end:
                                nearest_light_on=find_nearest_event_before(time,
                                    seg.eventarrays[events['LightON_motorCORc2_BIG']], epoch_start, epoch_end)
                                if time.rescale('s').magnitude.item(0)-nearest_light_on<2:
                                    nearest_fixation=find_nearest_event_before(nearest_light_on, seg.eventarrays[events['EVT09']],
                                        epoch_start, epoch_end)
                                    nearest_reward=find_nearest_event_after(time, seg.eventarrays[events['EVT07']],
                                        epoch_start, epoch_end)
                                    if nearest_fixation is not None and nearest_light_on-nearest_fixation<1.5 and nearest_reward is not None:
                                        trial_start_times.append(nearest_fixation-pretrial_padding)
                                        trial_end_times.append(nearest_reward+posttrial_padding)

                        # iterate through trials
                        for trial_idx in range(len(trial_start_times)):
                            # create trial
                            trial=RecordingTrial()
                            trial.trial_number=trial_idx+1
                            trial.start_time=trial_start_times[trial_idx]
                            trial.end_time=trial_end_times[trial_idx]
                            trial.save()
                            print('importing trial %d, %.3f-%.3f' % (trial_idx,trial.start_time,trial.end_time))

                            for event,evt_idx in events.iteritems():
                                for evt_time in seg.eventarrays[evt_idx].times:
                                    if trial.start_time <= evt_time < trial.end_time:
                                        # create trial events
                                        new_event=Event(name=event, description='', trial=trial, time=evt_time.rescale('s').magnitude.item(0))
                                        new_event.save()

                            trial_type=None
                            object=None
                            if Event.objects.filter(name='ev_01_LightON_visualCOR_RNG',trial=trial).count():
                                trial_type='nogo'
                                object='RNG'
                            elif Event.objects.filter(name='ev_02_LightON_motorCORc1_RNG',trial=trial).count():
                                trial_type='motor-light'
                                object='RNG'
                            elif Event.objects.filter(name='ev_04_Pull_CORc2_RNG',trial=trial).count():
                                trial_type='motor-dark'
                                object='RNG'

                            elif Event.objects.filter(name='ev_05_LightON_visualCOR_SML',trial=trial).count():
                                trial_type='nogo'
                                object='SML'
                            elif Event.objects.filter(name='ev_06_LightON_motorCORc1_SML',trial=trial).count():
                                trial_type='motor-light'
                                object='SML'
                            elif Event.objects.filter(name='ev_08_Pull_CORc2_SML',trial=trial).count():
                                trial_type='motor-dark'
                                object='SML'

                            elif Event.objects.filter(name='ev_09_LightON_visualCOR_BIG',trial=trial).count():
                                trial_type='nogo'
                                object='BIG'
                            elif Event.objects.filter(name='ev_10_LightON_motorCORc1_BIG',trial=trial).count():
                                trial_type='motor-light'
                                object='BIG'
                            elif Event.objects.filter(name='ev_12_Pull_CORc2_BIG',trial=trial).count():
                                trial_type='motor-dark'
                                object='BIG'

                            if (epoch_type,trial_type,object) in condition_map:
                                trial.condition=condition_map[(epoch_type,trial_type,object)]
                                trial.save()
                                events_to_delete=[]
                                for event in Event.objects.filter(trial=trial):
                                    old_evt_name=event.name
                                    if old_evt_name in event_map:
                                        event.name=event_map[old_evt_name][0]
                                        event.description=event_map[old_evt_name][1]
                                        event.save()
                                    else:
                                        events_to_delete.append(event.id)
                                Event.objects.filter(id__in=events_to_delete).delete()

                                for unit_idx,st in enumerate(seg.spiketrains):
                                    unit_recording=UnitRecording(unit=units[unit_idx], trial=trial)
                                    spike_times=[]
                                    for spike_time in st.rescale('s').magnitude:
                                        if trial.start_time <= spike_time < trial.end_time:
                                            spike_times.append(spike_time)
                                    if len(spike_times)>0:
                                        unit_recording.spike_times=','.join([str(x) for x in sorted(spike_times)])
                                    unit_recording.save()
                            else:
                                Event.objects.filter(trial=trial).delete()
                                trial.delete()



def find_nearest_event_before(event_time, event_array, epoch_start, epoch_end):
    nearest_time=0
    try:
        event_time=event_time.rescale('s').magnitude.item(0)
    except:
        pass
    for time_idx,time in enumerate(event_array.times):
        time=time.rescale('s').magnitude.item(0)
        if epoch_start <= time <= epoch_end:
            if time<event_time:
                diff=event_time-time
                if diff<event_time-nearest_time:
                    nearest_time=time
            else:
                break
    if nearest_time==0:
        return None
    return nearest_time


def find_nearest_event_after(event_time, event_array, epoch_start, epoch_end):
    try:
        event_time=event_time.rescale('s').magnitude.item(0)
    except:
        pass
    for time_idx,time in enumerate(event_array.times):
        time=time.rescale('s').magnitude.item(0)
        if epoch_start <= time <= epoch_end:
            if time>event_time:
                return time
    return None

class ImportView(LoginRequiredMixin, CreateView):
    model = Experiment
    form_class = ExperimentForm
    template_name = 'sensorimotordb/experiment/experiment_import_detail.html'

    def get_initial(self):
        initial=super(ImportView,self).get_initial()
        initial['collator']=self.request.user
        initial['last_modified_by']=self.request.user
        return initial

    def init_conditions(self):
        condition_types={
            'VISUOMOTOR_TASK':{
                'motor-light':['RNG','SML','BIG'],
                'motor-dark':['RNG','SML','BIG'],
                'nogo':['RNG','SML','BIG']
            },
            'OBSERVATION_TASK':{
                'motor-light':['RNG','SML','BIG'],
                'nogo':['RNG','SML','BIG']
            }
        }
        for epoch_type in condition_types:
            for trial_type in condition_types[epoch_type]:
                for object in condition_types[epoch_type][trial_type]:
                    condition=GraspCondition()
                    condition.experiment=self.object
                    condition.name='Epoch type: %s, Trial type: %s, Object: %s' % (epoch_type, trial_type, object)
                    condition.object_distance=0
                    condition.description=''
                    condition.save()

    def form_valid(self, form):
        self.object=form.save(commit=False)
        self.object.collator=self.request.user
        self.object.save()
        files = self.request.FILES.getlist('data_file')
        data_path=os.path.join(settings.MEDIA_ROOT,'experiment_data','%s' % self.object.id)
        os.mkdir(data_path)
        for f_idx,f in enumerate(files):
            data_filename=os.path.join(data_path,'orig_data_%d.nex' % f_idx)
            with open(data_filename, 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)
        self.init_conditions()

        return redirect('/sensorimotordb/experiment/%d/import/' % self.object.id)


class ConditionDetailView(LoginRequiredMixin, DetailView):
    model=Condition
    permission_required = 'view'

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if GraspObservationCondition.objects.filter(id=pk).count():
            self.model=GraspObservationCondition
            self.template_name = 'sensorimotordb/condition/grasp_observation_condition_view.html'
        elif GraspPerformanceCondition.objects.filter(id=pk).count():
            self.model = GraspPerformanceCondition
            self.template_name = 'sensorimotordb/condition/grasp_performance_condition_view.html'
        return super(ConditionDetailView,self).get_object(queryset=queryset)

    def get_context_data(self, **kwargs):
        context=super(ConditionDetailView,self).get_context_data(**kwargs)
        context['site_url']='http://%s' % get_current_site(self.request)
        context['video_url_mp4']=''
        if os.path.exists(os.path.join(settings.MEDIA_ROOT,'video','condition_%d.mp4' % self.object.id)):
            context['video_url_mp4']=''.join(['http://', get_current_site(None).domain, os.path.join('/media/video/',
                'condition_%d.mp4' % self.object.id)])
            context['video_events']=ConditionVideoEvent.objects.filter(condition=self.object).order_by('time')
        return context


class UnitDetailView(LoginRequiredMixin, DetailView):
    model = Unit
    template_name = 'sensorimotordb/unit/unit_view.html'


class ExperimentDetailView(LoginRequiredMixin, DetailView):
    model = Experiment
    template_name = 'sensorimotordb/experiment/experiment_view.html'

    def get_context_data(self, **kwargs):
        context=super(ExperimentDetailView,self).get_context_data(**kwargs)
        context['can_export']=False
        if self.request.user.is_superuser or ExperimentExportRequest.objects.filter(experiment__id=self.object.id, requesting_user__id=self.request.user.id, status='approved').exists():
            context['can_export']=True
        context['can_delete']=False
        if self.request.user.is_superuser or self.object.collator==self.request.user.id:
            context['can_delete']=True
        return context


class AnalysisResultsDetailView(LoginRequiredMixin, DetailView):
    model=AnalysisResults

    def get(self, request, *args, **kwargs):
        id=self.kwargs.get('pk', None)
        if VisuomotorClassificationAnalysisResults.objects.filter(id=id).exists():
            return redirect('/sensorimotordb/visuomotor_classification_analysis_results/%s/' % id)
        elif MirrorTypeClassificationAnalysisResults.objects.filter(id=id).exists():
            return redirect('/sensorimotordb/mirror_type_classification_analysis_results/%s/' % id)


class DeleteAnalysisResultsView(JSONResponseMixin,BaseDetailView):
    model=AnalysisResults
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            self.object=self.get_object()
            if VisuomotorClassificationAnalysisResults.objects.filter(id=self.object.id):
                results=VisuomotorClassificationAnalysisResults.objects.get(id=self.object.id)
                for classification in UnitClassification.objects.filter(analysis_results=results):
                    classification.delete()
                for unit_results in VisuomotorClassificationUnitAnalysisResults.objects.filter(analysis_results=results):
                    unit_results.delete()
                for level_mapping in AnalysisResultsLevelMapping.objects.filter(analysis_results=results):
                    level_mapping.delete()
                results.delete()
                self.object.delete()
            elif MirrorTypeClassificationAnalysisResults.objects.filter(id=self.object.id):
                results=MirrorTypeClassificationAnalysisResults.objects.get(id=self.object.id)
                for classification in UnitClassification.objects.filter(analysis_results=results):
                    classification.delete()
                for unit_results in MirrorTypeClassificationUnitAnalysisResults.objects.filter(analysis_results=results):
                    unit_results.delete()
                for level_mapping in AnalysisResultsLevelMapping.objects.filter(analysis_results=results):
                    level_mapping.delete()
                results.delete()
                self.object.delete()
            context={'id': self.request.POST['id']}

        return context


class DeleteExperimentView(JSONResponseMixin,BaseDetailView):
    model=Experiment
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            self.object=self.get_object()
            ConditionVideoEvent.objects.filter(condition__experiment=self.object).delete()
            units_to_delete=Unit.objects.filter(unit_recording__trial__condition__experiment=self.object).values_list('id',flat=True)
            UnitRecording.objects.filter(trial__condition__experiment=self.object).delete()
            Event.objects.filter(trial__condition__experiment=self.object).delete()
            RecordingTrial.objects.filter(condition__experiment=self.object).delete()
            Unit.objects.filter(id__in=units_to_delete).delete()
            Condition.objects.filter(experiment=self.object).delete()
            ExperimentExportRequest.objects.filter(experiment=self.object).delete()

            UnitAnalysisResults.objects.filter(analysis_results__experiment=self.object).delete()
            AnalysisResultsLevelMapping.objects.filter(analysis_results__experiment=self.object).delete()
            UnitClassification.objects.filter(analysis_results__experiment=self.object).delete()
            AnalysisResults.objects.filter(experiment=self.object).delete()

            data_path=os.path.join(settings.MEDIA_ROOT,'experiment_data','%s' % self.object.id)
            shutil.rmtree(data_path)

            self.object.delete()
            context={'id': self.request.POST['id']}

        return context


class VisuomotorClassificationAnalysisResultsDetailView(AnalysisResultsDetailView):
    model=VisuomotorClassificationAnalysisResults
    template_name = 'sensorimotordb/analysis/visuomotor_classification_analysis_results_view.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = AnalysisResultsDetailView.get_context_data(self, **kwargs)
        context['factors']=Factor.objects.filter(analysis=self.object.analysis)
        context['bodb_server']=settings.BODB_SERVER
        context['api_key']=ApiKey.objects.get(user=self.request.user).key
        context['username']=self.request.user.username
        return context


class DeleteVisuomotorClassificationAnalysisResultsView(JSONResponseMixin,BaseDetailView):
    model=VisuomotorClassificationAnalysisResults

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            self.object=self.get_object()
            UnitAnalysisResults.objects.filter(analysis_results=self.object).delete()
            UnitClassification.objects.filter(analysis_results=self.object).delete()
            VisuomotorClassificationUnitAnalysisResults.objects.filter(analysis_results=self.object).delete()
            AnalysisResultsLevelMapping.objects.filter(analysis_results=self.object).delete()
            self.object.delete()
            context={'id': self.request.POST['id']}

        return context


class MirrorTypeClassificationAnalysisResultsDetailView(AnalysisResultsDetailView):
    model=MirrorTypeClassificationAnalysisResults
    template_name = 'sensorimotordb/analysis/mirror_type_classification_analysis_results_view.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = AnalysisResultsDetailView.get_context_data(self, **kwargs)
        context['factors']=Factor.objects.filter(analysis=self.object.analysis)
        context['bodb_server']=settings.BODB_SERVER
        context['api_key']=ApiKey.objects.get(user=self.request.user).key
        context['username']=self.request.user.username
        return context


class DeleteMirrorTypeClassificationAnalysisResultsView(JSONResponseMixin,BaseDetailView):
    model=MirrorTypeClassificationAnalysisResults

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            self.object=self.get_object()
            UnitAnalysisResults.objects.filter(analysis_results=self.object).delete()
            UnitClassification.objects.filter(analysis_results=self.object).delete()
            MirrorTypeClassificationUnitAnalysisResults.objects.filter(analysis_results=self.object).delete()
            AnalysisResultsLevelMapping.objects.filter(analysis_results=self.object).delete()
            self.object.delete()
            context={'id': self.request.POST['id']}

        return context


class SearchView(LoginRequiredMixin, TemplateView):
    template_name = 'sensorimotordb/search.html'


class ExperimentExportRequestView(LoginRequiredMixin,CreateView):
    model = ExperimentExportRequest
    form_class = ExperimentExportRequestForm
    template_name = 'sensorimotordb/experiment/experiment_export_request_detail.html'

    def get_initial(self):
        initial=super(ExperimentExportRequestView,self).get_initial()
        initial['experiment']=Experiment.objects.get(id = self.kwargs.get('pk', None))
        initial['requesting_user']=self.request.user
        return initial

    def form_valid(self, form):
        self.object=form.save(commit=False)
        self.object.user=self.request.user
        self.object.save()

        return redirect('/sensorimotordb/experiment/%d/' % self.object.experiment.id)


class ExperimentExportRequestDenyView(LoginRequiredMixin,UpdateView):
    model=ExperimentExportRequest
    template_name = 'sensorimotordb/experiment/experiment_export_request_deny.html'
    pk_url_kwarg='activation_key'
    form_class = ExperimentExportRequestDenyForm

    def get_object(self, queryset=None):
        return ExperimentExportRequest.objects.get(activation_key=self.kwargs.get('activation_key'),experiment__id=self.kwargs.get('pk'))

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instantiating the form.
        """
        kwargs = super(ModelFormMixin, self).get_form_kwargs()
        return kwargs

    def form_valid(self, form):
        self.object.status='denied'
        self.object.save()

        # message subject
        subject='Experiment Export Request Denied'
        # message text
        text='Your request for exporting data from the experiment: %s has been denied.<br>' % self.object.experiment.title
        text+='Reason for denial: %s' % self.request.POST['reason']

        msg = EmailMessage(subject, text, 'uscbrainproject@gmail.com', [self.object.requesting_user.email])
        msg.content_subtype = "html"  # Main content is now text/html
        msg.send(fail_silently=True)

        return redirect('/sensorimotordb/experiment/%d/' % self.object.experiment.id)


class ExperimentExportRequestApproveView(LoginRequiredMixin, UpdateView):
    model=ExperimentExportRequest
    template_name = 'sensorimotordb/experiment/experiment_export_request_approve.html'
    pk_url_kwarg='activation_key'
    form_class = ExperimentExportRequestApproveForm

    def get_object(self, queryset=None):
        return ExperimentExportRequest.objects.get(activation_key=self.kwargs.get('activation_key'), experiment__id=self.kwargs.get('pk'))

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instantiating the form.
        """
        kwargs = super(ModelFormMixin, self).get_form_kwargs()
        return kwargs

    def form_valid(self, form):
        self.object.status='approved'
        self.object.save()

        # message subject
        subject='Experiment Export Request Approved'
        # message text
        export_url = ''.join(
            ['http://', get_current_site(None).domain, '/sensorimotordb/experiment/%d/export/' % self.object.experiment.id])
        text='Your request for the data from the experiment: %s has been approved. Click <a href="%s">here</a> to download the data.<br>' % (self.object.experiment.title, export_url)

        msg = EmailMessage(subject, text, 'uscbrainproject@gmail.com', [self.object.requesting_user.email])
        msg.content_subtype = "html"  # Main content is now text/html
        msg.send(fail_silently=True)

        return redirect('/sensorimotordb/experiment/%d/' % self.object.experiment.id)


class ExperimentExportView(LoginRequiredMixin, DetailView):
    model=Experiment

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.user.is_superuser or ExperimentExportRequest.objects.filter(requesting_user=request.user, experiment=self.object, status='approved').exists():
            exp_path=os.path.join(PROJECT_PATH,'..','data','experiment_%d.h5' % self.object.id)
            if not os.path.exists(exp_path):
                self.object.export(exp_path)
            fsock = open(exp_path,"r")
            response = HttpResponse(fsock, content_type='application/hdf')
            response['Content-Disposition'] = 'attachment; filename=experiment_%d.h5' % self.object.id
            return response
        return HttpResponseForbidden()


class UpdateUserProfileView(LoginRequiredMixin,UpdateView):
    form_class = UserProfileForm
    model = User
    template_name = 'registration/user_profile_detail.html'
    success_url = '/accounts/profile/?msg=saved'

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super(UpdateUserProfileView,self).get_context_data(**kwargs)
        context['msg']=self.request.GET.get('msg',None)
        context['api_key']=ApiKey.objects.get(user=self.request.user).key
        return context

    def form_valid(self, form):
        # update user object
        user=form.save()
        if 'password1' in self.request.POST and len(self.request.POST['password1']):
            user.set_password(self.request.POST['password1'])
        user.save()

        return redirect(self.success_url)


class CreateVisuomotorClassificationAnalysisView(LoginRequiredMixin,CreateView):
    model = VisuomotorClassificationAnalysisResults
    form_class = VisuomotorClassificationAnalysisResultsForm
    template_name = 'sensorimotordb/analysis/visuomotor_classification_analysis_results_create.html'

    def get_context_data(self, **kwargs):
        context_data=super(CreateVisuomotorClassificationAnalysisView,self).get_context_data(**kwargs)
        context_data['factors']=Factor.objects.filter(analysis=VisuomotorClassificationAnalysis.objects.filter()[0]).prefetch_related('levels')
        context_data['conditions']=[]
        experiment_id=self.request.GET.get('experiment',None)
        if experiment_id is not None:
            context_data['conditions']=Condition.objects.filter(experiment__id=experiment_id)
        return context_data

    def get_form(self, form_class=None):
        form=super(CreateVisuomotorClassificationAnalysisView,self).get_form(form_class=form_class)
        experiment_id=self.request.GET.get('experiment',None)
        if experiment_id is not None:
            all_evts=Event.objects.filter(trial__condition__experiment__id=experiment_id).values_list('name',flat=True).distinct()
            form.fields['baseline_rel_evt'].choices=[]
            form.fields['baseline_rel_end_evt'].choices=[('','')]
            form.fields['obj_view_woi_rel_evt'].choices=[]
            form.fields['obj_view_woi_rel_end_evt'].choices=[('','')]
            for evt in all_evts:
                form.fields['baseline_rel_evt'].choices.append((evt,evt))
                form.fields['baseline_rel_end_evt'].choices.append((evt,evt))
                form.fields['obj_view_woi_rel_evt'].choices.append((evt,evt))
                form.fields['obj_view_woi_rel_end_evt'].choices.append((evt,evt))

            form.fields['grasp_woi_rel_evt'].choices=[]
            form.fields['grasp_woi_rel_end_evt'].choices=[('','')]
            execution_conditions=GraspPerformanceCondition.objects.filter(experiment__id=experiment_id)
            motor_evts=[]
            for evt in all_evts:
                for condition in execution_conditions:
                    if Event.objects.filter(name=evt, trial__condition=condition).count()>0 and not evt in motor_evts:
                        motor_evts.append(evt)
            for evt in motor_evts:
                form.fields['grasp_woi_rel_evt'].choices.append((evt,evt))
                form.fields['grasp_woi_rel_end_evt'].choices.append((evt,evt))

        return form

    def get_initial(self):
        initial_data={'analysis': VisuomotorClassificationAnalysis.objects.filter()[0]}
        experiment_id=self.request.GET.get('experiment',None)
        if experiment_id is not None:
            initial_data['experiment']=experiment_id
        return initial_data

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        self.object=form.save()
        for field in self.request.POST:
            if field.startswith('level_mapping_'):
                level_id=int(field.split('_')[-1])
                condition_ids=self.request.POST.getlist(field)
                mapping=AnalysisResultsLevelMapping(level=Level.objects.get(id=level_id), analysis_results=self.object)
                mapping.save()
                for condition_id in condition_ids:
                    mapping.conditions.add(Condition.objects.get(id=condition_id))
        analysis=VisuomotorClassificationAnalysis.objects.get(id=self.object.analysis.id)
        analysis.run(self.object)
        return redirect('/sensorimotordb/experiment/%d/' % self.object.experiment.id)


class CreateMirrorTypeClassificationAnalysisView(LoginRequiredMixin,CreateView):
    model = MirrorTypeClassificationAnalysisResults
    form_class = MirrorTypeClassificationAnalysisResultsForm
    template_name = 'sensorimotordb/analysis/mirror_type_classification_analysis_results_create.html'

    def get_context_data(self, **kwargs):
        context_data=super(CreateMirrorTypeClassificationAnalysisView,self).get_context_data(**kwargs)
        context_data['factors']=Factor.objects.filter(analysis=MirrorTypeClassificationAnalysis.objects.filter()[0]).prefetch_related('levels')
        context_data['conditions']=[]
        experiment_id=self.request.GET.get('experiment',None)
        if experiment_id is not None:
            context_data['conditions']=Condition.objects.filter(experiment__id=experiment_id)
        return context_data

    def get_form(self, form_class=None):
        form=super(CreateMirrorTypeClassificationAnalysisView,self).get_form(form_class=form_class)
        experiment_id=self.request.GET.get('experiment',None)
        if experiment_id is not None:
            all_evts=Event.objects.filter(trial__condition__experiment__id=experiment_id).values_list('name',flat=True).distinct()
            form.fields['baseline_rel_evt'].choices=[]
            form.fields['baseline_rel_end_evt'].choices=[('','')]
            form.fields['reach_woi_rel_evt'].choices=[]
            form.fields['reach_woi_rel_end_evt'].choices=[('','')]
            form.fields['hold_woi_rel_evt'].choices=[]
            form.fields['hold_woi_rel_end_evt'].choices=[('','')]
            for evt in all_evts:
                form.fields['baseline_rel_evt'].choices.append((evt,evt))
                form.fields['baseline_rel_end_evt'].choices.append((evt,evt))
                form.fields['reach_woi_rel_evt'].choices.append((evt,evt))
                form.fields['reach_woi_rel_end_evt'].choices.append((evt,evt))
                form.fields['hold_woi_rel_evt'].choices.append((evt,evt))
                form.fields['hold_woi_rel_end_evt'].choices.append((evt,evt))

        return form

    def get_initial(self):
        initial_data={'analysis': MirrorTypeClassificationAnalysis.objects.filter()[0]}
        experiment_id=self.request.GET.get('experiment',None)
        if experiment_id is not None:
            initial_data['experiment']=experiment_id
        return initial_data

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        self.object=form.save()
        for field in self.request.POST:
            if field.startswith('level_mapping_'):
                level_id=int(field.split('_')[-1])
                condition_ids=self.request.POST.getlist(field)
                mapping=AnalysisResultsLevelMapping(level=Level.objects.get(id=level_id), analysis_results=self.object)
                mapping.save()
                for condition_id in condition_ids:
                    mapping.conditions.add(Condition.objects.get(id=condition_id))
        analysis=MirrorTypeClassificationAnalysis.objects.get(id=self.object.analysis.id)
        analysis.run(self.object)
        return redirect('/sensorimotordb/experiment/%d/' % self.object.experiment.id)