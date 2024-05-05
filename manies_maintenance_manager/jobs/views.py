"""
View functions for the jobs module in the Manies Maintenance Manager application.

This module contains view functions that handle requests for listing maintenance jobs
and creating new maintenance jobs. Each view function renders an HTML template that
corresponds to its specific functionality.

Functions:
- job_list: Renders the list of maintenance jobs.
- job_create: Provides the form for creating a new maintenance job.
"""

from django.shortcuts import render


def job_list(request):
    """
    Render the list of maintenance jobs.

    This view returns the job list page, which displays all current maintenance jobs
    registered in the system. It uses the 'pages/job_list.html' template.
    """
    return render(request, "pages/job_list.html")


def job_create(request):
    """
    Provide a form to create a new maintenance job.

    This view returns the job creation page, where users can enter details for a new
    maintenance job. It uses the 'pages/job_create.html' template to render the form.
    """
    return render(request, "pages/job_create.html")
