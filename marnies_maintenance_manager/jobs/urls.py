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

from .views.accept_quote_view import accept_quote
from .views.agent_list_view import agent_list
from .views.download_quote_view import download_quote
from .views.job_create_view import JobCreateView
from .views.job_detail_view import JobDetailView
from .views.job_list_view import JobListView
from .views.job_update_view import JobUpdateView
from .views.refuse_quote_view import refuse_quote

app_name = "jobs"
urlpatterns = [
    path("", JobListView.as_view(), name="job_list"),
    path("create/", JobCreateView.as_view(), name="job_create"),
    path("<uuid:pk>/", JobDetailView.as_view(), name="job_detail"),
    path("<uuid:pk>/update/", JobUpdateView.as_view(), name="job_update"),
    path("<uuid:pk>/download-quote/", download_quote, name="download_quote"),
    path("<uuid:pk>/refuse-quote/", refuse_quote, name="refuse_quote"),
    path("<uuid:pk>/accept-quote/", accept_quote, name="accept_quote"),
    path("agents/", agent_list, name="agent_list"),
]
