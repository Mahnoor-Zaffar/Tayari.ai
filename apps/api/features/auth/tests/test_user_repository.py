import uuid
from datetime import UTC, datetime

import pytest

from features.auth.models import User
from features.auth.repositories import UserRepository


class TestCreate:
    async def test_creates_user(self, repository: UserRepository, user_kwargs: dict) -> None:
        user = User(**user_kwargs)
        result = await repository.create(user)

        assert result.id is not None
        assert isinstance(result.id, uuid.UUID)
        assert result.email == user_kwargs["email"]
        assert result.username == user_kwargs["username"]
        assert result.created_at is not None
        assert result.updated_at is not None
        assert result.deleted_at is None
        assert result.email_verified is False
        assert result.is_active is True

    async def test_raises_on_duplicate_email(
        self, repository: UserRepository, existing_user: User, user_kwargs: dict
    ) -> None:
        dup = User(**user_kwargs)
        with pytest.raises(Exception):  # IntegrityError from SQLite
            await repository.create(dup)


class TestGetById:
    async def test_returns_user_when_found(self, repository: UserRepository, existing_user: User) -> None:
        result = await repository.get_by_id(existing_user.id)
        assert result is not None
        assert result.id == existing_user.id

    async def test_returns_none_when_not_found(self, repository: UserRepository) -> None:
        result = await repository.get_by_id(uuid.uuid4())
        assert result is None

    async def test_excludes_soft_deleted_by_default(self, repository: UserRepository, existing_user: User) -> None:
        await repository.soft_delete(existing_user)
        result = await repository.get_by_id(existing_user.id)
        assert result is None

    async def test_includes_soft_deleted_with_flag(self, repository: UserRepository, existing_user: User) -> None:
        await repository.soft_delete(existing_user)
        result = await repository.get_by_id(existing_user.id, include_deleted=True)
        assert result is not None
        assert result.deleted_at is not None


class TestGetByEmail:
    async def test_returns_user_when_found(self, repository: UserRepository, existing_user: User) -> None:
        result = await repository.get_by_email(existing_user.email)
        assert result is not None
        assert result.id == existing_user.id

    async def test_returns_none_when_not_found(self, repository: UserRepository) -> None:
        result = await repository.get_by_email("nobody@example.com")
        assert result is None

    async def test_excludes_soft_deleted(self, repository: UserRepository, existing_user: User) -> None:
        await repository.soft_delete(existing_user)
        result = await repository.get_by_email(existing_user.email)
        assert result is None

    async def test_case_sensitive_match(self, repository: UserRepository, existing_user: User) -> None:
        result = await repository.get_by_email(existing_user.email.upper())
        assert result is None


class TestGetByUsername:
    async def test_returns_user_when_found(self, repository: UserRepository, existing_user: User) -> None:
        result = await repository.get_by_username(existing_user.username)
        assert result is not None
        assert result.id == existing_user.id

    async def test_returns_none_when_not_found(self, repository: UserRepository) -> None:
        result = await repository.get_by_username("nobody")
        assert result is None

    async def test_excludes_soft_deleted(self, repository: UserRepository, existing_user: User) -> None:
        await repository.soft_delete(existing_user)
        result = await repository.get_by_username(existing_user.username)
        assert result is None


class TestListActive:
    async def test_returns_active_users(self, repository: UserRepository, existing_user: User) -> None:
        result = await repository.list_active()
        assert len(result) >= 1
        assert existing_user in result

    async def test_excludes_inactive_users(self, repository: UserRepository, existing_user: User) -> None:
        existing_user.is_active = False
        await repository.save(existing_user)
        result = await repository.list_active()
        assert existing_user not in result

    async def test_excludes_soft_deleted_users(self, repository: UserRepository, existing_user: User) -> None:
        await repository.soft_delete(existing_user)
        result = await repository.list_active()
        assert existing_user not in result

    async def test_respects_offset_and_limit(self, repository: UserRepository, user_kwargs: dict) -> None:
        for i in range(5):
            kw = dict(user_kwargs)
            kw["email"] = f"user{i}@example.com"
            kw["username"] = f"user{i}"
            await repository.create(User(**kw))

        result = await repository.list_active(offset=0, limit=3)
        assert len(result) == 3

        result = await repository.list_active(offset=3, limit=10)
        assert len(result) == 2


class TestSoftDelete:
    async def test_sets_deleted_at(self, repository: UserRepository, existing_user: User) -> None:
        before = datetime.now(UTC)
        result = await repository.soft_delete(existing_user)
        after = datetime.now(UTC)

        assert result.deleted_at is not None
        deleted_at = result.deleted_at.replace(tzinfo=UTC) if result.deleted_at.tzinfo is None else result.deleted_at
        assert before <= deleted_at <= after

    async def test_sets_is_active_false(self, repository: UserRepository, existing_user: User) -> None:
        result = await repository.soft_delete(existing_user)
        assert result.is_active is False


class TestExists:
    async def test_exists_by_email_returns_true(self, repository: UserRepository, existing_user: User) -> None:
        assert await repository.exists_by_email(existing_user.email) is True

    async def test_exists_by_email_returns_false(self, repository: UserRepository) -> None:
        assert await repository.exists_by_email("nobody@example.com") is False

    async def test_exists_by_email_excludes_deleted(self, repository: UserRepository, existing_user: User) -> None:
        await repository.soft_delete(existing_user)
        assert await repository.exists_by_email(existing_user.email) is False

    async def test_exists_by_username_returns_true(self, repository: UserRepository, existing_user: User) -> None:
        assert await repository.exists_by_username(existing_user.username) is True

    async def test_exists_by_username_returns_false(self, repository: UserRepository) -> None:
        assert await repository.exists_by_username("nobody") is False

    async def test_exists_by_username_excludes_deleted(self, repository: UserRepository, existing_user: User) -> None:
        await repository.soft_delete(existing_user)
        assert await repository.exists_by_username(existing_user.username) is False


class TestSave:
    async def test_persists_field_changes(self, repository: UserRepository, existing_user: User) -> None:
        existing_user.display_name = "Updated Name"
        result = await repository.save(existing_user)
        assert result.display_name == "Updated Name"

    async def test_updates_updated_at(self, repository: UserRepository, existing_user: User) -> None:
        original = existing_user.updated_at
        original_aware = original.replace(tzinfo=UTC) if original.tzinfo is None else original
        existing_user.display_name = "Updated Name"
        result = await repository.save(existing_user)
        result_aware = result.updated_at.replace(tzinfo=UTC) if result.updated_at.tzinfo is None else result.updated_at
        assert result_aware > original_aware


class TestCountActive:
    async def test_returns_zero_when_none_active(self, repository: UserRepository) -> None:
        assert await repository.count_active() == 0

    async def test_counts_only_active_users(self, repository: UserRepository, existing_user: User) -> None:
        assert await repository.count_active() == 1

    async def test_excludes_inactive(self, repository: UserRepository, existing_user: User) -> None:
        existing_user.is_active = False
        await repository.save(existing_user)
        assert await repository.count_active() == 0

    async def test_excludes_soft_deleted(self, repository: UserRepository, existing_user: User) -> None:
        await repository.soft_delete(existing_user)
        assert await repository.count_active() == 0
