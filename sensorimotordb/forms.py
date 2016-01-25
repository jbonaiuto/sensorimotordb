from django.contrib.auth.models import User
from django import forms
from django.forms.models import ModelForm
from registration.forms import RegistrationForm
from registration.users import UsernameField
from sensorimotordb.models import ExperimentExportRequest, Experiment

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