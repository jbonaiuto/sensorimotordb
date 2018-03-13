from django.contrib.auth.models import User
from django import forms
from django.forms.models import ModelForm, inlineformset_factory
from registration.forms import RegistrationForm
from registration.users import UsernameField
from sensorimotordb.models import ExperimentExportRequest, Experiment, GraspObservationCondition, \
    GraspPerformanceCondition, ClassificationAnalysis, Factor, FactorLevel, UnitClassificationType, \
    ClassificationAnalysisResults, ClassificationAnalysisSettings, ClusterAnalysis, ClusterAnalysisSettings, \
    ClusterAnalysisResults, Species, Condition, GraspCondition
from uscbp.nested_formset import nestedformset_factory


class ClusterAnalysisForm(ModelForm):
    name=forms.CharField(max_length=100, required=True)
    description=forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=True)
    mds_type=forms.ChoiceField(choices=ClusterAnalysis.MDS_TYPE_CHOICES, required=False)

    class Meta:
        model=ClusterAnalysis
        exclude=()


class ClusterAnalysisResultsForm(ModelForm):
    analysis=forms.ModelChoiceField(queryset=ClusterAnalysis.objects.all(),widget=forms.HiddenInput,required=True)
    analysis_settings=forms.ModelChoiceField(queryset=ClusterAnalysisSettings.objects.none(),required=False)
    experiment=forms.ModelChoiceField(queryset=Experiment.objects.all(),widget=forms.HiddenInput,required=True)
    name=forms.CharField(max_length=100, required=True)
    description=forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=True)

    class Meta:
        model=ClusterAnalysisResults
        exclude=()


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


class ClassificationAnalysisStep2Form(ModelForm):
    id=forms.CharField(max_length=100, required=True, widget=forms.HiddenInput)

    class Meta:
        model=ClassificationAnalysis
        exclude=('name','description')


class ClassificationAnalysisStep4Form(ModelForm):
    id=forms.CharField(max_length=100, required=True, widget=forms.HiddenInput)
    script_file=forms.FileField()

    class Meta:
        model=ClassificationAnalysis
        exclude=('name','description')

class ClassificationAnalysisResultsForm(ModelForm):
    analysis=forms.ModelChoiceField(queryset=ClassificationAnalysis.objects.all(),widget=forms.HiddenInput,required=True)
    analysis_settings=forms.ModelChoiceField(queryset=ClassificationAnalysisSettings.objects.none(),required=False)
    experiment=forms.ModelChoiceField(queryset=Experiment.objects.all(),widget=forms.HiddenInput,required=True)
    name=forms.CharField(max_length=100, required=True)
    description=forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=True)

    class Meta:
        model=ClassificationAnalysisResults
        exclude=()


class FactorInlineForm(ModelForm):
    analysis=forms.ModelChoiceField(queryset=ClassificationAnalysis.objects.all(),widget=forms.HiddenInput,required=True)
    name=forms.CharField(max_length=100, required=True)
    type=forms.ChoiceField(choices=Factor.FACTOR_TYPES, required=True)

    class Meta:
        model=Factor
        exclude=()


class FactorLevelInlineForm(ModelForm):
    factor=forms.ModelChoiceField(queryset=Factor.objects.all(),widget=forms.HiddenInput,required=True)
    value=forms.CharField(max_length=100, required=True)

    class Meta:
        model=FactorLevel
        exclude=()


ClassificationAnalysisFactorLevelFormSet = lambda *a, **kw: nestedformset_factory(ClassificationAnalysis,Factor,
                                                                                  nested_formset=inlineformset_factory(Factor, FactorLevel,
                                                                                                                       form=FactorLevelInlineForm,
                                                                                                                       fk_name='factor', extra=0,
                                                                                                                       can_delete=True), extra=0)(*a, **kw)


class ExperimentCreateForm(ModelForm):
    collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    last_modified_by = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    title = forms.CharField(max_length=200, required=True)
    brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=True)
    narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=False)
    subject_species=forms.ModelChoiceField(queryset=Species.objects.all(), required=True)
    data_file=forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=True)

    class Meta:
        model = Experiment
        exclude=('creation_time','last_modified_time')


class ExperimentImportForm(ModelForm):
    class Meta:
        model=Experiment
        exclude=('collator','last_modified_by','title','brief_description','narrative','subject_species')


class ConditionInlineForm(ModelForm):
    experiment=forms.ModelChoiceField(queryset=Experiment.objects.all(),widget=forms.HiddenInput,required=True)
    name=forms.CharField(max_length=100, required=True)
    description=forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=True)
    type=forms.ChoiceField(choices=Condition.CONDITION_TYPE_CHOICES)
    epoch_type=forms.CharField(max_length=50,widget=forms.HiddenInput,required=True)
    trial_type=forms.CharField(max_length=50,widget=forms.HiddenInput,required=True)
    object=forms.CharField(max_length=50,widget=forms.HiddenInput,required=True)

    class Meta:
        model=Condition
        exclude=()

ConditionFormSet = lambda *a, **kw: inlineformset_factory(Experiment,Condition,form=ConditionInlineForm, fk_name='experiment',
    extra=kw.pop('extra', 0), can_delete=True)(*a, **kw)


class GraspConditionInlineForm(ConditionInlineForm):
    object_distance=forms.DecimalField(required=True)
    grasp=forms.CharField(max_length=50)

    hand_visible = forms.BooleanField(required=False)
    object_visible = forms.BooleanField(required=False)

    demonstrator_species=forms.ModelChoiceField(queryset=Species.objects.all())
    demonstration_type=forms.ChoiceField(choices=GraspObservationCondition.DEMONSTRATION_CHOICES)
    viewing_angle=forms.DecimalField()
    whole_body_visible = forms.BooleanField(required=False)

    class Meta:
        model=GraspCondition
        exclude=()


class GraspObservationConditionForm(ModelForm):

     class Meta:
         model = GraspObservationCondition
         exclude=('experiment','type')


class GraspPerformanceConditionForm(ModelForm):

    class Meta:
        model = GraspPerformanceCondition
        exclude=('experiment','type')


GraspConditionFormSet = lambda *a, **kw: inlineformset_factory(Experiment,GraspCondition,form=GraspConditionInlineForm, fk_name='experiment',
    extra=kw.pop('extra', 0), can_delete=True)(*a, **kw)


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