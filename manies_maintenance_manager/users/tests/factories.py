"""Factory module for creating user instances for testing purposes."""

# pylint: disable=line-too-long

from collections.abc import Sequence

from factory import Faker  # type: ignore[attr-defined]
from factory import post_generation  # type: ignore[attr-defined]
from factory.django import DjangoModelFactory

from manies_maintenance_manager.users.models import User


class UserFactory(DjangoModelFactory):  # type: ignore[type-arg]
    """Factory for generating User model instances."""

    username = Faker("user_name")  # type: ignore[no-untyped-call]
    email = Faker("email")  # type: ignore[no-untyped-call]
    name = Faker("name")  # type: ignore[no-untyped-call]

    # pylint: disable=unused-argument
    # noinspection PyUnusedLocal
    @post_generation  # type: ignore[misc]
    def password(
        self,
        create: bool,  # noqa: FBT001
        extracted: Sequence[str],
        **kwargs: str,
    ) -> None:
        """Generate and set a password for the user.

        Args:
            create (bool): Whether the user is being created.
            extracted (Sequence[str]): Custom password, if provided.
            **kwargs (str): Additional keyword arguments.
        """
        password = (
            extracted
            if extracted
            else Faker(  # type: ignore[no-untyped-call]
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        # pylint: disable=no-member
        self.set_password(password)  # type: ignore[attr-defined]

    # pylint: disable=signature-differs
    @classmethod
    def _after_postgeneration(  # type: ignore[override]
        cls: type["UserFactory"],
        instance: User,
        create: bool,  # noqa: FBT001
        results: dict[str, str | None],
    ) -> None:
        """Ensure instance is saved after post-generation hooks if changes are made.

        Args:
            cls (type["UserFactory"]): The current class.
            instance (User): The user instance being created.
            create (bool): Flag to check if creation is ongoing.
            results (dict[str, str | None]): Post-generation hook results.

        # noqa: DAR102

        """
        # pylint: disable=no-member
        if create and results and not cls._meta.skip_postgeneration_save:  # type: ignore[attr-defined]
            # Some post-generation hooks ran, and may have modified us.
            instance.save()

    class Meta:
        """Meta-options for UserFactory."""

        model = User
        django_get_or_create = ["username"]
