"""
Tests for HTML content validation in Marnie's Maintenance Manager application views.

This module checks the HTML content returned by various views in the Marnie's Maintenance
Manager application. It covers tests for the home page, maintenance jobs page, and the
create maintenance job page. Each test ensures that the respective page renders the
expected HTML structure, elements, and uses the appropriate template.

The Django test client is used for making requests, and BeautifulSoup for parsing the
returned HTML. This setup ensures not only a successful HTTP response but also verifies
the accuracy of the HTML content against expected patterns and structures.

To execute these tests, run the following command:
`docker compose -f local.yml run --rm django pytest \
    marnies_maintenance_manager/jobs/tests/test_pages_return_correct_html.py`
"""

import pytest
from bs4 import BeautifulSoup
from django.test.client import Client
from django.views.generic import TemplateView
from django.views.generic.base import View as BaseView

from marnies_maintenance_manager.jobs.views import JobCreateView
from marnies_maintenance_manager.jobs.views import JobListView

HTTP_SUCCESS_STATUS_CODE = 200


def _run_shared_logic(  # noqa: PLR0913
    client: Client,
    url: str,
    expected_title: str,
    expected_template_name: str,
    expected_h1_text: str | None,
    expected_func_name: str,
    expected_url_name: str,
    expected_view_class: type[BaseView],  # TODO: Test this line more
) -> None:
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
    assert expected_template_name in [t.name for t in response.templates]

    # Validate details about the view function used to handle the route
    assert response.resolver_match.func.__name__ == expected_func_name
    assert response.resolver_match.url_name == expected_url_name
    assert (
        response.resolver_match.func.view_class  # type: ignore[attr-defined]
        == expected_view_class
    )


@pytest.mark.django_db()
def test_home_page_returns_correct_html(client: Client) -> None:
    """
    Verify that the home page renders correctly.

    This test checks if the home page returns HTML content with the specified title
    tag correctly formatted, includes necessary language attributes, uses the correct
    HTML structure, and utilizes the designated template.
    It also validates the view function linked to this page.
    """
    _run_shared_logic(
        client=client,
        url="/",
        expected_title="Marnie's Maintenance Manager",
        expected_h1_text=None,
        expected_template_name="pages/home.html",
        expected_func_name="view",
        expected_url_name="home",
        expected_view_class=TemplateView,
    )


@pytest.mark.django_db()
def test_maintenance_jobs_page_returns_correct_html(client: Client) -> None:
    """
    Verify the maintenance jobs page loads with the correct HTML.

    This test ensures the maintenance jobs page is loaded with the correct title, a
    header tag, and the appropriate HTML structure.
    It also verifies the use of the correct template and checks the associated view
    function for this route.
    """
    _run_shared_logic(
        client=client,
        url="/jobs/",
        expected_title="Maintenance Jobs",
        expected_h1_text="Maintenance Jobs",
        expected_template_name="jobs/job_list.html",
        expected_func_name="view",
        expected_url_name="job_list",
        expected_view_class=JobListView,
    )


@pytest.mark.django_db()
def test_create_maintenance_job_page_returns_correct_html(client: Client) -> None:
    """
    Ensure the create maintenance job page returns the expected HTML content.

    This test checks for the presence of the correct title and header in the HTML of
    the create maintenance job page, ensures the HTML structure is properly formed, and
    confirms that the designated template is used.
    It also verifies the correct view function is managing this route.
    """
    _run_shared_logic(
        client=client,
        url="/jobs/create/",
        expected_title="Create Maintenance Job",
        expected_h1_text="Create Maintenance Job",
        expected_template_name="jobs/job_create.html",
        expected_func_name="view",
        expected_url_name="job_create",
        expected_view_class=JobCreateView,
    )
