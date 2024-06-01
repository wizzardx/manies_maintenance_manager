"""Register models for the jobs application in the Django admin."""

from django.contrib import admin

from marnies_maintenance_manager.jobs.models import Job

admin.site.register(Job)
