"""Forms for the "jobs" app."""

from typing import TYPE_CHECKING

from django import forms
from django.core.files.base import File
from typeguard import check_type
from typeguard import typechecked

from marnies_maintenance_manager.jobs.models import Job

if TYPE_CHECKING:  # pragma: no cover
    # These are only for type checking:
    TypedModelForm = forms.ModelForm[Job]
    TypedFile = File[bytes]
else:
    TypedModelForm = forms.ModelForm
    TypedFile = File


class JobUpdateForm(TypedModelForm):
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


class QuoteUpdateForm(TypedModelForm):
    """Form for updating a quote."""

    class Meta:
        """Metaclass for the QuoteUpdateForm."""

        model = Job
        fields = [
            "quote",
        ]

        quote = forms.FileField()

    @typechecked
    def clean_quote(self) -> TypedFile:
        """Ensure that the quote is different from the current quote.

        Returns:
            TypedFile: The new quote.

        Raises:
            ValidationError: If the quote is the same as the current quote.
        """
        quote = check_type(self.cleaned_data.get("quote"), File)
        instance_quote = check_type(self.instance.quote, File)

        # Seek to 0 and then dread data from the two different files we want to
        # compare:
        read_data = []
        for file in (quote, instance_quote):
            file.seek(0)
            read_data.append(file.read())

        if read_data[0] == read_data[1]:
            msg = "You must provide a new quote"
            raise forms.ValidationError(msg)
        return quote


class DepositPOPUpdateForm(TypedModelForm):
    """Provide a form for the Proof of Payment update view."""

    class Meta:
        """Metaclass for the DepositPOPUpdateForm."""

        model = Job
        fields = [
            "deposit_proof_of_payment",
        ]

    deposit_proof_of_payment = forms.FileField()
