from django.contrib.auth.models import User
from django import forms
from django.forms.models import ModelForm
from mirrordb.models import ExperimentExportRequest, Experiment

class ExperimentExportRequestForm(ModelForm):
    requesting_user=forms.ModelChoiceField(User.objects.all(),widget=forms.HiddenInput,required=False)
    name = forms.CharField(widget=forms.TextInput(attrs={'size':'20'}),required=True)
    rationale = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=True)
    experiment = forms.ModelChoiceField(Experiment.objects.all(),widget=forms.HiddenInput,required=False)

    class Meta:
        model = ExperimentExportRequest
        exclude=('activation_key','status')


class ExperimentExportRequestDenyForm(forms.Form):
    reason=forms.CharField(widget=forms.Textarea(attrs={'cols':'57', 'rows':'5'}), required=True)


class ExperimentExportRequestApproveForm(forms.Form):
    reason=forms.CharField(widget=forms.Textarea(attrs={'cols':'57', 'rows':'5'}), required=True)