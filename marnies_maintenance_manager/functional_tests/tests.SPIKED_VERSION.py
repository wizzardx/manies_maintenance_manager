# ruff: noqa
"""Spiked Test Code that we need to merge into our main codebase."""

#
# class MySeleniumTests(CustomStaticLiveServerTestCase):
#
#     def test_basic_workflows(self):
#         User = get_user_model()
#         User.objects.create_user(username="bob", password="password", is_agent=True)
#         ## Also make sure that there is an associated email address, so that a
#         ## confirmation is not emailed when our testing 'bob' user logs in for
#         ## the first time. As a reminder, we are using django-allauth, which is
#         ## a bit more involved than the vanilla Django authentication system.
#         ## It most likely involves both the account.EmailConfirmation and
#         ## account.EmailAddress models:
#         user = User.objects.get(username="bob")
#         user.emailaddress_set.create(
#             email="bob@example.com", primary=True, verified=True
#         )
#
#         ## Create user for marnie, as well as registering his email address
#         User.objects.create_user(username="marnie", password="password")
#         user = User.objects.get(username="marnie")
#         user.emailaddress_set.create(
#             email="marnie@example.com", primary=True, verified=True
#         )

#         # TODO: Before signing in, the "jobs" link should not be visible
#         # TODO: Jobs link should only be visible to Agents, and not to Marnie
#
#         # TODO: Make sure an Agent can only see their own jobs
#
#         ## Check that 0 emails have been sent before Bob the Agent has clicked the "Submit" button
#         self.assertEqual(len(mail.outbox), 0)
#
#         ## Marnie should receive an email that was sent by the system on behalf of
#         ## Bob the agent.
#         self.assertEqual(len(mail.outbox), 1)
#         email = mail.outbox[0]
#         self.assertEqual(email.subject, "New maintenance request by bob")
#         self.assertIn("bob has made a new maintenance request.", email.body)
#         self.assertIn("Date: 2021-01-01", email.body)
#         self.assertIn("Address Details:\n\n1234 Main St.", email.body)
#         self.assertIn("GPS Link:\n\nhttps://www.google.com/maps", email.body)
#         self.assertIn("Quote Request Details:\n\nPlease fix my sink", email.body)
#         self.assertIn(
#             "PS: This mail is sent from an unmonitored email address. Please do not reply to this email.",
#             email.body,
#         )

#         ## Also clear our cookies, so that the next user flow can start fresh
#         self.browser.delete_all_cookies()
#
#         # Marnie received the email, so he goes to the main page of the website in his browser.
#         self.browser.get(self.live_server_url)
#
#         # He clicks the Sign In button
#         self.browser.find_element(By.LINK_TEXT, "Sign In").click()
#
#         # He enters his username and password
#         self.browser.find_element(By.ID, "id_login").send_keys("marnie")
#         self.browser.find_element(By.ID, "id_password").send_keys("password")
#
#         # He clicks the Sign In button
#         self.browser.find_element(By.CLASS_NAME, "btn-primary").click()
#
#         ## TODO: Check that Jobs list is only visible to Agents, and not to Marnie.
#         # self.assertEqual(len(self.browser.find_elements(By.LINK_TEXT, "Jobs")), 0)
#
#         # Marnie notices the Agents link
#         agents_link = self.browser.find_element(By.LINK_TEXT, "Agents")
#
#         ## TODO: Check that Agents link is only visible to Marnie, and not to Agents
#
#         # Marnie clicks on the Agents link
#         agents_link.click()
#
#         # He notices the page title
#         self.assertIn("Agents", self.browser.title)
#
#         # He sees a heading for Agents
#         self.assertIn("Agents", self.browser.find_element(By.TAG_NAME, "h1").text)
#
#         # He sees a listing of Agents.
#         agent_list = self.browser.find_element(By.ID, "agent_list")
#         agent_list_items = agent_list.find_elements(By.TAG_NAME, "li")
#         self.assertEqual(len(agent_list_items), 1)
#
#         # He sees that the first-listed agent is bob
#         self.assertIn("bob", agent_list.text)
#         self.fail("Finish the test!")
#
#         # He sees a listing of Agents.
#         xxxxxxx
#
#         # For now he should see the "Bob" agent.
#         xxxxxxx
#
#         # Marnie clicks on the "Bob" agent.
#         xxxxxxx
#
#         # He sees a link that will take him to the jobs that Bob has created.
#         xxxxxxx
#
#         # He clicks on the link.
#         xxxxxxx
#
#         # He sees a list of jobs that Bob has created.
#         xxxxxxx
#
#         # This should just be the one job that Bob created.
#         xxxxxxx
#
#         # He clicks on the job.
#         xxxxxxx
#
#         # He sees the details of the job that bob created
#         xxxxxxx
#
#         # He should not see an "Edit" button
#         xxxxxxx
#
#         # However, there are some new fields that he can fill out.
#
#         # He fills out the new fields -
#
#         # He clicks the "Submit" button
#
#         # He sees the updated job details
#
#         # There is no longer a Submit button visible
#
#         # Clicking the Submit button should have emailed Bob
#
#         # Marnie logs out
#
#         ## Clear the cookies again
#
#         # Having received the email, Bob logs back in.
#
#         # He clicks the Jobs button
#
#         # He sees the list of jobs
#
#         # He clicks on the job
#
#         # He sees the details of the job, including the new details that Marnie filled out
#         xxxxxxxxxxxxx
#
#         # He clicks the Jobs button
#         self.browser.find_element(By.LINK_TEXT, "Jobs").click()
#
#         ## TODO: Test having the user click on the job and being able to view it, but not being able to edit anything
#         xxxxxxx
#
#         ## This causes an email to be sent.
#         ## Hack: See if we're able to either see the sent email in the testing outbox, or in mailpit?
#         xxxxxxxxxxxxxxxx
#
#         # import time
#         # print("Sleeping for 1000 seconds")
#         # time.sleep(1000)
#         # xxxx
#         # self.browser.get(f"{self.live_server_url}/some_page")
#         # # Add assertions or interactions here
