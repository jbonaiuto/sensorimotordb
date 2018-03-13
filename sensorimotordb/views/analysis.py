from collections import OrderedDict

import os
from django.shortcuts import redirect
from django.views.generic import DetailView, CreateView, TemplateView
from django.views.generic.detail import BaseDetailView
from django.core.files.storage import FileSystemStorage
from formtools.wizard.views import SessionWizardView
from tastypie.models import ApiKey
from sensorimotordb.forms import ClassificationAnalysisForm, ClassificationAnalysisBaseForm, \
    ClassificationAnalysisResultsForm, ClassificationAnalysisStep2Form, ClusterAnalysisForm, \
    ClusterAnalysisResultsForm, ClassificationAnalysisFactorLevelFormSet, ClassificationAnalysisStep4Form
from sensorimotordb.models import AnalysisResults, ClassificationAnalysis, UnitClassificationType, Analysis, Factor, \
    FactorLevel, Condition, Event, ClassificationAnalysisResultsLevelMapping, ClassificationAnalysisResults, Experiment, \
    ClassificationAnalysisSettings, TimeWindowFactorLevelSettings, UnitClassification, UnitAnalysisResults, AnalysisSettings, \
    ClusterAnalysis, ClusterAnalysisResults, ClusterAnalysisSettings, TimeWindowConditionSettings
from sensorimotordb.views import LoginRequiredMixin, JSONResponseMixin
from uscbp import settings

class AnalysisListDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'sensorimotordb/analysis/analysis_list_view.html'

    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)
        context['classification_analyses']=ClassificationAnalysis.objects.all()
        context['cluster_analyses']=ClusterAnalysis.objects.all()
        return context


class DeleteClassificationAnalysisView(JSONResponseMixin,BaseDetailView):
    model=ClassificationAnalysis
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            self.object=self.get_object()
            if self.object.script_name is not None and os.path.exists(os.path.join(settings.MEDIA_ROOT,'scripts',self.object.script_name)):
                os.remove(os.path.join(settings.MEDIA_ROOT,'scripts',self.object.script_name))
            id=self.object.id
            UnitClassificationType.objects.filter(analysis=self.object).delete()
            UnitClassification.objects.filter(analysis_results__analysis=self.object).delete()
            UnitAnalysisResults.objects.filter(analysis_results__analysis=self.object).delete()
            AnalysisResults.objects.filter(analysis=self.object).delete()
            ClassificationAnalysisResults.objects.filter(analysis=self.object).delete()
            ClassificationAnalysisResultsLevelMapping.objects.filter(analysis_settings__analysis=self.object).delete()
            TimeWindowFactorLevelSettings.objects.filter(analysis_settings__analysis=self.object).delete()
            ClassificationAnalysisSettings.objects.filter(analysis=self.object).delete()
            AnalysisSettings.objects.filter(analysis=self.object).delete()
            FactorLevel.objects.filter(factor__analysis=self.object).delete()
            Factor.objects.filter(analysis=self.object).delete()
            self.object.delete()
            context={'id': id}

        return context


class ClassificationAnalysisDetailView(LoginRequiredMixin, DetailView):
    model = ClassificationAnalysis
    template_name = 'sensorimotordb/analysis/classification_analysis/classification_analysis_view.html'

    def get_context_data(self, **kwargs):
        context=super(ClassificationAnalysisDetailView,self).get_context_data(**kwargs)
        context['factors']=Factor.objects.filter(analysis=self.object).order_by('id')
        return context


CLASSIFICATION_ANALYSIS_WIZARD_FORMS = [("step1", ClassificationAnalysisForm),
                                        ("step2", ClassificationAnalysisStep2Form),
                                        ("step3", ClassificationAnalysisBaseForm),
                                        ("step4", ClassificationAnalysisStep4Form)
]

CLASSIFICATION_ANALYSIS_TEMPLATES = {"step1": 'sensorimotordb/analysis/classification_analysis/classification_analysis_create_1.html',
                                     "step2": 'sensorimotordb/analysis/classification_analysis/classification_analysis_create_2.html',
                                     "step3": 'sensorimotordb/analysis/classification_analysis/classification_analysis_create_3.html',
                                     "step4": 'sensorimotordb/analysis/classification_analysis/classification_analysis_create_4.html'
}

class CreateClassificationAnalysisWizardView(LoginRequiredMixin, SessionWizardView):

    file_storage=FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp'))

    def get_template_names(self):
        return [CLASSIFICATION_ANALYSIS_TEMPLATES[self.steps.current]]

    def get_context_data(self, form, **kwargs):
        context=super(CreateClassificationAnalysisWizardView,self).get_context_data(form, **kwargs)

        if 'create_classification_analysis_wizard_view-current_step' in self.request.POST:
            if self.request.POST['create_classification_analysis_wizard_view-current_step']=='step1':

                step_data=self.request.POST
                analysis=ClassificationAnalysis(name=step_data['step1-name'],
                    description=step_data['step1-description'])
                analysis.save()
                context['analysis']=analysis
                step_data['analysis_id']=analysis.id
                self.storage.set_step_data('step1', step_data)
                print(self.storage.get_step_data('step1'))
                context['factor_level_formset'] = ClassificationAnalysisFactorLevelFormSet(None,
                                                                                           instance=analysis,
                                                                                           queryset=Factor.objects.filter(analysis__id=analysis.id).order_by('id'), prefix='factor')
            elif self.request.POST['create_classification_analysis_wizard_view-current_step']=='step2':
                step1_data=self.storage.get_step_data('step1')
                analysis=ClassificationAnalysis.objects.get(id=step1_data['analysis_id'])
                context['analysis']=analysis
                context['factor_level_formset'] = ClassificationAnalysisFactorLevelFormSet(self.request.POST or None,
                                                                                           instance=analysis,
                                                                                           queryset=Factor.objects.filter(analysis__id=analysis.id).order_by('id'), prefix='factor')
                if context['factor_level_formset'].is_valid():
                    for factor_form in context['factor_level_formset'].forms:
                        if not factor_form.cleaned_data.get('DELETE', False):
                            factor=factor_form.save(commit=False)
                            factor.analysis=analysis
                            factor.save()
                            for level_form in factor_form.nested.forms:
                                if not level_form.cleaned_data.get('DELETE', False):
                                    level=level_form.save(commit=False)
                                    level.factor=factor
                                    level.save()
                step2_data=self.request.POST
                step2_data['analysis_id']=analysis.id
                self.storage.set_step_data('step2', step2_data)
                print(self.storage.get_step_data('step2'))
            elif self.request.POST['create_classification_analysis_wizard_view-current_step']=='step3':
                step2_data = self.storage.get_step_data('step2')
                analysis = ClassificationAnalysis.objects.get(id=step2_data['analysis_id'])
                context['analysis']=analysis
                step3_data = self.request.POST
                step3_data['analysis_id'] = analysis.id
                self.storage.set_step_data('step3', step3_data)
            elif self.request.POST['create_classification_analysis_wizard_view-current_step']=='step4':
                step3_data = self.storage.get_step_data('step3')
                analysis = ClassificationAnalysis.objects.get(id=step3_data['analysis_id'])
                context['analysis'] = analysis
                step4_data=self.request.POST
                self.storage.set_step_data('step4', step4_data)

        return context

    def render_done(self, form, **kwargs):
        """
        This method gets called when all forms passed. The method should also
        re-validate all steps to prevent manipulation. If any form fails to
        validate, `render_revalidation_failure` should get called.
        If everything is fine call `done`.
        """
        final_forms = OrderedDict()
        # walk through the form list and try to validate the data again.
        for form_key in self.get_form_list():
            form_obj = self.get_form(
                step=form_key,
                data=self.storage.get_step_data(form_key),
                files=self.storage.get_step_files(form_key)
            )
            final_forms[form_key] = form_obj

        # render the done view and reset the wizard before returning the
        # response. This is needed to prevent from rendering done with the
        # same data twice.
        done_response = self.done(final_forms.values(), form_dict=final_forms, **kwargs)
        self.storage.reset()
        return done_response

    def done(self, form_list, **kwargs):
        analysis=ClassificationAnalysis.objects.get(id=int(self.storage.get_step_data('step4')['step4-id']))
        for key, f in form_list[3].files.iteritems():
            (file,ext)=os.path.splitext(f.name)
            new_fname='classify_unit_%d%s' % (analysis.id,ext)
            analysis.script_name=new_fname
            with open(os.path.join(settings.MEDIA_ROOT, 'scripts', new_fname),'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)
            os.remove(os.path.join(settings.MEDIA_ROOT,'temp',f.name))
        analysis.save()
        return redirect('/sensorimotordb/classification_analysis/%d/' % analysis.id)


class CreateUnitClassificationTypeView(JSONResponseMixin, CreateView):
    model=UnitClassificationType

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            analysis=ClassificationAnalysis.objects.get(id=self.request.POST.get('analysis',-1))
            label=self.request.POST.get('label','')
            type=UnitClassificationType(analysis=analysis, label=label)
            type.save()
            context={
                'id': type.id,
                'label': type.label,
                'parent': None,
                'children': []
            }
        return context


class UpdateUnitClassificationTypeView(JSONResponseMixin, BaseDetailView):
    model=UnitClassificationType
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            parent=self.request.POST.get('parent',None)
            self.object=self.get_object()
            if parent is not None and int(parent)>-1:
                print(parent)
                self.object.parent=UnitClassificationType.objects.get(id=int(parent))
            else:
                self.object.parent=None
            self.object.save()
            context={}
        return context


class DeleteUnitClassificationTypeView(JSONResponseMixin, BaseDetailView):
    model=UnitClassificationType

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            id=self.object.id
            self.object=self.get_object()
            UnitClassification.objects.filter(type=self.object).delete()
            self.object.delete()
            context={'id': id, 'idx': self.request.GET.get('idx',-1)}

        return context


class CreateClusterAnalysisView(LoginRequiredMixin,CreateView):
    model = ClusterAnalysis
    template_name = 'sensorimotordb/analysis/cluster_analysis/cluster_analysis_create.html'
    form_class = ClusterAnalysisForm

    def get_context_data(self, **kwargs):
        context_data=super(CreateClusterAnalysisView,self).get_context_data(**kwargs)
        return context_data

    def get_initial(self):
        initial_data={}
        return initial_data

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        context=self.get_context_data()

        self.object=form.save()
        return redirect('/sensorimotordb/cluster_analysis/%d/' % self.object.id)


class ClusterAnalysisDetailView(LoginRequiredMixin, DetailView):
    model = ClusterAnalysis
    template_name = 'sensorimotordb/analysis/cluster_analysis/cluster_analysis_view.html'

    def get_context_data(self, **kwargs):
        context=super(ClusterAnalysisDetailView,self).get_context_data(**kwargs)
        return context


class RunAnalysisView(LoginRequiredMixin, DetailView):
    model=Analysis

    def get(self, request, *args, **kwargs):
        id=self.kwargs.get('pk', None)
        if ClassificationAnalysis.objects.filter(id=id).exists():
            return redirect('/sensorimotordb/classification_analysis/%s/run/?%s' % (id, '&'.join(['%s=%s' % (x,str(request.GET[x])) for x in request.GET])))
        elif ClusterAnalysis.objects.filter(id=id).exists():
            return redirect('/sensorimotordb/cluster_analysis/%s/run/?%s' % (id, '&'.join(['%s=%s' % (x,str(request.GET[x])) for x in request.GET])))


class RunClassificationAnalysisView(LoginRequiredMixin, CreateView):
    model = ClassificationAnalysisResults
    form_class = ClassificationAnalysisResultsForm
    template_name = 'sensorimotordb/analysis/classification_analysis/classification_analysis_run.html'

    def get_context_data(self, **kwargs):
        context=CreateView.get_context_data(self, **kwargs)
        context['analysis']=Analysis.objects.get_subclass(id=self.kwargs.get('pk',None))
        context['experiment']=Experiment.objects.get(id=self.request.GET.get('experiment',None))
        context['conditions']=Condition.objects.filter(experiment=context['experiment'])
        context['events']=Event.objects.filter(trial__condition__experiment__id=self.request.GET.get('experiment',None)).values_list('name',flat=True).distinct()
        return context

    def get_initial(self):
        initial_data=CreateView.get_initial(self)
        experiment_id=self.request.GET.get('experiment',None)
        if experiment_id is not None:
            initial_data['experiment']=Experiment.objects.get(id=experiment_id)
        analysis_id=self.kwargs.get('pk',None)
        if analysis_id is not None:
            initial_data['analysis']=Analysis.objects.get(id=analysis_id)
        return initial_data

    def form_valid(self, form):
        context=self.get_context_data()
        analysis=context['analysis']
        self.object=form.save()

        settings=ClassificationAnalysisSettings(analysis=analysis)
        settings.save()

        self.object.analysis_settings=settings
        self.object.save()

        for factor in analysis.analysis_factors.all():
            if factor.type=='time window':
                for level in factor.factor_levels.all():
                    tw_settings=TimeWindowFactorLevelSettings(analysis_settings=settings, level=level)
                    tw_settings.rel_evt=self.request.POST.get('level_%d_rel_event' % level.id)
                    rel_start=self.request.POST.get('level_%d_rel_start' % level.id)
                    if len(rel_start):
                        tw_settings.rel_start=int(rel_start)
                    rel_end=self.request.POST.get('level_%d_rel_end' % level.id)
                    if len(rel_end):
                        tw_settings.rel_end=int(rel_end)
                    tw_settings.rel_end_evt=self.request.POST.get('level_%d_rel_end_event' % level.id)
                    tw_settings.save()
            elif factor.type=='condition':
                for level in factor.factor_levels.all():
                    condition_ids=self.request.POST.getlist('level_mapping_%d' % level.id)
                    mapping=ClassificationAnalysisResultsLevelMapping(analysis_settings=settings, level=level)
                    mapping.save()
                    for condition_id in condition_ids:
                        mapping.conditions.add(Condition.objects.get(id=condition_id))
        analysis.run(self.object, settings)

        return redirect('/sensorimotordb/analysis_results/%d/' % self.object.id)


class RunClusterAnalysisView(LoginRequiredMixin, CreateView):
    model = ClusterAnalysisResults
    form_class = ClusterAnalysisResultsForm
    template_name = 'sensorimotordb/analysis/cluster_analysis/cluster_analysis_run.html'

    def get_context_data(self, **kwargs):
        context=CreateView.get_context_data(self, **kwargs)
        context['analysis']=Analysis.objects.get_subclass(id=self.kwargs.get('pk',None))
        context['experiment']=Experiment.objects.get(id=self.request.GET.get('experiment',None))
        context['conditions']=Condition.objects.filter(experiment=context['experiment'])
        context['events']=Event.objects.filter(trial__condition__experiment__id=self.request.GET.get('experiment',None)).values_list('name',flat=True).distinct()
        return context

    def get_initial(self):
        initial_data=CreateView.get_initial(self)
        experiment_id=self.request.GET.get('experiment',None)
        if experiment_id is not None:
            initial_data['experiment']=Experiment.objects.get(id=experiment_id)
        analysis_id=self.kwargs.get('pk',None)
        if analysis_id is not None:
            initial_data['analysis']=Analysis.objects.get(id=analysis_id)
        return initial_data

    def form_valid(self, form):
        context=self.get_context_data()
        analysis=context['analysis']
        self.object=form.save()

        settings=ClusterAnalysisSettings(analysis=analysis, num_clusters=int(self.request.POST['num_clusters']),
            bin_width=int(self.request.POST['bin_width']), kernel_width=int(self.request.POST['kernel_width']))
        settings.save()

        self.object.analysis_settings=settings
        self.object.save()

        num_conditions=int(self.request.POST['conditions-TOTAL_FORMS'])

        for idx in range(num_conditions):
            condition_id=int(self.request.POST['condition_%d-condition' % idx])
            time_window_condition_settings=TimeWindowConditionSettings(analysis_settings=settings,
                condition=Condition.objects.get(id=condition_id))

            time_window_condition_settings.rel_evt=self.request.POST['condition_%d_rel_event' % idx]
            rel_start=self.request.POST['condition_%d_rel_start' % idx]
            if len(rel_start):
                time_window_condition_settings.rel_start=int(rel_start)
            rel_end=self.request.POST['condition_%d_rel_end' % idx]
            if len(rel_end):
                time_window_condition_settings.rel_end=int(rel_end)
            time_window_condition_settings.rel_end_evt=self.request.POST['condition_%d_rel_end_event' % idx]

            time_window_condition_settings.baseline_evt=self.request.POST['condition_%d_baseline_event' % idx]
            baseline_start=self.request.POST['condition_%d_baseline_start' % idx]
            if len(baseline_start):
                time_window_condition_settings.baseline_start=int(baseline_start)
            baseline_end=self.request.POST['condition_%d_baseline_end' % idx]
            if len(baseline_end):
                time_window_condition_settings.baseline_end=int(baseline_end)
            time_window_condition_settings.baseline_end_evt=self.request.POST['condition_%d_baseline_end_event' % idx]

            time_window_condition_settings.save()
        analysis.run(self.object, settings)

        return redirect('/sensorimotordb/analysis_results/%d/' % self.object.id)


class AnalysisResultsDetailView(LoginRequiredMixin, DetailView):
    model=AnalysisResults

    def get(self, request, *args, **kwargs):
        id=self.kwargs.get('pk', None)
        if ClassificationAnalysisResults.objects.filter(id=id).exists():
            return redirect('/sensorimotordb/classification_analysis_results/%s/' % id)
        elif ClusterAnalysisResults.objects.filter(id=id).exists():
            return redirect('/sensorimotordb/cluster_analysis_results/%s/' % id)


class DeleteAnalysisResultsView(JSONResponseMixin,BaseDetailView):
    model=AnalysisResults
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            self.object=self.get_object()
            if ClassificationAnalysisResults.objects.filter(id=self.object.id):
                UnitClassification.objects.filter(analysis_results=self.object).delete()
                UnitAnalysisResults.objects.filter(analysis_results=self.object.delete())
                ClassificationAnalysisResults.objects.filter(id=self.object.id).delete()
            context={'id': self.request.POST['id']}

        return context


class ClassificationAnalysisResultsDetailView(AnalysisResultsDetailView):
    model=ClassificationAnalysisResults
    template_name = 'sensorimotordb/analysis/classification_analysis/classification_analysis_results_view.html'

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


class ClusterAnalysisResultsDetailView(AnalysisResultsDetailView):
    model=ClusterAnalysisResults
    template_name = 'sensorimotordb/analysis/cluster_analysis/cluster_analysis_results_view.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = AnalysisResultsDetailView.get_context_data(self, **kwargs)
        return context