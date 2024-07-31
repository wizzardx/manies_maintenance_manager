"""Tests for the forms in the "jobs" app."""

# pylint: disable=magic-value-comparison

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile

from marnies_maintenance_manager.jobs.forms import FinalPaymentPOPUpdateForm
from marnies_maintenance_manager.jobs.forms import JobCompleteForm
from marnies_maintenance_manager.jobs.forms import JobCompletionPhotoForm
from marnies_maintenance_manager.jobs.forms import JobCompletionPhotoFormSet
from marnies_maintenance_manager.jobs.forms import JobUpdateForm
from marnies_maintenance_manager.jobs.forms import QuoteUpdateForm
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.models import JobCompletionPhoto
from marnies_maintenance_manager.jobs.utils import safe_read
from marnies_maintenance_manager.users.models import User


class TestJobUpdateForm:
    """Tests for the JobUpdateForm form."""

    @staticmethod
    def test_model_class_is_job() -> None:
        """Test that the JobUpdateForm is for the Job model."""
        assert JobUpdateForm.Meta.model == Job

    @staticmethod
    def test_has_date_of_inspection_field() -> None:
        """Test that the JobUpdateForm has a date_of_inspection field."""
        assert "date_of_inspection" in JobUpdateForm.Meta.fields

    @staticmethod
    def test_has_quote_field() -> None:
        """Test that the JobUpdateForm has a quote field."""
        assert "quote" in JobUpdateForm.Meta.fields

    @staticmethod
    def test_date_of_inspection_field_is_required() -> None:
        """Test that the date_of_inspection field is required."""
        data = {"date_of_inspection": ""}
        form = JobUpdateForm(data=data)
        assert not form.is_valid()
        assert "date_of_inspection" in form.errors
        assert "This field is required." in form.errors["date_of_inspection"]

    @staticmethod
    def test_quote_field_is_required() -> None:
        """Test that the quote field is required."""
        data = {"quote": ""}
        form = JobUpdateForm(data=data)
        assert not form.is_valid()
        assert "quote" in form.errors
        assert "This field is required." in form.errors["quote"]


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


class TestJobCompleteForm:
    """Tests for the JobCompleteForm form."""

    @staticmethod
    def test_model_class_is_job() -> None:
        """Test that the JobCompleteForm is for the Job model."""
        assert JobCompleteForm.Meta.model == Job

    @staticmethod
    def test_has_job_date_field() -> None:
        """Test that the JobCompleteForm has a job_date field."""
        assert "job_date" in JobCompleteForm.Meta.fields

    @staticmethod
    def test_has_invoice_field() -> None:
        """Test that the JobCompleteForm has an invoice field."""
        assert "invoice" in JobCompleteForm.Meta.fields

    @staticmethod
    def test_has_comments_field() -> None:
        """Test that the JobCompleteForm has a comments field."""
        assert "comments" in JobCompleteForm.Meta.fields

    @staticmethod
    def test_job_date_field_is_setup_correctly() -> None:
        """Test that the job_date field is required."""
        data = {"job_date": ""}
        form = JobCompleteForm(data=data)
        assert not form.is_valid()
        assert "job_date" in form.errors
        assert "This field is required." in form.errors["job_date"]

        # Make sure that the Job Date field will render correctly as a date input
        widget = form.fields["job_date"].widget
        assert isinstance(widget, forms.DateInput)
        assert widget.input_type == "date"

    @staticmethod
    def test_invoice_field_is_required() -> None:
        """Test that the invoice field is required."""
        data = {"invoice": ""}
        form = JobCompleteForm(data=data)
        assert not form.is_valid()
        assert "invoice" in form.errors
        assert "This field is required." in form.errors["invoice"]

    @staticmethod
    def test_comments_field_is_not_required() -> None:
        """Test that the "comments" field is not required."""
        data = {"comments": ""}
        form = JobCompleteForm(data=data)
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
        """Test that the final_payment_pop  field is required."""
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
