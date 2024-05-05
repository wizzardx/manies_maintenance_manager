"""
Tests for HTML content validation in Manies Maintenance Manager application views.

This module checks the HTML content returned by various views in the Manies Maintenance
Manager application. It covers tests for the home page, maintenance jobs page, and the
create maintenance job page. Each test ensures that the respective page renders the
expected HTML structure, elements, and uses the appropriate template.

The Django test client is used for making requests, and BeautifulSoup for parsing the
returned HTML. This setup ensures not only a successful HTTP response but also verifies
the accuracy of the HTML content against expected patterns and structures.

To execute these tests, run the following command:
`docker compose -f local.yml run --rm django pytest \
    manies_maintenance_manager/jobs/tests/test_pages_return_correct_html.py`
"""

import re

import pytest
from bs4 import BeautifulSoup
from django.views.generic import TemplateView

HTTP_SUCCESS_STATUS_CODE = 200


@pytest.mark.django_db()
def test_home_page_returns_correct_html(client):
    """
    Verify that the home page renders correctly.

    This test checks if the home page returns HTML content with the specified title
    tag correctly formatted, includes necessary language attributes, uses the correct
    HTML structure, and utilizes the designated template.
    It also validates the view function linked to this page.
    """
    response = client.get("/")
    assert response.status_code == HTTP_SUCCESS_STATUS_CODE

    # Decode response content to check for specific HTML elements
    response_text = response.content.decode()
    assert re.search(
        r"<title>\s*Manies Maintenance Manager\s*</title>",
        response_text,
        re.IGNORECASE,
    ), (
        "Page title should contain 'Manies Maintenance Manager' with any "
        "amount of whitespace."
    )
    assert '<html lang="en">' in response_text
    assert "</html>" in response_text

    # Verify that the correct template was used
    assert "pages/home.html" in [t.name for t in response.templates]

    # Validate details about the view function used to handle the route
    assert response.resolver_match.func.__name__ == "view"
    assert response.resolver_match.url_name == "home"
    assert response.resolver_match.func.view_class == TemplateView


@pytest.mark.django_db()
def test_maintenance_jobs_page_returns_correct_html(client):
    """
    Verify the maintenance jobs page loads with the correct HTML.

    This test ensures the maintenance jobs page is loaded with the correct title, a
    header tag, and the appropriate HTML structure.
    It also verifies the use of the correct template and checks the associated view
    function for this route.
    """
    response = client.get("/jobs/")
    assert response.status_code == HTTP_SUCCESS_STATUS_CODE

    # Decode response content to check for specific HTML elements
    response_text = response.content.decode()
    assert re.search(
        r"<title>\s*Maintenance Jobs\s*</title>",
        response_text,
        re.IGNORECASE,
    ), "Page title should contain 'Maintenance Jobs' with any amount of whitespace."
    assert "<h1>Maintenance Jobs</h1>" in response_text
    assert '<html lang="en">' in response_text
    assert "</html>" in response_text

    # Verify that the correct template was used
    assert "pages/job_list.html" in [t.name for t in response.templates]

    # Validate details about the view function used to handle the route
    assert response.resolver_match.func.__name__ == "job_list"
    assert response.resolver_match.url_name == "job_list"


@pytest.mark.django_db()
def test_create_maintenance_job_page_returns_correct_html(client):
    """
    Ensure the create maintenance job page returns the expected HTML content.

    This test checks for the presence of the correct title and header in the HTML of
    the create maintenance job page, ensures the HTML structure is properly formed, and
    confirms that the designated template is used.
    It also verifies the correct view function is managing this route.
    """
    response = client.get("/jobs/create/")
    assert response.status_code == HTTP_SUCCESS_STATUS_CODE

    # Check the for <html> opening and closing tags:
    response_text = response.content.decode()
    assert '<html lang="en">' in response_text
    assert "</html>" in response_text

    # Parse HTML so that we can check for specific elements
    soup = BeautifulSoup(response_text, "html.parser")

    # Check the title tag
    title_tag = soup.find("title")
    assert title_tag, "Title tag should exist in the HTML"
    assert title_tag.get_text(strip=True) == "Create Maintenance Job"

    # Check a h1 tag
    h1_tag = soup.find("h1")
    assert h1_tag, "H1 tag should exist in the HTML"
    assert h1_tag.get_text(strip=True) == "Create Maintenance Job"

    # Verify that the correct template was usedd
    assert "pages/job_create.html" in [t.name for t in response.templates]

    # Validate details about the view function used to handle the route
    assert response.resolver_match.func.__name__ == "job_create"
    assert response.resolver_match.url_name == "job_create"
