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
