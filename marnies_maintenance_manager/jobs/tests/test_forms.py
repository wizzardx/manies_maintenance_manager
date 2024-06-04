"""Tests for the forms in the "jobs" app."""

# pylint: disable=magic-value-comparison

from marnies_maintenance_manager.jobs.forms import JobUpdateForm
from marnies_maintenance_manager.jobs.models import Job


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
    def test_date_of_inspection_field_is_required_date_input() -> None:
        """Test that the date_of_inspection field is required."""
        data = {"date_of_inspection": ""}
        form = JobUpdateForm(data=data)
        assert not form.is_valid()
        assert "date_of_inspection" in form.errors
        assert "This field is required." in form.errors["date_of_inspection"]

    @staticmethod
    def test_quote_field_is_required_file_field() -> None:
        """Test that the quote field is required."""
        data = {"quote": ""}
        form = JobUpdateForm(data=data)
        assert not form.is_valid()
        assert "quote" in form.errors
        assert "This field is required." in form.errors["quote"]
