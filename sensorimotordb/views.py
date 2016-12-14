import json
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
import os
from registration.forms import User
from tastypie.models import ApiKey
from sensorimotordb.forms import ExperimentExportRequestForm, ExperimentExportRequestDenyForm, ExperimentExportRequestApproveForm, UserProfileForm, VisuomotorClassificationAnalysisResultsForm, ExperimentForm, ConditionFormSet, ExperimentImportForm, GraspConditionFormSet
from sensorimotordb.models import Condition, GraspObservationCondition, GraspPerformanceCondition, Unit, Experiment, ExperimentExportRequest, ConditionVideoEvent, AnalysisResults, VisuomotorClassificationAnalysisResults, Factor, VisuomotorClassificationAnalysis, Event, AnalysisResultsLevelMapping, Level, UnitClassification, VisuomotorClassificationUnitAnalysisResults, Species, BrainRegion, RecordingTrial, UnitRecording, GraspCondition
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
                if not condition_form in condition_formset.deleted_forms:
                    grasp_condition=condition_form.save(commit=False)
                    print(grasp_condition.experiment.id)
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
        print(condition_map)
        self.import_kraskov_data(condition_map)
        return redirect('/sensorimotordb/experiment/%d/' % self.object.id)

    def import_kraskov_data(self, condition_map):
        data_file=os.path.join(settings.MEDIA_ROOT,'experiment_data','%s' % self.object.id,'orig_data.mat')
        mat_file = scipy.io.loadmat(data_file)
        trial_numbers = {}
        for i in range(len(mat_file['U'][0])):
            print('importing unit %d' % i)
            area_idx = -1
            unittype_idx = -1
            index_idx = -1
            events_idx = -1

            # get indices of area, unit type, index, and events
            for idx, (dtype, o) in enumerate(mat_file['U'][0][i].dtype.descr):
                if dtype == 'area':
                    area_idx = idx
                elif dtype == 'unittype':
                    unittype_idx = idx
                elif dtype == 'index':
                    index_idx = idx
                elif dtype == 'events':
                    events_idx = idx

            # create unit
            unit = Unit()
            area = mat_file['U'][0][i][area_idx][0]
            region = BrainRegion.objects.filter(Q(Q(name=area) | Q(abbreviation=area)))
            unit.area = region[0]
            unit.type = mat_file['U'][0][i][unittype_idx][0]
            unit.save()

            if not unit.id in trial_numbers:
                trial_numbers[unit.id] = {}

            index = mat_file['U'][0][i][index_idx]
            events = mat_file['U'][0][i][events_idx]

            trialtype_idx = -1
            object_idx = -1
            trial_start_idx = -1
            go_idx = -1
            mo_idx = -1
            do_idx = -1
            ho_idx = -1
            hoff_idx = -1
            trial_end_idx = -1
            for idx, (dtype, o) in enumerate(events[0].dtype.descr):
                if dtype == 'trialtype':
                    trialtype_idx = idx
                elif dtype == 'object':
                    object_idx = idx
                elif dtype == 'TrialStart':
                    trial_start_idx = idx
                elif dtype == 'Go':
                    go_idx = idx
                elif dtype == 'MO':
                    mo_idx = idx
                elif dtype == 'DO':
                    do_idx = idx
                elif dtype == 'HO':
                    ho_idx = idx
                elif dtype == 'HOff':
                    hoff_idx = idx
                elif dtype == 'TrialEnd':
                    trial_end_idx = idx

            trial_types = events[0][0][trialtype_idx][0]
            objects = events[0][0][object_idx][0]
            trial_start_times = events[0][0][trial_start_idx][0]
            go_events = events[0][0][go_idx][0]
            mo_events = events[0][0][mo_idx][0]
            do_events = events[0][0][do_idx][0]
            ho_events = events[0][0][ho_idx][0]
            hoff_events = events[0][0][hoff_idx][0]
            trial_end_times = events[0][0][trial_end_idx][0]

            # iterate through trials
            for j in range(len(trial_types)):
                # create trial
                trial = RecordingTrial()
                trial.condition = Condition.objects.get(id=condition_map[(trial_types[j],objects[j])])
                if not trial.condition.id in trial_numbers[unit.id]:
                    trial_numbers[unit.id][trial.condition.id] = 0
                trial_numbers[unit.id][trial.condition.id] += 1
                trial.trial_number = trial_numbers[unit.id][trial.condition.id]
                trial.start_time = trial_start_times[j]
                trial.end_time = trial_end_times[j]
                trial.save()

                next_trial_start_time = None
                if j < len(trial_types) - 1:
                    next_trial_start_time = trial_start_times[j + 1]

                previous_trial = None
                if trial_numbers[unit.id][trial.condition.id] > 1:
                    previous_trial = RecordingTrial.objects.get(condition=trial.condition,
                        unit_recordings__unit=unit, trial_number=trial_numbers[unit.id][trial.condition.id] - 1)

                unit_recording = UnitRecording(unit=unit, trial=trial)
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
                go_event = Event(name='go', description='go signal', trial=trial, time=go_events[j])
                go_event.save()

                mo_event = Event(name='mo', description='movement onset', trial=trial, time=mo_events[j])
                mo_event.save()

                do_event = Event(name='do', description='object displacement onset', trial=trial, time=do_events[j])
                do_event.save()

                ho_event = Event(name='ho', description='stable hold onset', trial=trial, time=ho_events[j])
                ho_event.save()

                hoff_event = Event(name='hoff', description='hold offset', trial=trial, time=hoff_events[j])
                hoff_event.save()


class ImportView(LoginRequiredMixin, CreateView):
    model = Experiment
    form_class = ExperimentForm
    template_name = 'sensorimotordb/experiment/experiment_import_detail.html'

    def get_initial(self):
        initial=super(ImportView,self).get_initial()
        initial['collator']=self.request.user
        initial['last_modified_by']=self.request.user
        return initial

    def get_event_types(self, data_file):
        event_types=[]
        mat_file = scipy.io.loadmat(data_file)
        for i in range(len(mat_file['U'][0])):
            events_idx = -1

            # get indices of area, unit type, index, and events
            for idx, (dtype, o) in enumerate(mat_file['U'][0][i].dtype.descr):
                if dtype == 'events':
                    events_idx = idx

            events = mat_file['U'][0][i][events_idx]

            for idx, (dtype, o) in enumerate(events[0].dtype.descr):
                if not (dtype == 'trialtype' or dtype == 'object' or dtype == 'TrialStart' or dtype == 'TrialEnd'):
                    if dtype.lower() not in event_types:
                        event_types.append(dtype.lower())
        return event_types


    def init_conditions(self, data_file):
        mat_file = scipy.io.loadmat(data_file)
        condition_type={}

        for i in range(len(mat_file['U'][0])):
            events_idx = -1

            # get indices of area, unit type, index, and events
            for idx, (dtype, o) in enumerate(mat_file['U'][0][i].dtype.descr):
                if dtype == 'events':
                    events_idx = idx

            events = mat_file['U'][0][i][events_idx]
            trialtype_idx = -1
            object_idx = -1
            for idx, (dtype, o) in enumerate(events[0].dtype.descr):
                if dtype == 'trialtype':
                    trialtype_idx = idx
                elif dtype == 'object':
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
        print(event_types)

        return redirect('/sensorimotordb/experiment/%d/import/?event_types=%s' % (self.object.id,','.join(event_types)))


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
        return context


class AnalysisResultsDetailView(LoginRequiredMixin, DetailView):
    model=AnalysisResults

    def get(self, request, *args, **kwargs):
        id=self.kwargs.get('pk', None)
        if VisuomotorClassificationAnalysisResults.objects.filter(id=id).exists():
            return redirect('/sensorimotordb/visuomotor_classification_analysis_results/%s/' % id)


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
            for classification in UnitClassification.objects.filter(analysis_results=self.object):
                classification.delete()
            for unit_results in VisuomotorClassificationUnitAnalysisResults.objects.filter(analysis_results=self.object):
                unit_results.delete()
            for level_mapping in AnalysisResultsLevelMapping.objects.filter(analysis_results=self.object):
                level_mapping.delete()
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