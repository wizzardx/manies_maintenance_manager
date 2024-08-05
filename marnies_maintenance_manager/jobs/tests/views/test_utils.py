"""Tests for the utility functions in the views module of the "jobs" app."""

# pylint: disable=too-few-public-methods

import re

import pytest
import pytest_mock
from django.core.mail import EmailMessage

from marnies_maintenance_manager.jobs.models import Job
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


@pytest.mark.django_db()
def test_prepare_and_send_email_quote(mocker: pytest_mock.MockFixture) -> None:
    """Test the 'QUOTE' branch of the prepare_and_send_email function.

    Args:
        mocker (pytest_mock.MockFixture): A pytest-mock fixture.
    """
    job = mocker.Mock(spec=Job)
    job.quote = mocker.Mock()
    job.quote.path = "/path/to/quote.pdf"
    job.agent.email = "agent@example.com"
    job.agent.username = "agent_username"

    mocker.patch.object(
        views_utils,
        "generate_email_body",
        return_value="Generated body",
    )
    mocker.patch.object(
        views_utils,
        "get_marnie_email",
        return_value="marnie@example.com",
    )
    mocker.patch.object(views_utils, "safe_read")
    mocker.patch("django.core.mail.EmailMessage.send")

    views_utils.prepare_and_send_email(
        email_subject="subject",
        email_body="body",
        job=job,
        request=mocker.Mock(),
        what_to_attach=views_utils.AttachmentType.QUOTE,
    )

    job.quote.read.assert_called_once()
    EmailMessage.send.assert_called_once()  # type: ignore[attr-defined]  # pylint: disable=no-member
    views_utils.generate_email_body.assert_called_once()  # type: ignore[attr-defined]  # pylint: disable=no-member
    views_utils.get_marnie_email.assert_called_once()  # type: ignore[attr-defined]  # pylint: disable=no-member
    views_utils.safe_read.assert_called_once()  # type: ignore[attr-defined]


@pytest.mark.django_db()
def test_prepare_and_send_email_none(mocker: pytest_mock.MockFixture) -> None:
    """Test the 'NONE' branch of the prepare_and_send_email function.

    Args:
        mocker (pytest_mock.MockFixture): A pytest-mock fixture.
    """
    job = mocker.Mock(spec=Job)
    job.agent.email = "agent@example.com"
    job.agent.username = "agent_username"

    mocker.patch.object(
        views_utils,
        "generate_email_body",
        return_value="Generated body",
    )
    mocker.patch.object(
        views_utils,
        "get_marnie_email",
        return_value="marnie@example.com",
    )
    mocker.patch("django.core.mail.EmailMessage.send")

    views_utils.prepare_and_send_email(
        email_subject="subject",
        email_body="body",
        job=job,
        request=mocker.Mock(),
        what_to_attach=views_utils.AttachmentType.NONE,
    )

    EmailMessage.send.assert_called_once()  # type: ignore[attr-defined]  # pylint: disable=no-member
    views_utils.generate_email_body.assert_called_once()  # type: ignore[attr-defined]  # pylint: disable=no-member
    views_utils.get_marnie_email.assert_called_once()  # type: ignore[attr-defined]  # pylint: disable=no-member


@pytest.mark.django_db()
def test_prepare_and_send_email_invoice_and_photos(
    mocker: pytest_mock.MockFixture,
) -> None:
    """Test the 'INVOICE_AND_PHOTOS' branch of the prepare_and_send_email function.

    Args:
        mocker (pytest_mock.MockFixture): A pytest-mock fixture.
    """
    job = mocker.Mock(spec=Job)
    job.invoice = mocker.Mock()
    job.invoice.path = "/path/to/invoice.pdf"
    job.job_completion_photos.all.return_value = [
        mocker.Mock(photo=mocker.Mock(path=f"/path/to/photo{i}.jpg")) for i in range(3)
    ]
    job.agent.email = "agent@example.com"
    job.agent.username = "agent_username"

    mocker.patch.object(
        views_utils,
        "generate_email_body",
        return_value="Generated body",
    )
    mocker.patch.object(
        views_utils,
        "get_marnie_email",
        return_value="marnie@example.com",
    )
    mocker.patch.object(views_utils, "safe_read")
    mocker.patch("django.core.mail.EmailMessage.send")

    views_utils.prepare_and_send_email(
        email_subject="subject",
        email_body="body",
        job=job,
        request=mocker.Mock(),
        what_to_attach=views_utils.AttachmentType.INVOICE_AND_PHOTOS,
    )

    job.invoice.read.assert_called_once()
    for photo in job.job_completion_photos.all():
        photo.photo.read.assert_called_once()
    EmailMessage.send.assert_called_once()  # type: ignore[attr-defined]  # pylint: disable=no-member
    views_utils.generate_email_body.assert_called_once()  # type: ignore[attr-defined]  # pylint: disable=no-member
    views_utils.get_marnie_email.assert_called_once()  # type: ignore[attr-defined]  # pylint: disable=no-member
    expected_num_calls = 4
    assert views_utils.safe_read.call_count == expected_num_calls  # type: ignore[attr-defined]


def test_get_content_type_for_pdf_file(mocker: pytest_mock.MockFixture) -> None:
    """Test that the function returns the correct content type for a PDF file.

    Args:
        mocker (pytest_mock.MockFixture): A pytest-mock fixture
    """
    attachment = mocker.Mock()
    attachment.path = "/path/to/file.pdf"
    pdf_mimetype = "application/pdf"
    assert views_utils.get_content_type(attachment) == pdf_mimetype


def test_get_content_type_for_jpg_file(mocker: pytest_mock.MockFixture) -> None:
    """Test that the function returns the correct content type for a JPEG file.

    Args:
        mocker (pytest_mock.MockFixture): A pytest-mock fixture
    """
    attachment = mocker.Mock()
    attachment.path = "/path/to/file.jpg"
    jpeg_mimetype = "image/jpeg"
    assert views_utils.get_content_type(attachment) == jpeg_mimetype
