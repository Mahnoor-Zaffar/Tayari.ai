import uuid
from datetime import UTC, datetime

import pytest

from features.auth.domain.user import User, UserCreate, UserUpdate
from features.auth.repositories import NotFoundError, UserRepository


class TestCreateUser:
    async def test_creates_user(self, repository: UserRepository, user_create: UserCreate) -> None:
        result = await repository.create_user(user_create)

        assert isinstance(result, User)
        assert result.id is not None
        assert isinstance(result.id, uuid.UUID)
        assert result.email == user_create.email
        assert result.username == user_create.username
        assert result.created_at is not None
        assert result.updated_at is not None
        assert result.deleted_at is None
        assert result.email_verified is False
        assert result.is_active is True

    async def test_raises_on_duplicate_email(
        self, repository: UserRepository, existing_user: User, user_create: UserCreate
    ) -> None:
        with pytest.raises(Exception):
            await repository.create_user(user_create)


class TestFindById:
    async def test_returns_user_when_found(self, repository: UserRepository, existing_user: User) -> None:
        result = await repository.find_by_id(existing_user.id)
        assert result is not None
        assert result.id == existing_user.id

    async def test_returns_none_when_not_found(self, repository: UserRepository) -> None:
        result = await repository.find_by_id(uuid.uuid4())
        assert result is None

    async def test_excludes_soft_deleted_by_default(self, repository: UserRepository, existing_user: User) -> None:
        await repository.delete_user(existing_user.id)
        result = await repository.find_by_id(existing_user.id)
        assert result is None

    async def test_includes_soft_deleted_with_flag(self, repository: UserRepository, existing_user: User) -> None:
        await repository.delete_user(existing_user.id)
        result = await repository.find_by_id(existing_user.id, include_deleted=True)
        assert result is not None
        assert result.deleted_at is not None


class TestFindByEmail:
    async def test_returns_user_when_found(self, repository: UserRepository, existing_user: User) -> None:
        result = await repository.find_by_email(existing_user.email)
        assert result is not None
        assert result.id == existing_user.id

    async def test_returns_none_when_not_found(self, repository: UserRepository) -> None:
        result = await repository.find_by_email("nobody@example.com")
        assert result is None

    async def test_excludes_soft_deleted(self, repository: UserRepository, existing_user: User) -> None:
        await repository.delete_user(existing_user.id)
        result = await repository.find_by_email(existing_user.email)
        assert result is None

    async def test_case_sensitive_match(self, repository: UserRepository, existing_user: User) -> None:
        result = await repository.find_by_email(existing_user.email.upper())
        assert result is None


class TestUpdateUser:
    async def test_updates_display_name(self, repository: UserRepository, existing_user: User) -> None:
        result = await repository.update_user(existing_user.id, UserUpdate(display_name="Updated Name"))
        assert result.display_name == "Updated Name"

    async def test_updates_updated_at(self, repository: UserRepository, existing_user: User) -> None:
        original = existing_user.updated_at
        result = await repository.update_user(existing_user.id, UserUpdate(display_name="Updated Name"))
        assert result.updated_at > original

    async def test_raises_when_user_not_found(self, repository: UserRepository) -> None:
        with pytest.raises(NotFoundError):
            await repository.update_user(uuid.uuid4(), UserUpdate(display_name="Nope"))


class TestDeleteUser:
    async def test_sets_deleted_at(self, repository: UserRepository, existing_user: User) -> None:
        before = datetime.now(UTC)
        await repository.delete_user(existing_user.id)
        after = datetime.now(UTC)

        result = await repository.find_by_id(existing_user.id, include_deleted=True)
        assert result is not None
        assert result.deleted_at is not None
        assert before <= result.deleted_at.replace(tzinfo=UTC) <= after

    async def test_sets_is_active_false(self, repository: UserRepository, existing_user: User) -> None:
        await repository.delete_user(existing_user.id)
        result = await repository.find_by_id(existing_user.id, include_deleted=True)
        assert result is not None
        assert result.is_active is False

    async def test_is_idempotent(self, repository: UserRepository, existing_user: User) -> None:
        await repository.delete_user(existing_user.id)
        await repository.delete_user(existing_user.id)


class TestExists:
    async def test_by_email_returns_true(self, repository: UserRepository, existing_user: User) -> None:
        assert await repository.exists(email=existing_user.email) is True

    async def test_by_email_returns_false(self, repository: UserRepository) -> None:
        assert await repository.exists(email="nobody@example.com") is False

    async def test_by_email_excludes_deleted(self, repository: UserRepository, existing_user: User) -> None:
        await repository.delete_user(existing_user.id)
        assert await repository.exists(email=existing_user.email) is False

    async def test_by_username_returns_true(self, repository: UserRepository, existing_user: User) -> None:
        assert await repository.exists(username=existing_user.username) is True

    async def test_by_username_returns_false(self, repository: UserRepository) -> None:
        assert await repository.exists(username="nobody") is False

    async def test_by_username_excludes_deleted(self, repository: UserRepository, existing_user: User) -> None:
        await repository.delete_user(existing_user.id)
        assert await repository.exists(username=existing_user.username) is False
