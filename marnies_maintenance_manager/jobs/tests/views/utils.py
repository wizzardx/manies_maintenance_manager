"""Tests for HTML content validation in Marnie's Maintenance Manager application views.

This module checks the HTML content returned by various views in the Marnie's
Maintenance Manager application. It covers tests for the home page, maintenance jobs
page, and the create maintenance job page. Each test ensures that the respective page
renders the expected HTML structure, elements, and uses the appropriate template.

The Django test client is used for making requests, and BeautifulSoup for parsing the
returned HTML. This setup ensures not only a successful HTTP response but also verifies
the accuracy of the HTML content against expected patterns and structures.

To execute these tests, run the following command:
`docker compose -f docker-compose.local.yml run --rm django pytest \
    marnies_maintenance_manager/jobs/tests/utils.py`
"""

# pylint: disable=unused-argument

from typing import cast

from bs4 import BeautifulSoup
from django.http.response import HttpResponse
from django.test.client import Client
from django.views.generic.base import View as BaseView

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
        assert (
            response.resolver_match.func.view_class  # type: ignore[attr-defined]
            == expected_view_class
        ), (
            f"Found {response.resolver_match.func.view_class} "  # type: ignore[attr-defined]
            f"instead of {expected_view_class}"
        )

    return cast(HttpResponse, response)
