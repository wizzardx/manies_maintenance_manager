"""Forms for the "jobs" app."""

from django import forms

from marnies_maintenance_manager.jobs.models import Job


class JobUpdateForm(forms.ModelForm):  # type: ignore[type-arg]
    """Form for updating a job."""

    class Meta:
        """Metaclass for the JobUpdateForm."""

        model = Job
        fields = [
            "date_of_inspection",
            "quote",
        ]

    date_of_inspection = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    quote = forms.FileField()
