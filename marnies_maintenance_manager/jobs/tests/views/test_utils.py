"""Tests for the utility functions in the views module of the "jobs" app."""

# pylint: disable=too-few-public-methods

import re

import pytest
import pytest_mock

from marnies_maintenance_manager.jobs.tests.views import utils
from marnies_maintenance_manager.jobs.views import utils as views_utils
from marnies_maintenance_manager.users.models import User


class TestAssertNoFormErrors:
    """Tests for the assert_no_form_errors function."""

    @staticmethod
    def test_form_errors_cause_assertion_error(mocker: pytest_mock.MockFixture) -> None:
        """Test that the function raises an AssertionError if the form has errors.

        Args:
            mocker (pytest_mock.MockFixture): A pytest-mock fixture.
        """

        class MockForm:
            """A mock form class with an "errors" attribute."""

            errors = {"field": ["This field is required."]}

        # Mock the isinstance function in the utils module, so that as a side effect
        # the "isinstance" check in the function will pass
        mocker.patch("marnies_maintenance_manager.jobs.tests.views.utils.isinstance")

        # Build a fake response to pass to the function
        mock_response = mocker.Mock()
        mock_response.context_data = {"form": MockForm}

        with pytest.raises(
            AssertionError,
            match=re.escape(
                "Form errors found in the response context: "
                "{'field': ['This field is required.']}",
            ),
        ):
            utils.assert_no_form_errors(mock_response)

    @staticmethod
    def test_no_form_errors_does_not_raise_error(
        mocker: pytest_mock.MockFixture,
    ) -> None:
        """Test that the function does not raise an error if the form has no errors.

        Args:
            mocker (pytest_mock.MockFixture): A pytest-mock fixture.
        """

        class MockForm:
            """A mock form class with an empty errors attribute."""

            errors: dict[str, list[str]] = {}

        # Mock the isinstance function in the utils module, so that as a side effect
        # the "isinstance" check in the function will pass
        mocker.patch("marnies_maintenance_manager.jobs.tests.views.utils.isinstance")

        # Build a fake response to pass to the function
        mock_response = mocker.Mock()
        mock_response.context_data = {"form": MockForm}

        utils.assert_no_form_errors(mock_response)  # Should not raise

    @staticmethod
    def test_response_is_not_a_template(mocker: pytest_mock.MockFixture) -> None:
        """Test that an AssertionError is raised if the response isn't a template.

        Args:
            mocker (pytest_mock.MockFixture): A pytest-mock fixture.
        """

        class MockForm:
            """A mock form class with an empty errors attribute."""

            errors: dict[str, list[str]] = {}

        # Build a fake response to pass to the function
        mock_response = mocker.Mock()
        mock_response.context_data = {"form": MockForm}

        utils.assert_no_form_errors(mock_response)  # Should not raise


@pytest.mark.django_db()
def test_prepare_and_send_email_with_unknown_attachment_type(
    mocker: pytest_mock.MockFixture,
    marnie_user: User,  # pylint: disable=unused-argument
) -> None:
    """Test that the function raises a ValueError if the attachment type is unknown.

    Args:
        mocker (pytest_mock.MockFixture): A pytest-mock fixture.
        marnie_user (User): A User instance
    """
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Invalid value for 'what_to_attach': 'unknown_attachment_type'",
        ),
    ):
        views_utils.prepare_and_send_email(
            email_subject="subject",
            email_body="body",
            job=mocker.Mock(),
            request=mocker.Mock(),
            what_to_attach="unknown_attachment_type",  # type: ignore[arg-type]
        )
