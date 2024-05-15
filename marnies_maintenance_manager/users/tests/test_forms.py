"""Module for all Form Tests."""

from django.utils.translation import gettext_lazy as _

from marnies_maintenance_manager.users.forms import UserAdminCreationForm
from marnies_maintenance_manager.users.models import User

# pylint: disable=magic-value-comparison, no-self-use


class TestUserAdminCreationForm:
    """Test class for all tests related to the UserAdminCreationForm."""

    # pylint: disable=too-few-public-methods

    def test_username_validation_error_msg(self, user: User) -> None:
        """Verify username uniqueness validation for UserAdminCreationForm.

        Args:
            user (User): A user instance used to test username uniqueness.

        Ensures that:
        1) A new user with an existing username cannot be added.
        2) Only 1 error is raised by the form.
        3) The expected error message is raised.
        """
        # The user already exists,
        # hence cannot be created.
        form = UserAdminCreationForm(
            {
                "username": user.username,
                "password1": user.password,
                "password2": user.password,
            },
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "username" in form.errors
        assert form.errors["username"][0] == _("This username has already been taken.")
