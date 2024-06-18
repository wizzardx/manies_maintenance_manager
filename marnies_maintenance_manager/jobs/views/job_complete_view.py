"""View for completing a Maintenance Job."""

from django.views.generic import UpdateView

from marnies_maintenance_manager.jobs.forms import JobCompleteForm
from marnies_maintenance_manager.jobs.models import Job


class JobCompleteView(UpdateView):
    """Complete a Maintenance Job."""

    model = Job
    form_class = JobCompleteForm
    template_name = "jobs/job_complete.html"
