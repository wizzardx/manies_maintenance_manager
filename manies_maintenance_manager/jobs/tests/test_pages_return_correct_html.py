import pytest


@pytest.mark.django_db()
def test_home_page_returns_correct_html(client):
    response = client.get("/")
    response_text = response.content.decode()
    assert "<title>Manies Maintenance Manager</title>" in response_text
    assert '<html lang="en">' in response_text
    assert "</html>" in response_text
    # Check the first template if multiple are used
    assert response.template_name[0] == "pages/home.html"
