from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from registration.backends.default.views import RegistrationView
from sensorimotordb.forms import SensoriMotorDBRegistrationForm
from sensorimotordb.views import UpdateUserProfileView

urlpatterns = patterns('',
    url(r'^accounts/register/$', RegistrationView.as_view(form_class=SensoriMotorDBRegistrationForm), name='registration_register'),
    (r'^accounts/', include('registration.backends.default.urls')),
    (r'^accounts/profile/$', UpdateUserProfileView.as_view(), {}, 'update_user_profile'),
    (r'^sensorimotordb/', include('sensorimotordb.urls')),
)+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [url(r'^__debug__/', include(debug_toolbar.urls)),] + urlpatterns