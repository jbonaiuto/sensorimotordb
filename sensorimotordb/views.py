from h5py import h5
from wsgiref.util import FileWrapper
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.views.generic import DetailView, TemplateView, CreateView, UpdateView, View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import ModelFormMixin
import h5py
import os
from registration.forms import User
from sensorimotordb.forms import ExperimentExportRequestForm, ExperimentExportRequestDenyForm, ExperimentExportRequestApproveForm, UserProfileForm
from sensorimotordb.models import Condition, GraspObservationCondition, GraspPerformanceCondition, Unit, Experiment, ExperimentExportRequest, ConditionVideoEvent
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
        return context

    def form_valid(self, form):
        # update user object
        user=form.save()
        if 'password1' in self.request.POST and len(self.request.POST['password1']):
            user.set_password(self.request.POST['password1'])
        user.save()

        return redirect(self.success_url)
