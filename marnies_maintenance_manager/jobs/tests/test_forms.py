"""Tests for the forms in the "jobs" app."""

# pylint: disable=magic-value-comparison

from typing import cast

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.uploadedfile import UploadedFile
from django.utils.datastructures import MultiValueDict

from marnies_maintenance_manager.jobs.forms import FinalPaymentPOPUpdateForm
from marnies_maintenance_manager.jobs.forms import JobCompleteInspectionForm
from marnies_maintenance_manager.jobs.forms import JobCompleteOnsiteWorkForm
from marnies_maintenance_manager.jobs.forms import JobCompletionPhotoForm
from marnies_maintenance_manager.jobs.forms import JobCompletionPhotoFormSet
from marnies_maintenance_manager.jobs.forms import JobSubmitDocumentationForm
from marnies_maintenance_manager.jobs.forms import QuoteUpdateForm
from marnies_maintenance_manager.jobs.forms import QuoteUploadForm
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.models import JobCompletionPhoto
from marnies_maintenance_manager.jobs.utils import safe_read
from marnies_maintenance_manager.users.models import User


class TestJobCompleteInspectionForm:
    """Tests for the JobCompleteInspectionForm form."""

    @staticmethod
    def test_model_class_is_job() -> None:
        """Test that the JobCompleteInspectionForm is for the Job model."""
        assert JobCompleteInspectionForm.Meta.model == Job

    @staticmethod
    def test_has_date_of_inspection_field() -> None:
        """Test that the JobCompleteInspectionForm has a date_of_inspection field."""
        assert "date_of_inspection" in JobCompleteInspectionForm.Meta.fields

    @staticmethod
    def test_does_not_have_quote_field() -> None:
        """Test that the JobCompleteInspectionForm does not have a quote field."""
        assert "quote" not in JobCompleteInspectionForm.Meta.fields

    @staticmethod
    def test_date_of_inspection_field_is_required() -> None:
        """Test that the date_of_inspection field is required."""
        data = {"date_of_inspection": ""}
        form = JobCompleteInspectionForm(data=data)
        assert not form.is_valid()
        assert "date_of_inspection" in form.errors
        assert "This field is required." in form.errors["date_of_inspection"]


class TestQuoteUploadForm:
    """Tests for the QuoteUploadForm form."""

    @staticmethod
    def test_model_class_is_job() -> None:
        """Test that the QuoteUploadForm is for the Job model."""
        assert QuoteUploadForm.Meta.model == Job

    @staticmethod
    def test_has_quote_field() -> None:
        """Test that the QuoteUploadForm has a quote field."""
        assert "quote" in QuoteUploadForm.Meta.fields

    @staticmethod
    def test_quote_field_is_required() -> None:
        """Test that the quote field is required."""
        data = {"quote": ""}
        form = QuoteUploadForm(data=data)
        assert not form.is_valid()
        assert "quote" in form.errors
        assert "This field is required." in form.errors["quote"]

    @staticmethod
    def test_updates_the_job_object(
        test_pdf: SimpleUploadedFile,
        bob_job_with_initial_marnie_inspection: Job,
    ) -> None:
        """Test that the form updates the job object.

        Args:
            test_pdf (SimpleUploadedFile): A test PDF file.
            bob_job_with_initial_marnie_inspection (Job): A job instance.
        """
        # Check Job before saving.
        job = bob_job_with_initial_marnie_inspection
        assert not job.quote
        assert job.quote.name == ""

        file_data = cast(MultiValueDict[str, UploadedFile], {"quote": test_pdf})
        form = QuoteUploadForm(instance=job, files=file_data)
        assert form.is_valid(), form.errors
        with safe_read(test_pdf):
            form.save()

        # Check Job after saving:
        quote_name = job.quote.name  # eg:  'quotes/test_XH4UNrl.pdf'
        assert quote_name.startswith("quotes/test")
        assert quote_name.endswith(".pdf")

        with safe_read(test_pdf):
            test_pdf_data = test_pdf.read()

        assert job.quote.read() == test_pdf_data


class TestQuoteUpdateForm:
    """Tests for the QuoteUpdateForm form."""

    @staticmethod
    def test_model_class_is_job() -> None:
        """Test that the QuoteUpdateForm is for the Job model."""
        assert QuoteUpdateForm.Meta.model == Job

    @staticmethod
    def test_has_quote_field() -> None:
        """Test that the QuoteUpdateForm has a quote field."""
        assert "quote" in QuoteUpdateForm.Meta.fields

    @staticmethod
    def test_should_have_an_error_if_same_quote_is_submitted(
        bob_agent_user: User,
        test_pdf: SimpleUploadedFile,
    ) -> None:
        """Test that the form has an error if the same quote is submitted.

        Args:
            bob_agent_user (User): A user instance for Bob the agent.
            test_pdf (SimpleUploadedFile): A test PDF file.
        """
        with safe_read(test_pdf):
            job = Job.objects.create(
                agent=bob_agent_user,
                date="2022-01-01",
                quote=test_pdf,
                address_details="1234 Main St, Springfield, IL",
                gps_link="https://www.google.com/maps",
                quote_request_details="Replace the kitchen sink",
            )

        data = {"quote": test_pdf}
        form = QuoteUpdateForm(data=data, instance=job)
        assert not form.is_valid()
        assert "quote" in form.errors
        assert "You must provide a new quote" in form.errors["quote"]


class TestJobCompleteOnsiteWorkForm:
    """Tests for the JobCompleteOnsiteWorkForm class."""

    @staticmethod
    def test_model_class_is_job() -> None:
        """Test that the JobCompleteOnsiteWorkForm class is for the Job model."""
        assert JobCompleteOnsiteWorkForm.Meta.model == Job

    @staticmethod
    def test_has_job_onsite_work_completion_date_field() -> None:
        """Test that our class has a a job_onsite_work_completion_date field."""
        assert (
            "job_onsite_work_completion_date" in JobCompleteOnsiteWorkForm.Meta.fields
        )

    @staticmethod
    def test_job_onsite_work_completion_date_field_is_setup_correctly() -> None:
        """Test that the job_onsite_work_completion_date field is required."""
        data = {"job_onsite_work_completion_date": ""}
        form = JobCompleteOnsiteWorkForm(data=data)
        assert not form.is_valid()
        assert "job_onsite_work_completion_date" in form.errors
        assert (
            "This field is required." in form.errors["job_onsite_work_completion_date"]
        )

        # Make sure that the Job Date field will render correctly as a date input
        widget = form.fields["job_onsite_work_completion_date"].widget
        assert isinstance(widget, forms.DateInput)
        assert widget.input_type == "date"


class TestJobSubmitDocumentationForm:
    """Tests for the JobSubmitDocumentationForm class."""

    @staticmethod
    def test_model_class_is_job() -> None:
        """Test that the JobCompleteForm class is for the Job model."""
        assert JobSubmitDocumentationForm.Meta.model == Job

    @staticmethod
    def test_has_invoice_field() -> None:
        """Test that the JobCompleteForm class has an invoice field."""
        assert "invoice" in JobSubmitDocumentationForm.Meta.fields

    @staticmethod
    def test_has_comments_field() -> None:
        """Test that the JobSubmitDocumentationForm class has a "comments" field."""
        assert "comments" in JobSubmitDocumentationForm.Meta.fields

    @staticmethod
    def test_invoice_field_is_required() -> None:
        """Test that the invoice field is required."""
        data = {"invoice": ""}
        form = JobSubmitDocumentationForm(data=data)
        assert not form.is_valid()
        assert "invoice" in form.errors
        assert "This field is required." in form.errors["invoice"]

    @staticmethod
    def test_comments_field_is_not_required() -> None:
        """Test that the "comments" field is not required."""
        data = {"comments": ""}
        form = JobSubmitDocumentationForm(data=data)
        assert not form.is_valid()
        assert "comments" not in form.errors


class TestFinalPaymentPOPUpdateForm:
    """Tests for the FinalPaymentPOPUpdateForm form."""

    @staticmethod
    def test_model_class_is_job() -> None:
        """Test that the FinalPaymentPOPUpdateForm is for the Job model."""
        assert FinalPaymentPOPUpdateForm.Meta.model == Job

    @staticmethod
    def test_has_final_payment_proof_of_payment_field() -> None:
        """Test that the FinalPaymentPOPUpdateForm has a final_payment_pop field."""
        assert "final_payment_pop" in FinalPaymentPOPUpdateForm.Meta.fields

    @staticmethod
    def test_final_payment_pop_field_is_required() -> None:
        """Test that the final_payment_pop field is required."""
        data = {"final_payment_pop": ""}
        form = FinalPaymentPOPUpdateForm(data=data)
        assert not form.is_valid()
        assert "final_payment_pop" in form.errors
        assert "This field is required." in form.errors["final_payment_pop"]


class TestJobCompletionPhotoForm:
    """Tests for the JobCompletionPhotoForm form."""

    @staticmethod
    def test_model_class_is_job_completion_photo() -> None:
        """Test that the JobCompletionPhotoForm is for the JobCompletionPhoto model."""
        assert JobCompletionPhotoForm.Meta.model == JobCompletionPhoto

    @staticmethod
    def test_has_photo_field() -> None:
        """Test that the JobCompletionPhotoForm has a photo field."""
        assert "photo" in JobCompletionPhotoForm.Meta.fields

    @staticmethod
    def test_photo_field_is_an_image_field() -> None:
        """Test that the photo field is an image field."""
        form = JobCompletionPhotoForm()
        assert isinstance(form.fields["photo"], forms.ImageField)

    @staticmethod
    def test_photo_field_is_required() -> None:
        """Test that the photo field is required."""
        data = {"photo": ""}
        form = JobCompletionPhotoForm(data=data)
        assert not form.is_valid()
        assert "photo" in form.errors
        assert "This field is required." in form.errors["photo"]


class TestJobCompletionPhotoFormSet:
    """Tests for the JobCompletionPhotoFormSet formset."""

    @staticmethod
    def test_model_class_is_job_completion_photo() -> None:
        """Test that JobCompletionPhotoFormSet is for the JobCompletionPhoto model."""
        assert JobCompletionPhotoFormSet.model == JobCompletionPhoto

    @staticmethod
    def test_form_class_is_job_completion_photo_form() -> None:
        """Test that the form class is the JobCompletionPhotoForm."""
        assert "'django.forms.widgets.JobCompletionPhotoForm'" in str(
            JobCompletionPhotoFormSet.form,
        )

    @staticmethod
    def test_extra_is_zero() -> None:
        """Test that the extra attribute is set to zero."""
        assert JobCompletionPhotoFormSet.extra == 0
