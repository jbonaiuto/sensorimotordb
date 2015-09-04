from django.views.generic import DetailView
from mirrordb.models import Condition

class ConditionDetailView(DetailView):
    model = Condition
    template_name = 'mirrordb/condition_view.html'
    permission_required = 'view'
