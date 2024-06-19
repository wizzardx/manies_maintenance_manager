"""View for completing a Maintenance Job."""

from typing import TYPE_CHECKING

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import UpdateView
from typeguard import check_type

from marnies_maintenance_manager.jobs.forms import JobCompleteForm
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.views.mixins import JobSuccessUrlMixin
from marnies_maintenance_manager.users.models import User

if TYPE_CHECKING:  # pylint: disable=consider-ternary-expression
    TypedUpdateView = UpdateView[  # pragma: no cover
        Job,
        JobCompleteForm,
    ]
else:
    TypedUpdateView = UpdateView


class JobCompleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    JobSuccessUrlMixin,
    TypedUpdateView,
):
    """Complete a Maintenance Job."""

    model = Job
    form_class = JobCompleteForm  # fields = ["job_date"]
    template_name = "jobs/job_complete.html"

    def test_func(self) -> bool:
        """Check if the user can access this view.

        Returns:
            bool: True if the user can access this view, False otherwise.
        """
        # Only Marnie and Admin users can reach this view, and only if the job has
        # not yet been completed by Marnie.
        user = check_type(self.request.user, User)

        job = self.get_object()
        return (job.status == Job.Status.DEPOSIT_POP_UPLOADED.value) and (
            user.is_superuser or user.is_marnie
        )
