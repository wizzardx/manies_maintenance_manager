import pytest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class CustomStaticLiveServerTestCase(StaticLiveServerTestCase):
    # Bind to all interfaces. This is so that in our dev environment, Chrome
    # running under Selenium in another Docker container, can connect to
    # our container. This is a bit of an ugly workaround to the default
    # `StaticLiveServerTestCase` behavior.
    host = "0.0.0.0"  # noqa: S104

    @property
    def live_server_url(self):
        """
        Returns the live server URL with the internal Docker service name.
        """
        return f"http://django:{self.server_thread.port}"


@pytest.fixture(scope="class")
def live_server(request):
    # Set up the custom live server
    live_server = CustomStaticLiveServerTestCase()
    live_server.setUpClass()
    request.cls.live_server = live_server

    yield live_server

    live_server.tearDownClass()


@pytest.fixture(scope="class")
def browser(request):
    options = Options()
    # You can add more options here if needed
    driver = webdriver.Remote(
        command_executor="http://chrome:4444/wd/hub",
        options=options,
    )
    request.cls.browser = driver

    yield driver

    driver.quit()


@pytest.mark.usefixtures("live_server", "browser")
class TestExistingAgentCreatesMaintenanceJob:
    def test_existing_agent_user_can_login_and_create_a_new_maintenance_job_and_logout(
        self,
    ):
        # Use the live_server_url from the modified fixture
        self.browser.get(self.live_server.live_server_url)

        # Continue with the test steps
        assert "Manies Maintenance Manager" in self.browser.title

        # He sees the Sign In button in the navbar
        pytest.fail("Finish the test!")

        # He clicks on the Sign In button

        # This sends him to the Sign In page, where he notices that the page title and
        # the header mention Sign In

        # He types "bob" into the Username field

        # He types "secret" into the Password field

        # He clicks the "Sign In" button

        # This sends him to the "Maintenance Jobs" page, where he notices that the page
        # title and the header mention Jobs

        # He notices a "Create Maintenance Job" link

        # He clicks on the "Create Maintenance Job" link

        # This sends him to the "Create Maintenance Job" page, where he notices that
        # the page title and the header mention Create Maintenance Job

        # He notices entry fields "Date", "Address Details", "GPS Link", and "Quote
        # Request Details"

        # He types 2021-01-01 into the "Date" field

        # He types "Department of Home Affairs Bellville" into the "Address Details"
        # field

        # He copy-pastes "https://maps.app.goo.gl/mXfDGVfn1dhZDxJj7" into the
        # "GPS Link" field

        # He types "Please fix the leaky faucet in the staff bathroom" into the
        # "Quote Request Details" field

        # He notices and clicks on a "Submit" button

        # This sends him back to the "Maintenance Jobs" page, where he notices that the
        # page title and the header mention Maintenance Jobs like before.

        # He notices that the new Maintenance Job is listed on the web page.

        # He clicks on the Sign Out button

        # Satisfied, he goes back to sleep
