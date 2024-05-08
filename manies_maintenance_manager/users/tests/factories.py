"""Factory module for creating user instances for testing purposes."""

from collections.abc import Sequence

from factory import Faker
from factory import post_generation
from factory.django import DjangoModelFactory

from manies_maintenance_manager.users.models import User


class UserFactory(DjangoModelFactory):  # type: ignore[misc]
    """Factory for generating User model instances."""

    username = Faker("user_name")
    email = Faker("email")
    name = Faker("name")

    @post_generation  # type: ignore[misc]
    def password(self, create: bool, extracted: Sequence[str], **kwargs: str) -> None:  # noqa: FBT001
        """
        Generate and set a password for the user.

        Args:
            create (bool): Whether the user is being created.
            extracted (Sequence[str]): Custom password, if provided.
            **kwargs (str): Additional keyword arguments.
        """
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        self.set_password(password)

    @classmethod
    def _after_postgeneration(
        cls: type["UserFactory"],
        instance: User,
        create: bool,  # noqa: FBT001
        results: dict[str, str | None],
    ) -> None:
        """
        Ensure instance is saved after post-generation hooks if changes are made.

        Args:
            cls (type["UserFactory"]): The current class.
            instance (User): The user instance being created.
            create (bool): Flag to check if creation is ongoing.
            results (dict[str, str | None]): Post-generation hook results.
        """
        if create and results and not cls._meta.skip_postgeneration_save:
            # Some post-generation hooks ran, and may have modified us.
            instance.save()

    class Meta:
        """Meta options for UserFactory."""

        model = User
        django_get_or_create = ["username"]
