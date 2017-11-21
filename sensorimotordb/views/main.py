import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic import TemplateView, UpdateView
from tastypie.models import ApiKey
from sensorimotordb.forms import UserProfileForm

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


class SearchView(LoginRequiredMixin, TemplateView):
    template_name = 'sensorimotordb/search.html'


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