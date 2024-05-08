"""
Functional tests for the 'Maintenance Jobs' feature.

These tests ensure that the job maintenance functionalities work as expected
from a user's perspective in the Manies Maintenance Manager application.
"""

from collections.abc import Iterator

import pytest
from pytest_django.live_server_helper import LiveServer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from manies_maintenance_manager.users.models import User


@pytest.fixture()
def browser() -> Iterator[WebDriver]:
    """
    Provide a configured Selenium WebDriver for testing in a Docker environment.

    Yields a WebDriver instance for use in tests, ensuring it's closed afterward.
    """
    options = Options()
    # You can add more options here if needed
    driver = webdriver.Remote(
        command_executor="http://chrome:4444/wd/hub",
        options=options,
    )

    yield driver

    driver.quit()


@pytest.fixture()
def live_server_url(live_server: LiveServer) -> str:
    """
    Modify the live_server URL to use 'django' instead of '0.0.0.0'.

    This change supports Docker inter-container communication during testing.
    Returns the modified URL as a string.
    """
    return live_server.url.replace("0.0.0.0", "django")  # noqa: S104


@pytest.mark.django_db()
def test_existing_agent_user_can_login_and_create_a_new_maintenance_job_and_logout(
    browser: WebDriver,
    live_server_url: str,
    bob_agent_user: User,
) -> None:
    """
    Ensure a user can log in, create a job, and log out.

    This test simulates a user logging into the system, creating a new
    maintenance job, and logging out, verifying each critical step.
    """
    # Manies client Bob has heard of Manies cool new maintenance management site.
    # He goes to check out its homepage.
    browser.get(live_server_url)

    # He notices the page title
    assert "Manies Maintenance Manager" in browser.title

    # He sees the Sign In button in the navbar
    sign_in_button = browser.find_element(By.LINK_TEXT, "Sign In")

    # He clicks on the Sign In button

    ## Note: Django-FastDev causes a DeprecationWarning to be logged when using the
    ## {% if %} template tag. This is somewhere deep within the Django-Allauth package,
    ## while handling a GET request to the /accounts/login/ URL. We can ignore this
    ## for the purpose of our testing.
    with pytest.warns(
        DeprecationWarning,
        match="set FASTDEV_STRICT_IF in settings, and use {% ifexists %} instead of "
        "{% if %}",
    ):
        sign_in_button.click()

    # This sends him to the Sign In page, where he notices that the page title and
    # the header mention Sign In
    assert "Sign In" in browser.title

    # He types "bob" into the Username field
    username_field = browser.find_element(By.ID, "id_login")
    username_field.send_keys("bob")

    # He types "secret" into the Password field
    password_field = browser.find_element(By.ID, "id_password")
    password_field.send_keys("password")

    # He clicks the "Sign In" button
    sign_in_button = browser.find_element(By.CLASS_NAME, "btn-primary")
    sign_in_button.click()

    # This takes him to his user page (where he can manage his user further). He
    # also sees this in the page title bar
    assert "User: bob" in browser.title

    # He sees the "Maintenance Jobs" link in the navbar
    maintenance_jobs_link = browser.find_element(By.LINK_TEXT, "Maintenance Jobs")

    # He clicks on the "Maintenance Jobs" link
    maintenance_jobs_link.click()

    # This sends him to the "Maintenance Jobs" page, where he notices that the page
    # title and the header mention Jobs
    assert "Maintenance Jobs" in browser.title
    assert "Maintenance Jobs" in browser.find_element(By.TAG_NAME, "h1").text

    # He notices a "Create Maintenance Job" link
    create_maintenance_job_link = browser.find_element(
        By.LINK_TEXT,
        "Create Maintenance Job",
    )

    # He clicks on the "Create Maintenance Job" link
    create_maintenance_job_link.click()

    # This sends him to the "Create Maintenance Job" page, where he notices that
    # the page title and the header mention Create Maintenance Job
    assert "Create Maintenance Job" in browser.title
    assert "Create Maintenance Job" in browser.find_element(By.TAG_NAME, "h1").text

    # He notices entry fields "Date", "Address Details", "GPS Link", and "Quote
    # Request Details", as well as a "Submit" button
    date_field = browser.find_element(By.ID, "id_date")
    address_details_field = browser.find_element(By.ID, "id_address_details")
    gps_link_field = browser.find_element(By.ID, "id_gps_link")
    quote_request_details_field = browser.find_element(
        By.ID,
        "id_quote_request_details",
    )
    submit_button = browser.find_element(By.CLASS_NAME, "btn-primary")

    # He types 2021-01-01 into the "Date" field
    date_field.send_keys("2021-01-01")

    # He types "Department of Home Affairs Bellville" into the "Address Details"
    # field
    address_details_field.send_keys("Department of Home Affairs Bellville")

    # He copy-pastes "https://maps.app.goo.gl/mXfDGVfn1dhZDxJj7" into the
    # "GPS Link" field
    gps_link_field.send_keys("https://maps.app.goo.gl/mXfDGVfn1dhZDxJj7")

    # He types "Please fix the leaky faucet in the staff bathroom" into the
    # "Quote Request Details" field
    quote_request_details_field.send_keys(
        "Please fix the leaky faucet in the staff bathroom",
    )

    # He clicks the Submit button
    submit_button.click()

    # This sends him back to the "Maintenance Jobs" page, where he notices that the
    # page title and the header mention Maintenance Jobs like before.
    assert "Maintenance Jobs" in browser.title
    assert "Maintenance Jobs" in browser.find_element(By.TAG_NAME, "h1").text

    # He notices that the new Maintenance Job is listed on the web page in a table
    table = browser.find_element(By.ID, "id_list_table")
    rows = table.find_elements(By.TAG_NAME, "tr")

    ## There should be only one row:
    assert len(rows) == 1
    row = rows[0]

    ## Grab the cell text contents from the row
    cell_texts = [cell.text for cell in row.find_elements(By.TAG_NAME, "td")]

    ## Make sure the cell text contents match the expected values.
    assert cell_texts == [
        "1",  # This is for the row number, automatically added by the system.
        "2021-01-01",
        "Department of Home Affairs Bellville",
        "https://maps.app.goo.gl/mXfDGVfn1dhZDxJj7",
        "Please fix the leaky faucet in the staff bathroom",
    ]

    # He clicks on the Sign Out button
    sign_out_button = browser.find_element(By.LINK_TEXT, "Sign Out")

    ## Note: Django-FastDev causes a DeprecationWarning to be logged when using the
    ## {% if %} template tag. This is somewhere deep within the Django-Allauth package,
    ## most likely while processing the templates for /accounts/logout/. We can also
    # ignore this for the purpose of our testing.
    with pytest.warns(
        DeprecationWarning,
        match="set FASTDEV_STRICT_IF in settings, and use {% ifexists %} instead of "
        "{% if %}",
    ):
        sign_out_button.click()

    # Satisfied, he goes back to sleep
