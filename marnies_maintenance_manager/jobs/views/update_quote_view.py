"""View for updating a quote for a Maintenance Job."""

from typing import TYPE_CHECKING

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import UpdateView
from typeguard import check_type

from marnies_maintenance_manager.jobs.forms import QuoteUpdateForm
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.users.models import User

if TYPE_CHECKING:  # pylint: disable=consider-ternary-expression
    TypedUpdateView = UpdateView[  # pragma: no cover
        Job,
        QuoteUpdateForm,
    ]
else:
    TypedUpdateView = UpdateView


class QuoteUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    TypedUpdateView,
):
    """Update a quote for a Maintenance Job."""

    model: type[Job] = Job
    form_class: type[QuoteUpdateForm] = QuoteUpdateForm
    template_name: str = "jobs/update_quote.html"

    def test_func(self) -> bool:
        """Check if the user can access this view.

        Returns:
            bool: True if the user can access this view, False otherwise.

        """
        # Only Marnie and Admin can access this view:
        user = check_type(self.request.user, User)
        return check_type(user.is_marnie or user.is_superuser, bool)
