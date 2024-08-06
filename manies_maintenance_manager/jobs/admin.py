"""Register models for the "jobs" application in the Django admin."""

from typing import TYPE_CHECKING

from django.contrib import admin

from .models import Job
from .models import JobCompletionPhoto

if TYPE_CHECKING:  # pragma: no cover
    TypedTabularInline = admin.TabularInline[JobCompletionPhoto, Job]
    TypedModelAdmin = admin.ModelAdmin[Job]
else:
    TypedTabularInline = admin.TabularInline
    TypedModelAdmin = admin.ModelAdmin


class JobCompletionPhotoInline(TypedTabularInline):
    """Inline for JobCompletionPhoto model."""

    model = JobCompletionPhoto
    extra = 1


@admin.register(Job)
class JobAdmin(TypedModelAdmin):
    """Admin for "Job" model."""

    inlines = [JobCompletionPhotoInline]
    list_display = ["agent", "number", "date", "status"]


@admin.register(JobCompletionPhoto)
class JobCompletionPhotoAdmin(TypedModelAdmin):
    """Admin for JobCompletionPhoto model."""

    list_display = ["job", "created"]
