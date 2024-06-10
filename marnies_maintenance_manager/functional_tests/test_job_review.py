"""Functional tests for job review.

These tests ensure that the job review functionalities, including viewing
job details submitted by agents, work as expected from a user's perspective
in the Marnie's Maintenance Manager application.
"""

# pylint: disable=unused-argument, magic-value-comparison

import pytest
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from marnies_maintenance_manager.functional_tests.utils import _check_jobs_page_table
from marnies_maintenance_manager.functional_tests.utils import _create_new_job
from marnies_maintenance_manager.functional_tests.utils import _sign_into_website
from marnies_maintenance_manager.users.models import User


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

    ## Thoroughly check that the table has the correct headings and row contents.
    _check_jobs_page_table(browser)

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
