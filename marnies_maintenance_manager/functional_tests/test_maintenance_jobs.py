"""Functional tests for the 'Maintenance Jobs' feature.

These tests ensure that the job maintenance functionalities work as expected
from a user's perspective in the Marnie's Maintenance Manager application.
"""

# pylint: disable=redefined-outer-name,unused-argument,magic-value-comparison

import time
from collections.abc import Callable
from collections.abc import Iterator
from typing import Any

import pytest
from pytest_django.live_server_helper import LiveServer
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from marnies_maintenance_manager.users.models import User

MAX_WAIT = 5  # Maximum time to wait during retries, before failing the test


@pytest.fixture()
def browser() -> Iterator[WebDriver]:
    """Provide a configured Selenium WebDriver for testing in a Docker environment.

    Yields:
        WebDriver: A WebDriver instance for use in tests, ensuring it's closed
                   afterward.
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
    """Modify the live_server URL to use 'django' instead of '0.0.0.0'.

    Args:
        live_server (LiveServer): The pytest-django fixture providing a live server.

    Returns:
        str: The modified URL as a string.
    """
    return live_server.url.replace("0.0.0.0", "django")  # noqa: S104


def wait_until(fn: Callable[[], Any]) -> Any:
    """Retry an action until it succeeds or the maximum wait time is reached.

    Args:
        fn (Callable[[], Any]): The function to execute.

    Returns:
        Any: The result of the function call.

    Raises:
        ElementClickInterceptedException: If the action does not succeed within the
                                          allotted time.
    """
    start_time = time.time()
    while True:  # pylint: disable=while-used
        try:
            return fn()
        except ElementClickInterceptedException:
            if time.time() - start_time > MAX_WAIT:
                raise  # pragma: no cover
            time.sleep(0.1)


def _sign_into_website(browser: WebDriver, username: str) -> None:
    # He sees the Sign In button in the navbar
    sign_in_button = browser.find_element(By.LINK_TEXT, "Sign In")

    # He clicks on the Sign In button

    ## Note: Django-FastDev causes a DeprecationWarning to be logged when using the
    ## {% if %} template tag. This is somewhere deep within the Django-Allauth package,
    ## while handling a GET request to the /accounts/login/ URL. We can ignore this
    ## for our testing.
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
    username_field.send_keys(username)

    # He types "secret" into the Password field
    password_field = browser.find_element(By.ID, "id_password")
    password_field.send_keys("password")

    # He clicks the "Sign In" button
    sign_in_button = browser.find_element(By.CLASS_NAME, "btn-primary")
    sign_in_button.click()

    # This takes him to his user page (where he can manage his user further).
    # He also sees this in the page title bar
    assert f"User: {username}" in browser.title


def _sign_out_of_website_and_clean_up(browser: WebDriver) -> None:
    # He clicks on the Sign Out button
    sign_out_button = browser.find_element(By.LINK_TEXT, "Sign Out")

    ## Note: Django-FastDev causes a DeprecationWarning to be logged when using the
    ## {% if %} template tag. This is somewhere deep within the Django-Allauth package,
    ## most likely while processing the templates for /accounts/logout/. We can also
    # ignore this for our testing.
    with pytest.warns(
        DeprecationWarning,
        match="set FASTDEV_STRICT_IF in settings, and use {% ifexists %} instead of "
        "{% if %}",
    ):
        sign_out_button.click()

    # An "Are you sure you want to sign out?" dialog pops up, asking him to confirm
    # that he wants to sign out.
    confirm_sign_out_button = browser.find_element(By.CLASS_NAME, "btn-primary")
    confirm_sign_out_button.click()

    # Also tidy up here by cleaning up all the browser cookies.
    browser.delete_all_cookies()

    # Satisfied, he goes back to sleep


def _create_new_job(
    browser: WebDriver,
    live_server_url: str,
) -> None:
    # pylint: disable=too-many-locals

    # Marnie's client Bob has heard of Marnie's cool new maintenance management site.
    # He goes to check out its homepage.
    browser.get(live_server_url)

    # He notices the page title
    assert "Marnie's Maintenance Manager" in browser.title

    ## Go through the process of logging into the website as 'bob' user:
    _sign_into_website(browser, "bob")

    # He sees some basic instructions on this page that tell him the next step that
    # he should click on the "Maintenance Jobs" link next.
    expected_msg = "Click on the 'Maintenance Jobs' link to create a new job."
    assert expected_msg in browser.page_source

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

    # He types 01/01/2021 into the "Date" field (dd/mm/yyyy) format.
    # It's a custom input field that adds the "-" values in for us.
    date_field.send_keys("01012021")

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
    wait_until(submit_button.click)

    # This sends him back to the "Maintenance Jobs" page, where he notices that the
    # page title and the header mention Maintenance Jobs like before.
    assert "Maintenance Jobs" in browser.title
    assert "Maintenance Jobs" in browser.find_element(By.TAG_NAME, "h1").text

    # He notices that the new Maintenance Job is listed on the web page in a table
    table = browser.find_element(By.ID, "id_list_table")
    rows = table.find_elements(By.TAG_NAME, "tr")

    ## There should be two rows:
    assert len(rows) == 2  # noqa: PLR2004

    ## The first row is the header row
    header_row = rows[0]
    header_cell_texts = [
        cell.text for cell in header_row.find_elements(By.TAG_NAME, "th")
    ]
    assert header_cell_texts == [
        "Number",
        "Date",
        "Address Details",
        "GPS Link",  # This is the displayed text, on-screen it's a link
        "Quote Request Details",
        "Date of Inspection",
        "Quote",
    ]

    ## The second row is the new job
    row = rows[1]
    cell_texts = [cell.text for cell in row.find_elements(By.TAG_NAME, "td")]

    ## Make sure the cell text contents match the expected values.
    assert cell_texts == [
        "1",  # This is for the row number, automatically added by the system.
        "2021-01-01",
        "Department of Home Affairs Bellville",
        "GPS",  # This is the displayed text, on-screen it's a link
        "Please fix the leaky faucet in the staff bathroom",
        "",  # This is for the Date of Inspection, which is empty for now
        "",  # This is for the Quote, which is empty for now
    ]

    # Satisfied, he goes back to sleep
    _sign_out_of_website_and_clean_up(browser)


@pytest.mark.django_db()
def test_existing_agent_user_can_login_and_create_a_new_maintenance_job_and_logout(
    browser: WebDriver,
    live_server_url: str,
    bob_agent_user: User,
    marnie_user_client: User,
) -> None:
    """Ensure a user can log in, create a job, and log out.

    This test simulates a user logging into the system, creating a new
    maintenance job, and logging out, verifying each critical step.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        bob_agent_user (User): The user instance for Bob, who is an agent.
        marnie_user_client (User): The user instance for Marnie, included for context.
    """
    # The body of our logic is moved to a helper function, because we're going
    # to be re-using this logic a lot of times for other functional tests.
    _create_new_job(browser, live_server_url)


# pylint: disable=too-many-statements,too-many-locals
def test_marnie_can_view_agents_job(
    browser: WebDriver,
    live_server_url: str,
    marnie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure Marnie can view the jobs submitted by Bob the Agent.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        marnie_user (User): The user instance for Marnie.
        bob_agent_user (User): The user instance for Bob, who is an agent.
    """
    ## First, quickly run through the steps of an Agent creating a new Job.
    _create_new_job(browser, live_server_url)

    # Marnie received the notification email (in an earlier step), and so now he wants
    # to take a look at the Maintenance Job details
    # that were submitted by the Agent.

    # Marnie logs into the system.
    _sign_into_website(browser, "marnie")

    # He sees some text on the current page that informs him that he can see the
    # per-agent "spreadsheets" over under the "Agents" link.
    expected_msg = "Click on the 'Agents' link to view each Agents Maintenance Jobs."
    assert expected_msg in browser.page_source

    # He also notices an "Agents" links in the navbar.
    agents_link = browser.find_element(By.LINK_TEXT, "Agents")

    # He clicks on the Agents link
    agents_link.click()

    # This takes him to a page listing the Agents. Each Agent is a link.
    assert "Agents" in browser.title
    assert "Agents" in browser.find_element(By.TAG_NAME, "h1").text
    assert "bob" in browser.page_source

    # He clicks on the link for Bob.
    bob_agent_link = browser.find_element(By.LINK_TEXT, "bob")
    bob_agent_link.click()

    # This takes him to the Maintenance Jobs page for Bob the Agent.
    assert "Maintenance Jobs for bob" in browser.title
    assert "Maintenance Jobs for bob" in browser.find_element(By.TAG_NAME, "h1").text

    # On this page he can see the list of Maintenance Jobs that Bob has submitted.
    table = browser.find_element(By.ID, "id_list_table")
    rows = table.find_elements(By.TAG_NAME, "tr")

    ## There should be two rows:
    assert len(rows) == 2  # noqa: PLR2004

    ## The first row is the header row
    header_row = rows[0]
    header_cell_texts = [
        cell.text for cell in header_row.find_elements(By.TAG_NAME, "th")
    ]
    assert header_cell_texts == [
        "Number",
        "Date",
        "Address Details",
        "GPS Link",  # This is the displayed text, on-screen it's a link
        "Quote Request Details",
        "Date of Inspection",
        "Quote",
    ]

    # The second row is the set of job details submitted by Bob earlier
    row = rows[1]
    cell_texts = [cell.text for cell in row.find_elements(By.TAG_NAME, "td")]

    ## Make sure the cell text contents match the expected values.
    assert cell_texts == [
        "1",  # This is for the row number, automatically added by the system.
        "2021-01-01",
        "Department of Home Affairs Bellville",
        "GPS",  # This is the displayed text, on-screen it's a link
        "Please fix the leaky faucet in the staff bathroom",
        "",  # This is for the Date of Inspection, which is empty for now
        "",  # This is for the Quote, which is empty for now
    ]

    # Since he's not an Agent, he does not see the "Create Maintenance Job" link.
    with pytest.raises(NoSuchElementException):
        browser.find_element(By.LINK_TEXT, "Create Maintenance Job").click()

    # He sees that the #1 in the Number column is a link.
    number_link = browser.find_element(By.LINK_TEXT, "1")

    # He sees an instruction which tells him to click on the link in the Number column
    # to view the details of each Maintenance Job.
    expected_msg = "Click on the number in each row to go to the Job details."
    assert expected_msg in browser.page_source

    # He clicks on the #1 link in the Number column.
    number_link.click()

    # This takes him to a page where he can see (but not modify) the previously -
    # submitted details, such as the Date, Address Details, GPS Link, and Quote Request
    # Details.
    assert "Maintenance Job Details" in browser.title
    assert "Maintenance Job Details" in browser.find_element(By.TAG_NAME, "h1").text

    # The previously submitted Maintenance Job details are displayed on the page.
    assert "2021-01-01" in browser.page_source
    assert "Department of Home Affairs Bellville" in browser.page_source
    assert "GPS" in browser.page_source
    assert "Please fix the leaky faucet in the staff bathroom" in browser.page_source


def _update_job_with_inspection_date_and_quote(browser: WebDriver) -> None:
    # Marnie logs into the system.
    _sign_into_website(browser, "marnie")

    # He clicks on the Agents link
    agents_link = browser.find_element(By.LINK_TEXT, "Agents")
    agents_link.click()

    # He clicks on the link for Bob.
    bob_agent_link = browser.find_element(By.LINK_TEXT, "bob")
    bob_agent_link.click()

    # This takes him to the Maintenance Jobs page for Bob the Agent.

    # He clicks on the link with the number 1 in the text:
    number_link = browser.find_element(By.LINK_TEXT, "1")
    number_link.click()

    # Just below the existing details, he sees an "Update" link.
    update_link = browser.find_element(By.LINK_TEXT, "Update")

    # He clicks on the Edit link
    update_link.click()

    # On the next page, he sees that the page title and header mention "Update
    # Maintenance Job"
    assert "Update Maintenance Job" in browser.title
    assert "Update Maintenance Job" in browser.find_element(By.TAG_NAME, "h1").text

    # He also sees on this page, that he can edit (only) these fields:
    # - Date of Inspection
    inspection_date_field = browser.find_element(By.ID, "id_date_of_inspection")

    # - Quote (an invoice to be uploaded by Marnie, for the fixes to be done for
    #   the site he has visited)>
    quote_invoice_field = browser.find_element(By.ID, "id_quote")

    # As well as a "submit" button just below those two:
    submit_button = browser.find_element(By.CLASS_NAME, "btn-primary")

    # But in particular, he doesn't see fields that only the Agent should be able to
    # edit, while submitting the job.
    with pytest.raises(NoSuchElementException):
        browser.find_element(By.ID, "id_date")
    with pytest.raises(NoSuchElementException):
        browser.find_element(By.ID, "id_address_details")
    with pytest.raises(NoSuchElementException):
        browser.find_element(By.ID, "id_gps_link")
    with pytest.raises(NoSuchElementException):
        browser.find_element(By.ID, "id_quote_request_details")

    # He inputs a date into the inspection date field.
    inspection_date_field.send_keys("02012021")

    # He uploads a Quote invoice.
    quote_invoice_field.send_keys(
        "/app/marnies_maintenance_manager/functional_tests/test.pdf",
    )

    # He clicks the "submit" button.
    submit_button.click()

    # This takes him back to the Maintenance Jobs page for Bob the Agent.
    assert "Maintenance Jobs for bob" in browser.title
    assert "Maintenance Jobs for bob" in browser.find_element(By.TAG_NAME, "h1").text

    # He also sees a flash notification that an email has been sent to Bob.
    expected_msg = "An email has been sent to bob."
    assert expected_msg in browser.page_source

    # He sees that the new details are now listed in the table.
    table = browser.find_element(By.ID, "id_list_table")
    rows = table.find_elements(By.TAG_NAME, "tr")

    ## There should be exactly one row here
    assert len(rows) == 2  # noqa: PLR2004

    ## Get the row, and confirm that the details include everything submitted up until
    ## now.
    row = rows[1]
    cell_texts = [cell.text for cell in row.find_elements(By.TAG_NAME, "td")]
    assert cell_texts == [
        "1",
        "2021-01-01",
        "Department of Home Affairs Bellville",
        "GPS",
        "Please fix the leaky faucet in the staff bathroom",
        "2021-02-01",
        "Download Quote",
    ]

    # He clicks on the #1 number again:
    number_link = browser.find_element(By.LINK_TEXT, "1")
    number_link.click()

    # Over here he can now see the inspection date:
    assert "2021-02-01" in browser.page_source

    # And also, there is a link to the Quote invoice, with the text "Download Quote":
    quote_link = browser.find_element(By.LINK_TEXT, "Download Quote")

    # If he looks at the link more closely, he can see it's a PDF file:
    download_url = quote_link.get_attribute("href")
    assert isinstance(download_url, str)

    ## Example href value:
    ## http://django:37369/jobs/d7f07107-e711-44b9-be0a-1fab149229a0/download-quote/
    assert download_url.endswith("/download-quote/")

    ## Sign out and tidy up cookies:
    _sign_out_of_website_and_clean_up(browser)


def test_marnie_can_update_agents_job(
    browser: WebDriver,
    live_server_url: str,
    marnie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure Marnie can update the details of a job submitted by Bob the Agent.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        marnie_user (User): The user instance for Marnie.
        bob_agent_user (User): The user instance for Bob, who is an agent.
    """
    ## First, quickly run through the steps of an Agent creating a new Job.
    _create_new_job(browser, live_server_url)

    # Most of our logic is now in this shared function:
    _update_job_with_inspection_date_and_quote(browser)


def test_bob_can_refuse_marnies_quote(
    browser: WebDriver,
    live_server_url: str,
    marnie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure Bob can refuse the quote submitted by Marnie.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        marnie_user (User): The user instance for Marnie.
        bob_agent_user (User): The user instance for Bob, who is an agent.
    """
    ## First, quickly run through the steps of an Agent creating a new Job.
    _create_new_job(browser, live_server_url)

    ## Next, Marnie does an inspection, and updates the inspection date and quote.
    _update_job_with_inspection_date_and_quote(browser)

    # Bob receives the email notification that Marnie has done the initial inpection,
    # so he signs in to the website
    _sign_into_website(browser, "bob")

    # He clicks on the "Maintenance Jobs" link:
    maintenance_jobs_link = browser.find_element(By.LINK_TEXT, "Maintenance Jobs")
    maintenance_jobs_link.click()

    # He can see from the Title and the Heading that he is in the "Maintenance Jobs"
    # page.
    assert "Maintenance Jobs" in browser.title
    assert "Maintenance Jobs" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees his original job details over there.
    table = browser.find_element(By.ID, "id_list_table")
    rows = table.find_elements(By.TAG_NAME, "tr")

    ## There should be exactly one row here
    assert len(rows) == 2  # noqa: PLR2004

    ## Get the row, and confirm that the details include everything submitted up until
    ## now, as well as the details that Marnie added.
    row = rows[1]
    cell_texts = [cell.text for cell in row.find_elements(By.TAG_NAME, "td")]
    assert cell_texts == [
        "1",
        "2021-01-01",
        "Department of Home Affairs Bellville",
        "GPS",
        "Please fix the leaky faucet in the staff bathroom",
        "2021-02-01",
        "Download Quote",
    ]

    # He clicks on the "1" link to go to the details for the Job.
    number_link = browser.find_element(By.LINK_TEXT, "1")
    number_link.click()

    # He can see from the Title and the Heading that he is in the "Maintenance Job
    # Details" page.
    assert "Maintenance Job Details" in browser.title
    assert "Maintenance Job Details" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees a "Refuse Quote" button and an "Accept Quote" button.
    refuse_button = browser.find_element(By.LINK_TEXT, "Refuse Quote")
    accept_button = browser.find_element(By.LINK_TEXT, "Accept Quote")

    # He clicks on the "Refuse Quote" button.
    refuse_button.click()

    # A warning dialog comes up, asking him to confirm the refusal.
    # He sees two buttons, "Cancel" and "OK"
    _cancel_refusal_button = browser.find_element(By.CLASS_NAME, "btn-secondary")
    confirm_refusal_button = browser.find_element(By.CLASS_NAME, "btn-primary")

    # He Clicks OK, confirming the refusal.
    confirm_refusal_button.click()

    # A message flash comes up, saying that Marnie was emailed
    expected_msg = "An email has been sent to marnie."
    assert expected_msg in browser.page_source

    # He now sees a "Job Status: Refused" entry on the page.
    assert "Job Status: Refused" in browser.page_source

    # He does not see the "Refuse Job" button any longer.
    with pytest.raises(NoSuchElementException):
        browser.find_element(By.LINK_TEXT, "Refuse Quote")

    # He does still see an "Accept Job" button.
    assert accept_button.is_displayed()

    # He clicks on the "Maintenance Jobs" link to take him back to the main listing
    maintenance_jobs_link = browser.find_element(By.LINK_TEXT, "Maintenance Jobs")
    maintenance_jobs_link.click()

    # In the "Accept or Reject A/R" cell of his Job in the listing, he can see the
    # text "Rejected"
    table = browser.find_element(By.ID, "id_list_table")
    rows = table.find_elements(By.TAG_NAME, "tr")
    row = rows[1]
    cell_texts = [cell.text for cell in row.find_elements(By.TAG_NAME, "td")]
    assert cell_texts == [
        "1",
        "2021-01-01",
        "Department of Home Affairs Bellville",
        "GPS",
        "Please fix the leaky faucet in the staff bathroom",
        "2021-02-01",
        "Rejected",
    ]

    # Satisfied, he logs out of the website, and goes back to sleep
    _sign_out_of_website_and_clean_up(browser)

    pytest.fail("Complete this test!")
