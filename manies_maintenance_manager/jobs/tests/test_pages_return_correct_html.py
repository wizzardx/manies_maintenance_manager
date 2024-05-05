import pytest
from django.views.generic import TemplateView


@pytest.mark.django_db()
def test_home_page_returns_correct_html(client):
    response = client.get("/")
    assert response.status_code == 200

    # Decode response content to check for specific HTML elements
    response_text = response.content.decode()
    assert "<title>Manies Maintenance Manager</title>" in response_text
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
    assert response.status_code == 200

    # Decode response content to check for specific HTML elements
    response_text = response.content.decode()
    assert "<title>Maintenance Jobs</title>" in response_text
    assert "<h1>Maintenance Jobs</h1>" in response_text
    assert '<html lang="en">' in response_text
    assert "</html>" in response_text

    # Verify that the correct template was used
    assert "pages/job_list.html" in [t.name for t in response.templates]

    # Validate details about the view function used to handle the route
    assert response.resolver_match.func.__name__ == "job_list"
    assert response.resolver_match.url_name == "job_list"
