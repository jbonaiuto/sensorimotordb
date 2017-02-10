import json
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
from sensorimotordb.forms import ExperimentExportRequestForm, ExperimentExportRequestDenyForm, ExperimentExportRequestApproveForm, UserProfileForm, VisuomotorClassificationAnalysisResultsForm
from sensorimotordb.models import Condition, GraspObservationCondition, GraspPerformanceCondition, Unit, Experiment, ExperimentExportRequest, ConditionVideoEvent, AnalysisResults, VisuomotorClassificationAnalysisResults, Factor, VisuomotorClassificationAnalysis, Event, AnalysisResultsLevelMapping, Level, UnitClassification, VisuomotorClassificationUnitAnalysisResults
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