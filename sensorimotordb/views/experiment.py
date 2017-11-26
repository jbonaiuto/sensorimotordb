from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.views.generic import UpdateView, DetailView, CreateView, TemplateView
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import ModelFormMixin
from haystack.management.commands import update_index, rebuild_index
import os
from sensorimotordb.api import FullRecordingTrialResource, ExperimentResource, ConditionResource
from sensorimotordb.forms import GraspObservationConditionForm, GraspPerformanceConditionForm, ExperimentForm, ExperimentExportRequestForm, ExperimentExportRequestDenyForm, ExperimentExportRequestApproveForm
from sensorimotordb.models import Condition, GraspObservationCondition, GraspPerformanceCondition, ConditionVideoEvent, Unit, UnitRecording, Event, RecordingTrial, Experiment, ExperimentExportRequest, UnitAnalysisResults, UnitClassification, AnalysisResults, Analysis, ClassificationAnalysisResults, Penetration
from sensorimotordb.views import LoginRequiredMixin, JSONResponseMixin
from uscbp import settings
from uscbp.settings import PROJECT_PATH

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


class ApiProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'sensorimotordb/api_profile.html'
    resource_class = None

    def get_context_data(self, **kwargs):
        context_data=super(ApiProfileView,self).get_context_data(**kwargs)

        resource=self.resource_class()
        obj_list = resource.wrap_view('dispatch_list')(self.request)
        response = resource.create_response(self.request, obj_list)
        context_data['api_response'] = response
        return context_data


class FullRecordingTrialApiProfileView(ApiProfileView):
    resource_class=FullRecordingTrialResource


class ExperimentApiProfileView(ApiProfileView):
    resource_class=ExperimentResource

    def get_context_data(self, **kwargs):
        context_data=super(ApiProfileView,self).get_context_data(**kwargs)

        resource=self.resource_class()
        obj = resource.wrap_view('dispatch_detail')(self.request,**kwargs)
        response = resource.create_response(self.request, obj)
        context_data['api_response'] = response
        return context_data


class ConditionApiProfileView(ApiProfileView):
    resource_class=ConditionResource
