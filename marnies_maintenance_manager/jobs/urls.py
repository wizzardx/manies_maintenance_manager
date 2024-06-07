"""URL routing definitions for the jobs module in the Marnie's Maintenance Manager.

This module defines URL patterns for the 'jobs' application, mapping URLs to their
respective view functions for listing and creating maintenance jobs. It uses
Django's path function to establish routes.

The urlpatterns list includes:
- A route for the job list page, linked to the `job_list` view.
- A route for the "create job" page, linked to the `job_create` view.

This configuration maintains a clean separation of concerns between URLs and views,
adhering to Django's principles for URL dispatching.

Usage examples:
Access the job list with `/jobs/` and the creation page with `/jobs/create/`.
"""

from django.urls import path

from .views.agent_list_view import agent_list
from .views.deposit_pop_update_view import DepositPOPUpdateView
from .views.job_create_view import JobCreateView
from .views.job_detail_view import JobDetailView
from .views.job_list_view import JobListView
from .views.job_update_view import JobUpdateView
from .views.quote_accept_view import quote_accept
from .views.quote_download_view import quote_download
from .views.quote_reject_view import quote_reject
from .views.quote_update_view import QuoteUpdateView

app_name = "jobs"
urlpatterns = [
    path("", JobListView.as_view(), name="job_list"),
    path("agents/", agent_list, name="agent_list"),
    path("create/", JobCreateView.as_view(), name="job_create"),
    path("<uuid:pk>/", JobDetailView.as_view(), name="job_detail"),
    path("<uuid:pk>/update/", JobUpdateView.as_view(), name="job_update"),
    path("<uuid:pk>/quote/accept/", quote_accept, name="quote_accept"),
    path("<uuid:pk>/quote/download/", quote_download, name="quote_download"),
    path("<uuid:pk>/quote/reject/", quote_reject, name="quote_reject"),
    path("<uuid:pk>/quote/update/", QuoteUpdateView.as_view(), name="quote_update"),
    path(
        "<uuid:pk>/deposit_pop/update/",
        DepositPOPUpdateView.as_view(),
        name="deposit_pop_update",
    ),
]
