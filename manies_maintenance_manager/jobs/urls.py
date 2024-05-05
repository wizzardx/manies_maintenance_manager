"""
URL routing definitions for the jobs module in the Manies Maintenance Manager.

This module defines URL patterns for the 'jobs' application, mapping URLs to their
respective view functions for listing and creating maintenance jobs. It utilizes
Django's path function to establish routes.

The urlpatterns list includes:
- A route for the job list page, linked to the `job_list` view.
- A route for the create job page, linked to the `job_create` view.

This configuration maintains a clean separation of concerns between URLs and views,
adhering to Django's principles for URL dispatching.

Usage examples:
Access the job list with `/jobs/` and the creation page with `/jobs/create/`.
"""

from django.urls import path

from .views import job_create
from .views import job_list

app_name = "jobs"
urlpatterns = [
    path("", job_list, name="job_list"),
    path("create/", job_create, name="job_create"),
]
