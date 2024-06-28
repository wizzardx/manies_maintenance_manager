"""Tests for the validators module."""

# pylint: disable=too-few-public-methods

import pytest
import pytest_mock
from django.core.exceptions import ValidationError

from marnies_maintenance_manager.jobs.validators import validate_pdf_contents


class TestValidatePDFContents:
    """Tests for the validate_pdf_contents function."""

    @staticmethod
    def tests_fails_if_tell_is_not_zero(mocker: pytest_mock.MockFixture) -> None:
        """Test that a ValidationError is raised if the file has already been read.

        Args:
            mocker (pytest_mock.MockFixture): A pytest-mock fixture.
        """
        file = mocker.Mock()
        file.tell.return_value = 1

        with pytest.raises(ValidationError, match="The file has already been read"):
            validate_pdf_contents(file)

    @staticmethod
    def test_should_fail_if_file_too_large(mocker: pytest_mock.MockFixture) -> None:
        """Test that a ValidationError is raised if the file size is too large.

        Args:
            mocker (pytest_mock.MockFixture): A pytest-mock fixture.
        """
        file = mocker.Mock()
        file.tell.return_value = 0
        file.size = 10 * 1024 * 1024
        file.name = "test.pdf"
        file.read.return_value = b"%PDF-1.5"

        with pytest.raises(
            ValidationError,
            match="File size should not exceed 5.0 MB. Your file, test.pdf, "
            "is 10.0 MB.",
        ):
            validate_pdf_contents(file)

    @staticmethod
    def test_reported_size_has_one_decimal_place(
        mocker: pytest_mock.MockFixture,
    ) -> None:
        """Test that the reported file size has one decimal place.

        Args:
            mocker (pytest_mock.MockFixture): A pytest-mock fixture.
        """
        file = mocker.Mock()
        file.tell.return_value = 0
        file.size = 100 * 1024 * 1024 / 3 * 2  # 66.7 MB
        file.name = "large_file.pdf"
        file.read.return_value = b"%PDF-1.5"
        max_size = int(1024 * 1024 / 3)  # 0.3 MB

        with pytest.raises(
            ValidationError,
            match="File size should not exceed 0.3 MB. Your file, large_file.pdf, "
            "is 66.7 MB.",
        ):
            validate_pdf_contents(file, max_size=max_size)
