from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.views.generic import UpdateView, DetailView, CreateView
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import ModelFormMixin
from haystack.management.commands import update_index, rebuild_index
import math
import os
import scipy.io
from sensorimotordb.forms import GraspObservationConditionForm, GraspPerformanceConditionForm, ExperimentForm, \
    ExperimentExportRequestForm, ExperimentExportRequestDenyForm, ExperimentExportRequestApproveForm, ExperimentImportForm, GraspConditionFormSet, ExperimentCreateForm
from sensorimotordb.models import Condition, GraspObservationCondition, GraspPerformanceCondition, ConditionVideoEvent, \
    Unit, UnitRecording, Event, RecordingTrial, Experiment, ExperimentExportRequest, UnitAnalysisResults, \
    UnitClassification, AnalysisResults, Analysis, GraspCondition, Species, BrainRegion, Penetration, ClassificationAnalysisResults, Subject
from sensorimotordb.views import LoginRequiredMixin, JSONResponseMixin
from uscbp import settings
from uscbp.settings import PROJECT_PATH

def get_events(trial):
    ev_idx = -1

    # get indices of area, unit type, index, and events
    for idx, (dtype, o) in enumerate(trial.dtype.descr):
        if dtype == 'ev':
            ev_idx = idx

    ev = trial[ev_idx]
    ev_idx=-1
    for idx, (dtype, o) in enumerate(ev.dtype.descr):
        if dtype == 'ev':
            ev_idx = idx
    events=ev[0][0][ev_idx]
    return events

def get_key(mat_file):
    key='U'
    if 'au' in mat_file:
        key='au'
    elif 'AU' in mat_file:
        key='AU'
    return key

excluded_events=['gng','err','wrn','LCDoff']

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
                ttype_part=parts[0]
                trial_type=ttype_part.split(' ')[2]
                obj_part=parts[1]
                object=int(obj_part.split(' ')[2])
                init_data.append({
                    'id':condition.id,
                    'condition_ptr':condition.id,
                    'name':condition.name,
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

        context['event_types']=self.request.GET['event_types'].split(',')
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
                if grasp_condition.type=='grasp_performance':
                    grasp_perf_cond=GraspPerformanceCondition(graspcondition_ptr=grasp_condition)
                    grasp_perf_cond.__dict__.update(grasp_condition.__dict__)
                    grasp_perf_cond.hand_visible=condition_form.cleaned_data['hand_visible']
                    grasp_perf_cond.object_visible=condition_form.cleaned_data['object_visible']
                    grasp_perf_cond.save()
                elif grasp_condition.type=='grasp_observation':
                    grasp_obs_cond=GraspObservationCondition(graspcondition_ptr=grasp_condition)
                    grasp_obs_cond.__dict__.update(grasp_condition.__dict__)
                    grasp_obs_cond.demonstrator_species=condition_form.cleaned_data['demonstrator_species']
                    grasp_obs_cond.demonstration_type=condition_form.cleaned_data['demonstration_type']
                    grasp_obs_cond.viewing_angle=condition_form.cleaned_data['viewing_angle']
                    grasp_obs_cond.whole_body_visible=condition_form.cleaned_data['whole_body_visible']
                    grasp_obs_cond.save()

                condition_map[(condition_form.cleaned_data['trial_type'],int(condition_form.cleaned_data['object']))]=grasp_condition.id
        else:
            return self.form_invalid(form)
        self.import_kraskov_data(condition_map)
        try:
            rebuild_index.Command().handle(interactive=False)
        except:
            pass
        return redirect('/sensorimotordb/experiment/%d/' % self.object.id)

    def import_kraskov_data(self, condition_map):
        data_file=os.path.join(settings.MEDIA_ROOT,'experiment_data','%s' % self.object.id,'orig_data.mat')
        mat_file = scipy.io.loadmat(data_file)
        key=get_key(mat_file)

        trial_numbers = {}
        for i in range(len(mat_file[key][0])):
            print('importing unit %d' % i)
            unit=mat_file[key][0][i]
            area_idx = -1
            unittype_idx = -1
            index_idx = -1

            # get indices of area, unit type, index, and events
            for idx, (dtype, o) in enumerate(unit.dtype.descr):
                if dtype == 'area':
                    area_idx = idx
                elif dtype == 'unit':
                    unittype_idx = idx
                elif dtype == 'index':
                    index_idx = idx

            # create unit
            unit_obj = Unit()
            area = unit[area_idx][0]
            region = BrainRegion.objects.filter(Q(Q(name=area) | Q(abbreviation=area)))
            unit_obj.area = region[0]
            unit_obj.type = unit[unittype_idx][0]
            unit_obj.save()

            if not unit_obj.id in trial_numbers:
                trial_numbers[unit_obj.id] = {}

            index = unit[index_idx]
            events=get_events(unit)

            trialtype_idx = -1
            object_idx = -1
            trial_start_idx = -1
            trial_end_idx = -1
            err_idx=-1
            evt_idx={}
            for idx, (dtype, o) in enumerate(events[0].dtype.descr):
                if dtype == 'hm':
                    trialtype_idx = idx
                elif dtype == 'obj':
                    object_idx = idx
                elif dtype == 'LCDon':
                    trial_start_idx = idx
                elif dtype == 'HPN':
                    trial_end_idx = idx
                elif dtype == 'err':
                    err_idx=idx
                elif not dtype in excluded_events:
                    evt_idx[dtype]=idx

            trial_types = events[0][0][trialtype_idx][0]
            objects = events[0][0][object_idx][0]
            trial_start_times = events[0][0][trial_start_idx][0]
            trial_end_times = events[0][0][trial_end_idx][0]
            errors=events[0][0][err_idx][0]
            event_times={}
            for ev_type in evt_idx:
                event_times[ev_type]=events[0][0][evt_idx[ev_type]][0]

            # iterate through trials
            num_trials=0
            for j in range(len(trial_types)):
                if not math.isnan(trial_start_times[j]) and not math.isnan(trial_end_times[j]) and errors[j]==0:
                    num_trials=num_trials+1
                    # create trial
                    trial = RecordingTrial()
                    trial.condition = Condition.objects.get(id=condition_map[(trial_types[j],objects[j])])
                    if not trial.condition.id in trial_numbers[unit_obj.id]:
                        trial_numbers[unit_obj.id][trial.condition.id] = 0
                    trial_numbers[unit_obj.id][trial.condition.id] += 1
                    trial.trial_number = trial_numbers[unit_obj.id][trial.condition.id]
                    trial.start_time = trial_start_times[j]
                    trial.end_time = trial_end_times[j]
                    trial.save()

                    next_trial_start_time = None
                    if j < len(trial_types) - 1:
                        next_trial_start_time = trial_start_times[j + 1]

                    previous_trial = None
                    if trial_numbers[unit_obj.id][trial.condition.id] > 1:
                        previous_trial = RecordingTrial.objects.get(condition=trial.condition,
                            unit_recordings__unit=unit_obj, trial_number=trial_numbers[unit_obj.id][trial.condition.id] - 1)

                    unit_recording = UnitRecording(unit=unit_obj, trial=trial)
                    # load spikes
                    spike_times = []
                    for k in range(len(index)):
                        if previous_trial is None:
                            if index[k, 0] >= trial.start_time - 1.0:
                                if next_trial_start_time is None:
                                    if index[k, 0] < trial.end_time + 1.0:
                                        spike_times.append(index[k, 0])
                                elif index[k, 0] < trial.end_time + 1.0 and index[k, 0] < next_trial_start_time:
                                    spike_times.append(index[k, 0])
                        elif index[k, 0] >= trial.start_time - 1.0 and index[k, 0] >= previous_trial.end_time:
                            if next_trial_start_time is None:
                                if index[k, 0] < trial.end_time + 1.0:
                                    spike_times.append(index[k, 0])
                            elif index[k, 0] < trial.end_time + 1.0 and index[k, 0] < next_trial_start_time:
                                spike_times.append(index[k, 0])

                    unit_recording.spike_times = ','.join([str(x) for x in sorted(spike_times)])
                    unit_recording.save()

                    # create trial events
                    for ev_type in event_times:
                        if not math.isnan(event_times[ev_type][j]):
                            event=Event(name=ev_type, description=ev_type, trial=trial, time=event_times[ev_type][j])
                            event.save()
            print('%d trials' % num_trials)


class ImportView(LoginRequiredMixin, CreateView):
    model = Experiment
    form_class = ExperimentCreateForm
    template_name = 'sensorimotordb/experiment/experiment_import_detail.html'

    def get_initial(self):
        initial=super(ImportView,self).get_initial()
        initial['collator']=self.request.user
        initial['last_modified_by']=self.request.user
        return initial

    def get_event_types(self, data_file):
        event_types=[]
        mat_file = scipy.io.loadmat(data_file)
        key=get_key(mat_file)
        for i in range(len(mat_file[key][0])):
            trial=mat_file[key][0][i]
            events=get_events(trial)

            for idx, (dtype, o) in enumerate(events.dtype.descr):
                if not (dtype == 'hm' or dtype == 'obj' or dtype == 'LCDon' or dtype == 'HPN' or dtype in excluded_events):
                    if dtype.lower() not in event_types:
                        event_types.append(dtype.lower())
        return event_types


    def init_conditions(self, data_file):
        mat_file = scipy.io.loadmat(data_file)
        key=get_key(mat_file)
        condition_type={}

        for i in range(len(mat_file[key][0])):
            trial=mat_file[key][0][i]
            events=get_events(trial)

            trialtype_idx = -1
            object_idx = -1
            for idx, (dtype, o) in enumerate(events.dtype.descr):
                if dtype == 'hm':
                    trialtype_idx = idx
                elif dtype == 'obj':
                    object_idx = idx

            trial_types = events[0][0][trialtype_idx][0]
            objects = events[0][0][object_idx][0]

            # iterate through trials
            for j in range(len(trial_types)):
                # create trial
                trial_type=trial_types[j]
                object=objects[j]
                if not trial_type in condition_type:
                    condition_type[trial_type]=[]
                if not object in condition_type[trial_type]:
                    condition_type[trial_type].append(object)

        for trial_type in condition_type:
            for object in condition_type[trial_type]:
                condition=GraspCondition()
                condition.experiment=self.object
                condition.name='Trial type: %s, Object: %d' % (trial_type, object)
                condition.object_distance=0
                condition.description=''
                condition.save()


    def form_valid(self, form):
        self.object=form.save(commit=False)
        self.object.collator=self.request.user
        self.object.save()

        data_file=self.request.FILES['data_file']
        data_path=os.path.join(settings.MEDIA_ROOT,'experiment_data','%s' % self.object.id)
        os.mkdir(data_path)
        data_filename=os.path.join(data_path,'orig_data.mat')
        with open(data_filename, 'wb+') as destination:
            for chunk in data_file.chunks():
                destination.write(chunk)

        self.init_conditions(data_filename)
        event_types=self.get_event_types(data_filename)

        return redirect('/sensorimotordb/experiment/%d/import/?event_types=%s' % (self.object.id,','.join(event_types)))


class UpdateConditionView(LoginRequiredMixin, UpdateView):
    model=Condition
    permission_required = 'edit'

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if GraspObservationCondition.objects.filter(id=pk).count():
            self.model=GraspObservationCondition
            self.template_name = 'sensorimotordb/condition/grasp_observation_condition_edit.html'
            self.form_class=GraspObservationConditionForm
        elif GraspPerformanceCondition.objects.filter(id=pk).count():
            self.model = GraspPerformanceCondition
            self.template_name = 'sensorimotordb/condition/grasp_performance_condition_edit.html'
            self.form_class=GraspPerformanceConditionForm
        return super(UpdateConditionView,self).get_object(queryset=queryset)

    def form_valid(self, form):
        self.object.last_modified_by=self.request.user
        self.object.save()

        try:
            update_index.Command().handle(interactive=False)
        except:
            pass

        return redirect('/sensorimotordb/condition/%d/' % self.object.id)


class DeleteConditionView(JSONResponseMixin,BaseDetailView):
    model=Condition
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            self.object=self.get_object()
            ConditionVideoEvent.objects.filter(condition=self.object).delete()
            units_to_delete=Unit.objects.filter(unit_recording__trial__condition=self.object).values_list('id',flat=True)
            UnitRecording.objects.filter(trial__condition=self.object).delete()
            Event.objects.filter(trial__condition=self.object).delete()
            RecordingTrial.objects.filter(condition=self.object).delete()
            Unit.objects.filter(id__in=units_to_delete).delete()

            self.object.delete()

            try:
                rebuild_index.Command().handle(interactive=False)
            except:
                pass

            context={'id': self.request.POST['id']}

        return context


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
        context['can_delete']=False
        context['can_edit']=False
        if self.request.user.is_superuser or self.object.experiment.collator==self.request.user.id:
            context['can_delete']=True
            context['can_edit']=True
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
        context['can_edit']=False
        if self.request.user.is_superuser or self.object.collator==self.request.user.id:
            context['can_delete']=True
            context['can_edit']=True
        context['analyses']=Analysis.objects.all()
        return context


class UpdateExperimentView(LoginRequiredMixin, UpdateView):
    model=Experiment
    template_name = 'sensorimotordb/experiment/experiment_edit.html'
    form_class = ExperimentForm

    def form_valid(self, form):
        self.object.last_modified_by=self.request.user
        self.object.save()

        try:
            update_index.Command().handle(interactive=False)
        except:
            pass
        return redirect('/sensorimotordb/experiment/%d/' % self.object.id)


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
            Subject.objects.filter(penetration__units__id__in=units_to_delete).delete()
            Penetration.objects.filter(units__id__in=units_to_delete).delete()
            Condition.objects.filter(experiment=self.object).delete()
            ExperimentExportRequest.objects.filter(experiment=self.object).delete()

            if ClassificationAnalysisResults.objects.filter(experiment=self.object):
                UnitClassification.objects.filter(analysis_results__experiment=self.object).delete()
                UnitAnalysisResults.objects.filter(analysis_results__experiment=self.object.delete())
                ClassificationAnalysisResults.objects.filter(experiment=self.object).delete()
            AnalysisResults.objects.filter(experiment=self.object).delete()

            self.object.delete()

            try:
                rebuild_index.Command().handle(interactive=False)
            except:
                pass
            context={'id': self.request.POST['id']}

        return context


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
        return ExperimentExportRequest.objects.get(activation_key=self.kwargs.get('activation_key'),
            experiment__id=self.kwargs.get('pk'))

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
        return ExperimentExportRequest.objects.get(activation_key=self.kwargs.get('activation_key'),
            experiment__id=self.kwargs.get('pk'))

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