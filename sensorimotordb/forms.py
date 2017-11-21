from django.contrib.auth.models import User
from django import forms
from django.forms.models import ModelForm, inlineformset_factory
from registration.forms import RegistrationForm
from registration.users import UsernameField
from sensorimotordb.models import ExperimentExportRequest, Experiment, Analysis, GraspObservationCondition, \
    GraspPerformanceCondition, ClassificationAnalysis, ANOVA, ANOVAFactor, ANOVAFactorLevel, UnitClassificationType, \
    UnitClassificationCondition, ANOVAComparison, ClassificationAnalysisResults, ClassificationAnalysisSettings
from uscbp.nested_formset import nestedformset_factory

class ClassificationAnalysisBaseForm(ModelForm):
    id=forms.CharField(max_length=100, required=True, widget=forms.HiddenInput)

    class Meta:
        model=ClassificationAnalysis
        exclude=('name','description')


class ClassificationAnalysisForm(ModelForm):
    name=forms.CharField(max_length=100, required=True)
    description=forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=True)

    class Meta:
        model=ClassificationAnalysis
        exclude=()


class ClassificationAnalysisResultsForm(ModelForm):
    analysis=forms.ModelChoiceField(queryset=ClassificationAnalysis.objects.all(),widget=forms.HiddenInput,required=True)
    analysis_settings=forms.ModelChoiceField(queryset=ClassificationAnalysisSettings.objects.none(),required=False)
    experiment=forms.ModelChoiceField(queryset=Experiment.objects.all(),widget=forms.HiddenInput,required=True)
    name=forms.CharField(max_length=100, required=True)
    description=forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=True)

    class Meta:
        model=ClassificationAnalysisResults
        exclude=()


class ANOVAForm(ModelForm):
    analysis=forms.ModelChoiceField(queryset=Analysis.objects.all(),widget=forms.HiddenInput,required=True)
    name=forms.CharField(max_length=100, required=True)
    dependent_variable=forms.CharField(max_length=100, required=True)

    class Meta:
        model=ANOVA
        exclude=()


class ANOVAFactorInlineForm(ModelForm):
    anova=forms.ModelChoiceField(queryset=ANOVA.objects.all(),widget=forms.HiddenInput,required=True)
    name=forms.CharField(max_length=100, required=True)
    type=forms.ChoiceField(choices=ANOVAFactor.ANOVA_FACTOR_TYPES, required=True)

    class Meta:
        model=ANOVAFactor
        exclude=()


class ANOVAFactorLevelInlineForm(ModelForm):
    factor=forms.ModelChoiceField(queryset=ANOVAFactor.objects.all(),widget=forms.HiddenInput,required=True)
    value=forms.CharField(max_length=100, required=True)

    class Meta:
        model=ANOVAFactorLevel
        exclude=()


ANOVAFactorLevelFormSet = lambda *a, **kw: nestedformset_factory(ANOVA,ANOVAFactor,nested_formset=inlineformset_factory(ANOVAFactor, ANOVAFactorLevel, form=ANOVAFactorLevelInlineForm, fk_name='factor', extra=0, can_delete=True), extra=0)(*a, **kw)

class UnitClassificationConditionInlineForm(ModelForm):
    id=forms.IntegerField(widget=forms.HiddenInput,required=False)
    comparisons=forms.ModelMultipleChoiceField(ANOVAComparison.objects.all().select_subclasses(),widget=forms.CheckboxSelectMultiple)
    classification_type=forms.ModelChoiceField(UnitClassificationType.objects.all(), widget=forms.HiddenInput,required=False)
    class Meta:
        model=UnitClassificationCondition
        exclude=('lft','tree_id','rght','level')

UnitClassificationTypeConditionFormSet = lambda *a, **kw: nestedformset_factory(ClassificationAnalysis,UnitClassificationType,nested_formset=inlineformset_factory(UnitClassificationType, UnitClassificationCondition, form=UnitClassificationConditionInlineForm, fk_name='classification_type', extra=0, can_delete=True), fk_name='analysis', extra=0, fields=['label','analysis'])(*a, **kw)


class GraspObservationConditionForm(ModelForm):

     class Meta:
         model = GraspObservationCondition
         exclude=('experiment','type')


class GraspPerformanceConditionForm(ModelForm):

    class Meta:
        model = GraspPerformanceCondition
        exclude=('experiment','type')

class ExperimentForm(ModelForm):

    class Meta:
        model = Experiment
        exclude=('collator','creation_time','last_modified_time')


class ExperimentExportRequestForm(ModelForm):
    requesting_user=forms.ModelChoiceField(User.objects.all(),widget=forms.HiddenInput,required=False)
    rationale = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=True)
    experiment = forms.ModelChoiceField(Experiment.objects.all(),widget=forms.HiddenInput,required=False)

    class Meta:
        model = ExperimentExportRequest
        exclude=('activation_key','status')


class ExperimentExportRequestDenyForm(forms.Form):
    reason=forms.CharField(widget=forms.Textarea(attrs={'cols':'57', 'rows':'5'}), required=True)


class ExperimentExportRequestApproveForm(forms.Form):
    reason=forms.CharField(widget=forms.Textarea(attrs={'cols':'57', 'rows':'5'}), required=True)


class SensoriMotorDBRegistrationForm(RegistrationForm):
    first_name = forms.CharField(max_length=254, required=True)
    last_name = forms.CharField(max_length=254, required=True)

    class Meta:
        model = User
        fields = (UsernameField(),'first_name','last_name', "email")


class UserProfileForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput(render_value=False),required=False)
    password2 = forms.CharField(widget=forms.PasswordInput(render_value=False),required=False)

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.

        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(u'You must type the same password each time')
        return self.cleaned_data

    class Meta:
        model=User
        fields = ('first_name','last_name','email')