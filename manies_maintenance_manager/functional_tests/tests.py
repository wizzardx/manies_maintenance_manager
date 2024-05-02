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


class ExistingAgentCreatesMaintenanceJobTest(CustomStaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        # You can add more options here if needed
        cls.browser = webdriver.Remote(
            command_executor="http://chrome:4444/wd/hub",
            options=options,
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def test_existing_agent_user_can_login_and_create_a_new_maintenance_job_and_logout(
        self,
    ):
        # One of Manies property manager contacts, Bob, an `Agent`, has heard of a cool
        # new webpage that's for helping to coordinate Manies Maintenance jobs with him.
        # He goes to check out its homepage
        self.browser.get(f"{self.live_server_url}")

        # He notices the page title and the navbar mention Manies Maintenance Manager
        self.assertIn("Manies Maintenance Manager", self.browser.title)

        # He sees the Sign In button in the navbar
        self.fail("Finish the test!")

        # He clicks on the Sign In button

        # This sends him to the Sign In page, where he notices that the page title and
        # the header mention Sign In

        # He types "bob" into the Username field

        # He types "bob" into the Password field

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
