"""Tests for HTML content validation in Marnie's Maintenance Manager application views.

This module checks the HTML content returned by various views in the Marnie's
Maintenance Manager application. It covers tests for the home page, maintenance jobs
page, and the "create maintenance job" page. Each test ensures that the respective page
renders the expected HTML structure, elements, and uses the appropriate template.

The Django test client is used for making requests, and BeautifulSoup for parsing the
returned HTML. This setup ensures not only a successful HTTP response but also verifies
the accuracy of the HTML content against expected patterns and structures.

To execute these tests, run the following command:
`docker compose -f docker-compose.local.yml run --rm django pytest \
    marnies_maintenance_manager/jobs/tests/utils.py`
"""

# pylint: disable=unused-argument

from bs4 import BeautifulSoup
from django.contrib.messages.storage.base import Message
from django.core.mail import EmailMessage
from django.http.response import HttpResponse
from django.test.client import Client
from django.views.generic.base import View as BaseView
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs.models import Job

HTTP_SUCCESS_STATUS_CODE = 200


# pylint: disable=too-many-arguments, no-self-use, magic-value-comparison
def check_basic_page_html_structure(  # noqa: PLR0913
    client: Client,
    url: str,
    expected_title: str,
    expected_template_name: str,
    expected_h1_text: str | None,
    expected_func_name: str,
    expected_url_name: str,
    expected_view_class: type[BaseView] | None,
) -> HttpResponse:
    """Check the basic HTML structure of a page.

    Within the Maintenance Manager app.

    Args:
        client (Client): The Django test client.
        url (str): The URL to check.
        expected_title (str): The expected title of the HTML page.
        expected_template_name (str): The expected template name to render the page.
        expected_h1_text (str | None): The expected text of the h1 tag in the HTML.
        expected_func_name (str): The name of the view function handling the route.
        expected_url_name (str): The name of the URL pattern used to access the route.
        expected_view_class (type[BaseView] | None): The view class to handle the route.

    Returns:
        HttpResponse: The response object from the client.
    """
    response = client.get(url)
    assert response.status_code == HTTP_SUCCESS_STATUS_CODE

    # Parse HTML so that we can check for specific elements
    response_text = response.content.decode()
    soup = BeautifulSoup(response_text, "html.parser")

    # Check the title tag
    title_tag = soup.find("title")
    assert title_tag, "Title tag should exist in the HTML"
    assert title_tag.get_text(strip=True) == expected_title

    # Check a h1 tag
    if expected_h1_text is not None:
        h1_tag = soup.find("h1")
        assert h1_tag, "H1 tag should exist in the HTML"
        assert h1_tag.get_text(strip=True) == expected_h1_text

    # Check additional expected HTML strings:
    assert '<html lang="en">' in response_text
    assert "</html>" in response_text

    # Verify that the correct template was used
    assert expected_template_name in [
        t.name for t in response.templates
    ], f"Expected template {expected_template_name} not used"

    # Validate details about the view function used to handle the route
    assert (
        response.resolver_match.func.__name__ == expected_func_name
    ), f"Found {response.resolver_match.func.__name__} instead of {expected_func_name}"
    assert (
        response.resolver_match.url_name == expected_url_name
    ), f"Found {response.resolver_match.url_name} instead of {expected_url_name}"
    if expected_view_class is not None:
        func = response.resolver_match.func
        view_class = func.view_class  # type: ignore[attr-defined]
        assert (
            view_class == expected_view_class
        ), f"Found {view_class} instead of {expected_view_class}"

    return check_type(response, HttpResponse)


def assert_email_contains_job_details(
    email: EmailMessage,
) -> tuple[str, tuple[str, bytes, str]]:
    """Assert that the email contains the job details.

    Args:
        email (EmailMessage): The email message object.

    Returns:
        tuple[str, tuple[str, bytes, str]]: The attachment name and the attachment.
    """
    job = Job.objects.get()
    # Check that there's a link to the job detail view in the email body:
    job_id = str(job.id)
    assert (
        f"Details of the job can be found at: http://testserver/jobs/{job_id}/"
        in email.body
    )
    assert "Details of your original request:" in email.body
    # A separator line:
    assert "-----" in email.body
    # The original mail subject line, as a line in the body:
    assert "Subject: New maintenance request by bob" in email.body
    # And all the original body lines, too, as per our previous test where the
    # agent user had just created a new job:
    assert "bob has made a new maintenance request." in email.body
    assert "Number: 1" in email.body
    assert "Date: 2022-01-01" in email.body
    assert "Address Details:\n\n1234 Main St, Springfield, IL" in email.body
    assert "GPS Link:\n\nhttps://www.google.com/maps" in email.body
    assert "Quote Request Details:\n\nReplace the kitchen sink" in email.body
    assert (
        "PS: This mail is sent from an unmonitored email address. "
        "Please do not reply to this email." in email.body
    )
    # Check the mail attachment
    assert len(email.attachments) == 1
    attachment = email.attachments[0]
    # Attachment name can be something like one of these:
    # - quotes/test_r8TJrLv.pdf
    # - quotes/test.pdf
    attach_name = attachment[0]
    return attach_name, attachment


def assert_standard_email_content(email: EmailMessage, job: Job) -> None:
    """Assert the standard email content.

    Args:
        email (EmailMessage): The email message object.
        job (Job): The job object.
    """
    assert (
        f"Details of the job can be found at: http://testserver/jobs/{job.id}/"
        in email.body
    )

    assert "Details of the original request:" in email.body

    # A separator line:
    assert "-----" in email.body

    # Subject and body of mail that we sent a bit previously:

    assert "Subject: Quote for your maintenance request" in email.body

    assert (
        "Marnie performed the inspection on 2001-02-05 and has quoted you."
        in email.body
    )

    # The original mail subject line, as a line in the body:
    assert "Subject: New maintenance request by bob" in email.body

    # And all the original body lines, too, as per our previous test where the
    # agent user had just created a new job:

    assert "bob has made a new maintenance request." in email.body
    assert "Date: 2022-01-01" in email.body
    assert "Number: 1" in email.body
    assert "Address Details:\n\n1234 Main St, Springfield, IL" in email.body
    assert "GPS Link:\n\nhttps://www.google.com/maps" in email.body
    assert "Quote Request Details:\n\nReplace the kitchen sink" in email.body
    assert (
        "PS: This mail is sent from an unmonitored email address. "
        "Please do not reply to this email." in email.body
    )


def assert_standard_quote_post_response(
    bob_agent_user_client: Client,
    bob_job_with_initial_marnie_inspection: Job,
    verb: str,
) -> list[Message]:
    """Assert the response after accepting or rejecting a quote.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob the agent user.
        bob_job_with_initial_marnie_inspection (Job): The job with an initial Marnie
            inspection.
        verb (str): The verb to use in the URL path.

    Returns:
        list[Message]: The messages returned by the response context.
    """
    assert verb in {"accept", "reject"}

    response = bob_agent_user_client.post(
        f"/jobs/{bob_job_with_initial_marnie_inspection.id}/quote/{verb}/",
        follow=True,
    )
    # Check the response code:
    assert response.status_code == status.HTTP_200_OK
    # Check the redirect chain:
    assert response.redirect_chain == [
        (f"/jobs/{bob_job_with_initial_marnie_inspection.id}/", 302),
    ]
    # Check the message:
    messages = list(response.context["messages"])
    assert len(messages) == 1
    return messages
