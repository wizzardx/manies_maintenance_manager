"""
View functions for the jobs module in the Marnie's Maintenance Manager application.

This module contains view functions that handle requests for listing maintenance jobs
and creating new maintenance jobs. Each view function renders an HTML template that
corresponds to its specific functionality.
"""

from typing import Any
from typing import cast

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import AnonymousUser
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView

from marnies_maintenance_manager.users.models import User

from .models import Job


class JobListView(LoginRequiredMixin, UserPassesTestMixin, ListView):  # type: ignore[type-arg]
    """
    Display a list of all Maintenance Jobs.

    This view extends Django's ListView class to display a list of all maintenance jobs
    in the system. It uses the 'jobs/job_list.html' template.
    """

    model = Job
    template_name = "jobs/job_list.html"

    def test_func(self) -> bool:
        """Check if the user is an agent, or a superuser."""
        user = cast(User, self.request.user)
        return user.is_agent or user.is_superuser

    def get_queryset(self) -> QuerySet[Job]:
        """Return a queryset of all users."""
        user = self.request.user
        if isinstance(user, AnonymousUser):  # pragma: no cover
            # This should never happen, because our class inherits from
            # LoginRequiredMixin
            msg = "User is not logged in"
            raise TypeError(msg)
        return Job.objects.filter(agent=user)


class JobCreateView(LoginRequiredMixin, CreateView):  # type: ignore[type-arg]
    """
    Provide a form to create a new Maintenance Job.

    This view extends Django's CreateView class to create a form for users to input
    details for a new maintenance job. It uses the 'jobs/job_create.html' template.
    """

    model = Job
    fields = ["date", "address_details", "gps_link", "quote_request_details"]
    template_name = "jobs/job_create.html"
    success_url = reverse_lazy("jobs:job_list")

    def form_valid(self, form: Any) -> HttpResponse:
        """Set the agent field to the current user before saving the form."""
        # The "form" is dynamically generated by Django, so we can't type-check it.
        form.instance.agent = self.request.user
        return super().form_valid(form)
