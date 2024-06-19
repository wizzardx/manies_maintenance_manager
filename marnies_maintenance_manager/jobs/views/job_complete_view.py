"""View for completing a Maintenance Job."""

from typing import TYPE_CHECKING

from django.views.generic import UpdateView

from marnies_maintenance_manager.jobs.forms import JobCompleteForm
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.views.mixins import JobSuccessUrlMixin

if TYPE_CHECKING:  # pylint: disable=consider-ternary-expression
    TypedUpdateView = UpdateView[  # pragma: no cover
        Job,
        JobCompleteForm,
    ]
else:
    TypedUpdateView = UpdateView


class JobCompleteView(JobSuccessUrlMixin, TypedUpdateView):
    """Complete a Maintenance Job."""

    model = Job
    form_class = JobCompleteForm
    template_name = "jobs/job_complete.html"
