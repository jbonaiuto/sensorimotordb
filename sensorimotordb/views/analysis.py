from collections import OrderedDict
from django.shortcuts import redirect
from django.views.generic import DetailView, CreateView, TemplateView
from django.views.generic.detail import BaseDetailView
from formtools.wizard.views import SessionWizardView
from tastypie.models import ApiKey
from sensorimotordb.forms import ClassificationAnalysisForm, ClassificationAnalysisBaseForm, UnitClassificationTypeConditionFormSet, ANOVAForm, ANOVAFactorLevelFormSet, ClassificationAnalysisResultsForm
from sensorimotordb.models import AnalysisResults, ClassificationAnalysis, ANOVA, ANOVAComparison, UnitClassificationType, Analysis, ANOVAFactor, ANOVAEffect, ANOVAOneWayPairwiseComparison, ANOVATwoWayPairwiseComparison, ANOVAThreeWayPairwiseComparison, ANOVAFactorLevel, UnitClassificationCondition, Condition, Event, ClassificationAnalysisResultsLevelMapping, ClassificationAnalysisResults, Experiment, ClassificationAnalysisSettings, TimeWindowFactorLevelSettings, UnitClassification, UnitAnalysisResults
from sensorimotordb.views import LoginRequiredMixin, JSONResponseMixin
from uscbp import settings

class AnalysisListDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'sensorimotordb/analysis/analysis_list_view.html'

    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)
        context['classification_analyses']=ClassificationAnalysis.objects.all()
        return context


class DeleteClassificationAnalysisView(JSONResponseMixin,BaseDetailView):
    model=ClassificationAnalysis
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            self.object=self.get_object()
            id=self.object.id
            UnitClassificationCondition.objects.filter(classification_type__analysis=self.object).delete()
            UnitClassificationType.objects.filter(analysis=self.object).delete()
            ANOVAComparison.objects.filter(anova__analysis=self.object).delete()
            ClassificationAnalysisResultsLevelMapping.objects.filter(analysis_settings__analysis=self.object).delete()
            ANOVAFactorLevel.objects.filter(factor__anova__analysis=self.object).delete()
            ANOVAFactor.objects.filter(anova__analysis=self.object).delete()
            ANOVA.objects.filter(analysis=self.object).delete()
            self.object.delete()
            context={'id': id}

        return context


class ClassificationAnalysisDetailView(LoginRequiredMixin, DetailView):
    model = ClassificationAnalysis
    template_name = 'sensorimotordb/analysis/classification_analysis/classification_analysis_view.html'

    def get_context_data(self, **kwargs):
        context=super(ClassificationAnalysisDetailView,self).get_context_data(**kwargs)
        context['anovas']=ANOVA.objects.filter(analysis=self.object).order_by('id')
        context['anova_comparisons']=[]
        for anova in context['anovas']:
            for comparison in ANOVAComparison.objects.filter(anova=anova).select_subclasses().order_by('id'):
                context['anova_comparisons'].append(comparison)
        return context


CLASSIFICATION_ANALYSIS_WIZARD_FORMS = [("step1", ClassificationAnalysisForm),
                                        ("step2", ClassificationAnalysisBaseForm),
                                        ("step3", ClassificationAnalysisBaseForm),
                                        ("step4", ClassificationAnalysisBaseForm)
]

CLASSIFICATION_ANALYSIS_TEMPLATES = {"step1": 'sensorimotordb/analysis/classification_analysis/classification_analysis_create_1.html',
                                     "step2": 'sensorimotordb/analysis/classification_analysis/classification_analysis_create_2.html',
                                     "step3": 'sensorimotordb/analysis/classification_analysis/classification_analysis_create_3.html',
                                     "step4": 'sensorimotordb/analysis/classification_analysis/classification_analysis_create_4.html'
}

class CreateClassificationAnalysisWizardView(LoginRequiredMixin, SessionWizardView):

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
            elif self.request.POST['create_classification_analysis_wizard_view-current_step']=='step2':
                step1_data=self.storage.get_step_data('step1')
                analysis=ClassificationAnalysis.objects.get(id=step1_data['analysis_id'])
                context['analysis']=analysis
                context['classification_type_formset']=UnitClassificationTypeConditionFormSet(None,
                    instance=analysis, queryset=UnitClassificationType.objects.filter(analysis=analysis),
                    prefix='classification_type')
                context['anovas']=ANOVA.objects.filter(analysis=analysis).order_by('id')
                context['anova_comparisons']=[]
                for anova in context['anovas']:
                    for comparison in ANOVAComparison.objects.filter(anova=anova).select_subclasses().order_by('id'):
                        context['anova_comparisons'].append(comparison)
                step2_data=self.request.POST
                step2_data['analysis_id']=analysis.id
                self.storage.set_step_data('step2', step2_data)
                print(self.storage.get_step_data('step2'))
            elif self.request.POST['create_classification_analysis_wizard_view-current_step']=='step3':
                step3_data=self.request.POST
                analysis=ClassificationAnalysis.objects.get(id=step3_data['step3-id'])
                context['analysis']=analysis
                context['classification_type_formset']=UnitClassificationTypeConditionFormSet(self.request.POST,
                    instance=analysis, queryset=UnitClassificationType.objects.filter(analysis=analysis), prefix='classification_type')
                if context['classification_type_formset'].is_valid():
                    for classification_type_form in context['classification_type_formset'].forms:
                        if not classification_type_form.cleaned_data.get('DELETE', False):
                            classification_type=classification_type_form.save(commit=False)
                            classification_type.analysis=analysis
                            classification_type.save()
                            for condition_form in classification_type_form.nested.forms:
                                if not condition_form.cleaned_data.get('DELETE', False):
                                    condition=condition_form.save(commit=False)
                                    condition.classification_type=classification_type
                                    condition.save()
                                    condition_form.save_m2m()
                step3_data=self.request.POST
                step3_data['analysis_id']=analysis.id
                self.storage.set_step_data('step3', step3_data)
            elif self.request.POST['create_classification_analysis_wizard_view-current_step']=='step4':
                step4_data=self.request.POST
                analysis=ClassificationAnalysis.objects.get(id=step4_data['step4-id'])
                context['analysis']=analysis
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
        analysis=int(self.storage.get_step_data('step4')['step4-id'])
        return redirect('/sensorimotordb/classification_analysis/%d/' % analysis)


#class CreateClassificationAnalysisView(LoginRequiredMixin,CreateView):
#    model = ClassificationAnalysis
#    form_class = ClassificationAnalysisForm
#    template_name = 'sensorimotordb/analysis/classification_analysis_create.html'
#
#    def get_context_data(self, **kwargs):
#        context_data=super(CreateClassificationAnalysisView,self).get_context_data(**kwargs)
#        return context_data
#
#    def form_valid(self, form):
#        """
#        If the form is valid, save the associated model.
#        """
#        self.object=form.save()
#        return redirect('/sensorimotordb/classification_analysis/%d/edit/' % self.object.id)
#
#
#class UpdateClassificationAnalysisView(LoginRequiredMixin,UpdateView):
#    model=ClassificationAnalysis
#    template_name = 'sensorimotordb/analysis/classification_analysis_edit.html'
#    form_class = ClassificationAnalysisForm
#
#    def form_valid(self, form):
#        self.object=form.save()
#
#        return redirect('/sensorimotordb/classification_analysis/%d/edit2/' % self.object.id)
#
#
#class Update2ClassificationAnalysisView(LoginRequiredMixin,UpdateView):
#    model=ClassificationAnalysis
#    template_name = 'sensorimotordb/analysis/classification_analysis_edit2.html'
#    form_class = ClassificationAnalysisForm
#
#    def get_context_data(self, **kwargs):
#        context_data=super(Update2ClassificationAnalysisView,self).get_context_data(**kwargs)
#        context_data['classification_type_formset']=UnitClassificationTypeConditionFormSet(self.request.POST or None, instance=self.object,
#            queryset=UnitClassificationType.objects.filter(analysis=self.object), prefix='classification_type')
#        context_data['anovas']=ANOVA.objects.filter(analysis=self.object).order_by('id')
#        context_data['anova_comparisons']=[]
#        for anova in context_data['anovas']:
#            for comparison in ANOVAComparison.objects.filter(anova=anova).select_subclasses().order_by('id'):
#                context_data['anova_comparisons'].append(comparison)
#
#        return context_data
#
#    def form_valid(self, form):
#
#        context=self.get_context_data()
#        classification_type_formset = context['classification_type_formset']
#
#        if classification_type_formset.is_valid():
#            self.object=form.save()
#            for classification_type_form in classification_type_formset.forms:
#                if not classification_type_form.cleaned_data.get('DELETE', False):
#                    classification_type=classification_type_form.save(commit=False)
#                    classification_type.analysis=self.object
#                    classification_type.save()
#                    for condition_form in classification_type_form.nested.forms:
#                        if not condition_form.cleaned_data.get('DELETE', False):
#                            condition=condition_form.save(commit=False)
#                            condition.classification_type=classification_type
#                            condition.save()
#                            condition_form.save_m2m()
#
#        else:
#            return self.form_invalid(form)
#
#        return redirect('/sensorimotordb/classification_analysis/%d/edit3/' % self.object.id)
#
#
#class Update3ClassificationAnalysisView(LoginRequiredMixin,UpdateView):
#    model=ClassificationAnalysis
#    template_name = 'sensorimotordb/analysis/classification_analysis_edit3.html'
#    form_class = ClassificationAnalysisForm
#
#    def get_context_data(self, **kwargs):
#        context_data=super(Update3ClassificationAnalysisView,self).get_context_data(**kwargs)
#        context_data['classification_types']=UnitClassificationType.objects.filter(analysis=self.object)
#
#        return context_data
#
#    def form_valid(self, form):
#        context=self.get_context_data()
#        self.object=form.save()
#        return redirect('/sensorimotordb/classification_analysis/%d/' % self.object.id)


class CreateANOVAView(LoginRequiredMixin,CreateView):
    model = ANOVA
    template_name = 'sensorimotordb/analysis/classification_analysis/anova_create.html'
    form_class = ANOVAForm

    def get_context_data(self, **kwargs):
        context_data=super(CreateANOVAView,self).get_context_data(**kwargs)
        context_data['factor_level_formset']=ANOVAFactorLevelFormSet(self.request.POST or None, instance=self.object,
            queryset=ANOVA.objects.filter(analysis__id=self.request.GET.get('analysis','')).order_by('id'), prefix='factor')
        return context_data

    def get_initial(self):
        initial_data={'analysis': Analysis.objects.get(id=self.request.GET.get('analysis',''))}
        return initial_data

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        context=self.get_context_data()
        factor_level_formset = context['factor_level_formset']

        self.object=form.save()
        if factor_level_formset.is_valid():
            for factor_form in factor_level_formset.forms:
                if not factor_form.cleaned_data.get('DELETE', False):
                    factor=factor_form.save(commit=False)
                    factor.anova=self.object
                    factor.save()
                    for level_form in factor_form.nested.forms:
                        if not level_form.cleaned_data.get('DELETE', False):
                            level=level_form.save(commit=False)
                            level.factor=factor
                            level.save()

            # Create comparisons
            factors=ANOVAFactor.objects.filter(anova=self.object)

            # Main effect
            for factor in factors:
                main_effect=ANOVAEffect(anova=self.object)
                main_effect.save()
                main_effect.factors.add(factor)
                main_effect.save()

            # Two-way interactions
            for f_idx1, factor1 in enumerate(factors):
                for f_idx2, factor2 in enumerate(factors):
                    if f_idx2>f_idx1:
                        interaction_effect=ANOVAEffect(anova=self.object)
                        interaction_effect.save()
                        interaction_effect.factors.add(factor1)
                        interaction_effect.factors.add(factor2)
                        interaction_effect.save()

            # Three-way interaction
            if factors.count()==3:
                interaction_effect=ANOVAEffect(anova=self.object)
                interaction_effect.save()
                for factor in factors:
                    interaction_effect.factors.add(factor)
                interaction_effect.save()

            # Main effect pairwise comparisons
            for f_idx, factor in enumerate(factors):
                for l_idx1, level1 in enumerate(factor.anova_factor_levels.all()):
                    for l_idx2, level2 in enumerate(factor.anova_factor_levels.all()):
                        if l_idx2>l_idx1:
                            pairwise=ANOVAOneWayPairwiseComparison(anova=self.object, factor=factor,level1=level1, level2=level2, relationship='gt')
                            pairwise.save()
                            pairwise=ANOVAOneWayPairwiseComparison(anova=self.object, factor=factor,level1=level1, level2=level2, relationship='lt')
                            pairwise.save()

            # Two-way interactions pairwise comparisons
            for f_idx1, factor1 in enumerate(factors):
                for f1_l_idx, f1_level in enumerate(factor1.anova_factor_levels.all()):
                    for f_idx2, factor2 in enumerate(factors):
                        if not f_idx2==f_idx1:
                            for f2_l_idx1, f2_level1 in enumerate(factor2.anova_factor_levels.all()):
                                for f2_l_idx2, f2_level2 in enumerate(factor2.anova_factor_levels.all()):
                                    if f2_l_idx2>f2_l_idx1:
                                        pairwise=ANOVATwoWayPairwiseComparison(anova=self.object, factor1=factor1, factor1_level=f1_level,
                                            factor2=factor2, factor2_level1=f2_level1, factor2_level2=f2_level2,
                                            relationship='gt')
                                        pairwise.save()
                                        pairwise=ANOVATwoWayPairwiseComparison(anova=self.object, factor1=factor1, factor1_level=f1_level,
                                            factor2=factor2, factor2_level1=f2_level1, factor2_level2=f2_level2,
                                            relationship='lt')
                                        pairwise.save()

            # Three-way interactions pairwise comparisons
            for f_idx1, factor1 in enumerate(factors):
                for f1_l_idx, f1_level in enumerate(factor1.anova_factor_levels.all()):
                    for f_idx2, factor2 in enumerate(factors):
                        if not f_idx2==f_idx1:
                            for f2_l_idx, f2_level in enumerate(factor2.anova_factor_levels.all()):
                                for f_idx3, factor3 in enumerate(factors):
                                    if not f_idx3==f_idx1 and not f_idx3==f_idx2:
                                        for f3_l_idx1, f3_level1 in enumerate(factor3.anova_factor_levels.all()):
                                            for f3_l_idx2, f3_level2 in enumerate(factor3.anova_factor_levels.all()):
                                                if f3_l_idx2>f3_l_idx1:
                                                    pairwise=ANOVAThreeWayPairwiseComparison(anova=self.object, factor1=factor1, factor1_level=f1_level,
                                                        factor2=factor2, factor2_level=f2_level, factor3=factor3,
                                                        factor3_level1=f3_level1, factor3_level2=f3_level2,
                                                        relationship='gt')
                                                    pairwise.save()
                                                    pairwise=ANOVAThreeWayPairwiseComparison(anova=self.object, factor1=factor1, factor1_level=f1_level,
                                                        factor2=factor2, factor2_level=f2_level, factor3=factor3,
                                                        factor3_level1=f3_level1, factor3_level2=f3_level2,
                                                        relationship='lt')
                                                    pairwise.save()
        else:
            return self.form_invalid(form)

        return redirect('/sensorimotordb/anova/%d/?action=create' % self.object.id)


class ANOVADetailView(LoginRequiredMixin, DetailView):
    model=ANOVA
    template_name = 'sensorimotordb/analysis/classification_analysis/anova_view.html'

    def get_context_data(self, **kwargs):
        context_data=super(ANOVADetailView,self).get_context_data(**kwargs)
        context_data['factors']=ANOVAFactor.objects.filter(anova=self.object)
        return context_data


class DeleteANOVAView(JSONResponseMixin,BaseDetailView):
    model=ANOVA

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            id=self.object.id
            self.object=self.get_object()
            ANOVAEffect.objects.filter(factors__anova=self.object).delete()
            ANOVAOneWayPairwiseComparison.objects.filter(factor__anova=self.object).delete()
            ANOVATwoWayPairwiseComparison.objects.filter(factor1__anova=self.object).delete()
            ANOVAThreeWayPairwiseComparison.objects.filter(factor1__anova=self.object).delete()
            ANOVAFactorLevel.objects.filter(factor__anova=self.object).delete()
            ANOVAFactor.objects.filter(anova=self.object).delete()
            self.object.delete()
            context={'id': id}

        return context


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


class DeleteUnitClassificationConditionView(JSONResponseMixin, BaseDetailView):
    model=UnitClassificationCondition

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            id=self.object.id
            self.object=self.get_object()
            self.object.delete()
            context={'id': id, 'type_idx': self.request.GET.get('type_idx',-1), 'idx': self.request.GET.get('idx',-1)}

        return context


class DeleteUnitClassificationTypeView(JSONResponseMixin, BaseDetailView):
    model=UnitClassificationType

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            id=self.object.id
            self.object=self.get_object()
            self.object.delete()
            context={'id': id, 'idx': self.request.GET.get('idx',-1)}

        return context


class RunAnalysisView(LoginRequiredMixin, DetailView):
    model=Analysis

    def get(self, request, *args, **kwargs):
        id=self.kwargs.get('pk', None)
        if ClassificationAnalysis.objects.filter(id=id).exists():
            return redirect('/sensorimotordb/classification_analysis/%s/run/?%s' % (id, '&'.join(['%s=%s' % (x,str(request.GET[x])) for x in request.GET])))


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
        for anova in analysis.analysis_anovas.all():
            for factor in anova.anova_factors.all():
                if factor.type=='time window':
                    for level in factor.anova_factor_levels.all():
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
                    for level in factor.anova_factor_levels.all():
                        condition_ids=self.request.POST.getlist('level_mapping_%d' % level.id)
                        mapping=ClassificationAnalysisResultsLevelMapping(analysis_settings=settings, level=level)
                        mapping.save()
                        for condition_id in condition_ids:
                            mapping.conditions.add(Condition.objects.get(id=condition_id))
        analysis.run(self.object, settings)

        return redirect('/sensorimotordb/analysis_results/%d/' % self.object.id)


#class CreateVisuomotorClassificationAnalysisView(LoginRequiredMixin,CreateView):
#    model = VisuomotorClassificationAnalysisResults
#    form_class = VisuomotorClassificationAnalysisResultsForm
#    template_name = 'sensorimotordb/analysis/visuomotor_classification_analysis_results_create.html'
#
#    def get_context_data(self, **kwargs):
#        context_data=super(CreateVisuomotorClassificationAnalysisView,self).get_context_data(**kwargs)
#        context_data['factors']=Factor.objects.filter(analysis=VisuomotorClassificationAnalysis.objects.filter()[0]).prefetch_related('levels')
#        context_data['conditions']=[]
#        experiment_id=self.request.GET.get('experiment',None)
#        if experiment_id is not None:
#            context_data['conditions']=Condition.objects.filter(experiment__id=experiment_id)
#        return context_data
#
#    def get_form(self, form_class=None):
#        form=super(CreateVisuomotorClassificationAnalysisView,self).get_form(form_class=form_class)
#        experiment_id=self.request.GET.get('experiment',None)
#        if experiment_id is not None:
#            all_evts=Event.objects.filter(trial__condition__experiment__id=experiment_id).values_list('name',flat=True).distinct()
#            form.fields['baseline_rel_evt'].choices=[]
#            form.fields['baseline_rel_end_evt'].choices=[('','')]
#            form.fields['obj_view_woi_rel_evt'].choices=[]
#            form.fields['obj_view_woi_rel_end_evt'].choices=[('','')]
#            for evt in all_evts:
#                form.fields['baseline_rel_evt'].choices.append((evt,evt))
#                form.fields['baseline_rel_end_evt'].choices.append((evt,evt))
#                form.fields['obj_view_woi_rel_evt'].choices.append((evt,evt))
#                form.fields['obj_view_woi_rel_end_evt'].choices.append((evt,evt))
#
#            form.fields['grasp_woi_rel_evt'].choices=[]
#            form.fields['grasp_woi_rel_end_evt'].choices=[('','')]
#            execution_conditions=GraspPerformanceCondition.objects.filter(experiment__id=experiment_id)
#            motor_evts=[]
#            for evt in all_evts:
#                for condition in execution_conditions:
#                    if Event.objects.filter(name=evt, trial__condition=condition).count()>0 and not evt in motor_evts:
#                        motor_evts.append(evt)
#            for evt in motor_evts:
#                form.fields['grasp_woi_rel_evt'].choices.append((evt,evt))
#                form.fields['grasp_woi_rel_end_evt'].choices.append((evt,evt))
#
#        return form
#
#    def get_initial(self):
#        initial_data={'analysis': VisuomotorClassificationAnalysis.objects.filter()[0]}
#        experiment_id=self.request.GET.get('experiment',None)
#        if experiment_id is not None:
#            initial_data['experiment']=experiment_id
#        return initial_data
#
#    def form_valid(self, form):
#        """
#        If the form is valid, save the associated model.
#        """
#        self.object=form.save()
#        for field in self.request.POST:
#            if field.startswith('level_mapping_'):
#                level_id=int(field.split('_')[-1])
#                condition_ids=self.request.POST.getlist(field)
#                mapping=AnalysisResultsLevelMapping(level=Level.objects.get(id=level_id), analysis_results=self.object)
#                mapping.save()
#                for condition_id in condition_ids:
#                    mapping.conditions.add(Condition.objects.get(id=condition_id))
#        analysis=VisuomotorClassificationAnalysis.objects.get(id=self.object.analysis.id)
#        analysis.run(self.object)
#        return redirect('/sensorimotordb/experiment/%d/' % self.object.experiment.id)
#
#
#class CreateMirrorTypeClassificationAnalysisView(LoginRequiredMixin,CreateView):
#    model = MirrorTypeClassificationAnalysisResults
#    form_class = MirrorTypeClassificationAnalysisResultsForm
#    template_name = 'sensorimotordb/analysis/mirror_type_classification_analysis_results_create.html'
#
#    def get_context_data(self, **kwargs):
#        context_data=super(CreateMirrorTypeClassificationAnalysisView,self).get_context_data(**kwargs)
#        context_data['factors']=Factor.objects.filter(analysis=MirrorTypeClassificationAnalysis.objects.filter()[0]).prefetch_related('levels')
#        context_data['conditions']=[]
#        experiment_id=self.request.GET.get('experiment',None)
#        if experiment_id is not None:
#            context_data['conditions']=Condition.objects.filter(experiment__id=experiment_id)
#        return context_data
#
#    def get_form(self, form_class=None):
#        form=super(CreateMirrorTypeClassificationAnalysisView,self).get_form(form_class=form_class)
#        experiment_id=self.request.GET.get('experiment',None)
#        if experiment_id is not None:
#            all_evts=Event.objects.filter(trial__condition__experiment__id=experiment_id).values_list('name',flat=True).distinct()
#            form.fields['baseline_rel_evt'].choices=[]
#            form.fields['baseline_rel_end_evt'].choices=[('','')]
#            form.fields['reach_woi_rel_evt'].choices=[]
#            form.fields['reach_woi_rel_end_evt'].choices=[('','')]
#            form.fields['hold_woi_rel_evt'].choices=[]
#            form.fields['hold_woi_rel_end_evt'].choices=[('','')]
#            for evt in all_evts:
#                form.fields['baseline_rel_evt'].choices.append((evt,evt))
#                form.fields['baseline_rel_end_evt'].choices.append((evt,evt))
#                form.fields['reach_woi_rel_evt'].choices.append((evt,evt))
#                form.fields['reach_woi_rel_end_evt'].choices.append((evt,evt))
#                form.fields['hold_woi_rel_evt'].choices.append((evt,evt))
#                form.fields['hold_woi_rel_end_evt'].choices.append((evt,evt))
#
#        return form
#
#    def get_initial(self):
#        initial_data={'analysis': MirrorTypeClassificationAnalysis.objects.filter()[0]}
#        experiment_id=self.request.GET.get('experiment',None)
#        if experiment_id is not None:
#            initial_data['experiment']=experiment_id
#        return initial_data
#
#    def form_valid(self, form):
#        """
#        If the form is valid, save the associated model.
#        """
#        self.object=form.save()
#        for field in self.request.POST:
#            if field.startswith('level_mapping_'):
#                level_id=int(field.split('_')[-1])
#                condition_ids=self.request.POST.getlist(field)
#                mapping=AnalysisResultsLevelMapping(level=Level.objects.get(id=level_id), analysis_results=self.object)
#                mapping.save()
#                for condition_id in condition_ids:
#                    mapping.conditions.add(Condition.objects.get(id=condition_id))
#        analysis=MirrorTypeClassificationAnalysis.objects.get(id=self.object.analysis.id)
#        analysis.run(self.object)
#        return redirect('/sensorimotordb/experiment/%d/' % self.object.experiment.id)


class AnalysisResultsDetailView(LoginRequiredMixin, DetailView):
    model=AnalysisResults

    def get(self, request, *args, **kwargs):
        id=self.kwargs.get('pk', None)
        if ClassificationAnalysisResults.objects.filter(id=id).exists():
            return redirect('/sensorimotordb/classification_analysis_results/%s/' % id)


class DeleteAnalysisResultsView(JSONResponseMixin,BaseDetailView):
    model=AnalysisResults
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            self.object=self.get_object()
            if ClassificationAnalysisResults.objects.filter(id=self.object.id):
                UnitAnalysisResults.objects.filter(analysis_results=self.object).delete()
                UnitClassification.objects.filter(analysis_results=self.object).delete()
                ClassificationAnalysisResults.objects.get(id=self.object.id).delete()
                self.object.delete()
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
        context['factors']=ANOVAFactor.objects.filter(anova__analysis=self.object.analysis)
        context['bodb_server']=settings.BODB_SERVER
        context['api_key']=ApiKey.objects.get(user=self.request.user).key
        context['username']=self.request.user.username
        return context


#class DeleteVisuomotorClassificationAnalysisResultsView(JSONResponseMixin,BaseDetailView):
#    model=VisuomotorClassificationAnalysisResults
#
#    def get_context_data(self, **kwargs):
#        context={'msg':u'No POST data sent.' }
#        if self.request.is_ajax():
#            self.object=self.get_object()
#            UnitAnalysisResults.objects.filter(analysis_results=self.object).delete()
#            UnitClassification.objects.filter(analysis_results=self.object).delete()
#            VisuomotorClassificationUnitAnalysisResults.objects.filter(analysis_results=self.object).delete()
#            AnalysisResultsLevelMapping.objects.filter(analysis_results=self.object).delete()
#            self.object.delete()
#            context={'id': self.request.POST['id']}
#
#        return context


#class MirrorTypeClassificationAnalysisResultsDetailView(AnalysisResultsDetailView):
#    model=MirrorTypeClassificationAnalysisResults
#    template_name = 'sensorimotordb/analysis/mirror_type_classification_analysis_results_view.html'
#
#    def get(self, request, *args, **kwargs):
#        self.object = self.get_object()
#        context = self.get_context_data(object=self.object)
#        return self.render_to_response(context)
#
#    def get_context_data(self, **kwargs):
#        context = AnalysisResultsDetailView.get_context_data(self, **kwargs)
#        context['factors']=Factor.objects.filter(analysis=self.object.analysis)
#        context['bodb_server']=settings.BODB_SERVER
#        context['api_key']=ApiKey.objects.get(user=self.request.user).key
#        context['username']=self.request.user.username
#        return context


#class DeleteMirrorTypeClassificationAnalysisResultsView(JSONResponseMixin,BaseDetailView):
#    model=MirrorTypeClassificationAnalysisResults
#
#    def get_context_data(self, **kwargs):
#        context={'msg':u'No POST data sent.' }
#        if self.request.is_ajax():
#            self.object=self.get_object()
#            UnitAnalysisResults.objects.filter(analysis_results=self.object).delete()
#            UnitClassification.objects.filter(analysis_results=self.object).delete()
#            MirrorTypeClassificationUnitAnalysisResults.objects.filter(analysis_results=self.object).delete()
#            AnalysisResultsLevelMapping.objects.filter(analysis_results=self.object).delete()
#            self.object.delete()
#            context={'id': self.request.POST['id']}
#
#        return context


#class VisuomotorClassificationAnalysisResultsDetailView(AnalysisResultsDetailView):
#    model=VisuomotorClassificationAnalysisResults
#    template_name = 'sensorimotordb/analysis/visuomotor_classification_analysis_results_view.html'
#
#    def get(self, request, *args, **kwargs):
#        self.object = self.get_object()
#        context = self.get_context_data(object=self.object)
#        return self.render_to_response(context)
#
#    def get_context_data(self, **kwargs):
#        context = AnalysisResultsDetailView.get_context_data(self, **kwargs)
#        context['factors']=Factor.objects.filter(analysis=self.object.analysis)
#        context['bodb_server']=settings.BODB_SERVER
#        context['api_key']=ApiKey.objects.get(user=self.request.user).key
#        context['username']=self.request.user.username
#        return context


#class DeleteVisuomotorClassificationAnalysisResultsView(JSONResponseMixin,BaseDetailView):
#    model=VisuomotorClassificationAnalysisResults
#
#    def get_context_data(self, **kwargs):
#        context={'msg':u'No POST data sent.' }
#        if self.request.is_ajax():
#            self.object=self.get_object()
#            UnitAnalysisResults.objects.filter(analysis_results=self.object).delete()
#            UnitClassification.objects.filter(analysis_results=self.object).delete()
#            VisuomotorClassificationUnitAnalysisResults.objects.filter(analysis_results=self.object).delete()
#            AnalysisResultsLevelMapping.objects.filter(analysis_results=self.object).delete()
#            self.object.delete()
#            context={'id': self.request.POST['id']}
#
#        return context


#class MirrorTypeClassificationAnalysisResultsDetailView(AnalysisResultsDetailView):
#    model=MirrorTypeClassificationAnalysisResults
#    template_name = 'sensorimotordb/analysis/mirror_type_classification_analysis_results_view.html'
#
#    def get(self, request, *args, **kwargs):
#        self.object = self.get_object()
#        context = self.get_context_data(object=self.object)
#        return self.render_to_response(context)
#
#    def get_context_data(self, **kwargs):
#        context = AnalysisResultsDetailView.get_context_data(self, **kwargs)
#        context['factors']=Factor.objects.filter(analysis=self.object.analysis)
#        context['bodb_server']=settings.BODB_SERVER
#        context['api_key']=ApiKey.objects.get(user=self.request.user).key
#        context['username']=self.request.user.username
#        return context


#class DeleteMirrorTypeClassificationAnalysisResultsView(JSONResponseMixin,BaseDetailView):
#    model=MirrorTypeClassificationAnalysisResults
#
#    def get_context_data(self, **kwargs):
#        context={'msg':u'No POST data sent.' }
#        if self.request.is_ajax():
#            self.object=self.get_object()
#            UnitAnalysisResults.objects.filter(analysis_results=self.object).delete()
#            UnitClassification.objects.filter(analysis_results=self.object).delete()
#            MirrorTypeClassificationUnitAnalysisResults.objects.filter(analysis_results=self.object).delete()
#            AnalysisResultsLevelMapping.objects.filter(analysis_results=self.object).delete()
#            self.object.delete()
#            context={'id': self.request.POST['id']}
#
#        return context