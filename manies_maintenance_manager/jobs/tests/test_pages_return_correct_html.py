import re

import pytest
from django.views.generic import TemplateView

HTTP_SUCCESS_STATUS_CODE = 200


@pytest.mark.django_db()
def test_home_page_returns_correct_html(client):
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
