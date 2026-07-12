from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from features.auth.domain.user import User, UserCreate
from features.auth.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
    UsernameAlreadyExistsError,
    UserNotActiveError,
    UserNotFoundError,
)
from features.auth.jwt.models import TokenPayload
from features.auth.services import AuthenticationService, AuthResult, RegistrationData


def build_token_payload(*, sub: str, type_: str = "refresh") -> TokenPayload:
    return TokenPayload(
        sub=sub,
        type=type_,
        exp=datetime.now(UTC),
        iat=datetime.now(UTC),
        jti=str(uuid4()),
        iss="tayari-ai",
        aud="tayari-api",
        roles=[],
        permissions=[],
    )


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_user(user_id: UUID) -> User:
    return User(
        id=user_id,
        email="alice@example.com",
        username="alice",
        display_name="Alice Smith",
        password_hash="$2b$12$hashed",
        email_verified=False,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def registration_data() -> RegistrationData:
    return RegistrationData(
        email="bob@example.com",
        username="bob",
        display_name="Bob Jones",
        password="plain-password",
    )


@pytest.fixture
def mock_repository() -> AsyncMock:
    repo = AsyncMock()
    repo.find_by_email = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.create_user = AsyncMock()
    repo.update_user = AsyncMock()
    repo.exists = AsyncMock()
    return repo


@pytest.fixture
def mock_password_service() -> MagicMock:
    pwd = MagicMock()
    pwd.hash_password = MagicMock(return_value="$2b$12$hashed")
    pwd.verify_password = MagicMock(return_value=True)
    pwd.needs_rehash = MagicMock(return_value=False)
    return pwd


@pytest.fixture
def mock_token_service() -> MagicMock:
    svc = MagicMock()
    svc.create_access_token = MagicMock(return_value="access-token")
    svc.create_refresh_token = MagicMock(return_value="refresh-token")
    svc.create_email_verification_token = MagicMock(return_value="verify-token")
    svc.create_password_reset_token = MagicMock(return_value="reset-token")
    svc.verify = AsyncMock(return_value=build_token_payload(sub=str(uuid4())))
    svc.revoke = AsyncMock()
    return svc


@pytest.fixture
def service(
    mock_repository: AsyncMock,
    mock_password_service: MagicMock,
    mock_token_service: MagicMock,
) -> AuthenticationService:
    return AuthenticationService(
        repository=mock_repository,
        password_service=mock_password_service,
        token_service=mock_token_service,
    )


class TestRegister:
    async def test_creates_user_and_returns_tokens(
        self,
        service: AuthenticationService,
        mock_repository: AsyncMock,
        mock_password_service: MagicMock,
        mock_token_service: MagicMock,
        registration_data: RegistrationData,
        sample_user: User,
    ) -> None:
        mock_repository.exists.return_value = False
        mock_repository.create_user.return_value = sample_user

        result = await service.register(registration_data)

        assert isinstance(result, AuthResult)
        assert result.user == sample_user
        assert result.access_token == "access-token"
        assert result.refresh_token == "refresh-token"

        mock_password_service.hash_password.assert_called_once_with("plain-password")
        mock_repository.exists.assert_any_call(email=registration_data.email)
        mock_repository.exists.assert_any_call(username=registration_data.username)
        mock_repository.create_user.assert_called_once()
        create_call = mock_repository.create_user.call_args[0][0]
        assert isinstance(create_call, UserCreate)
        assert create_call.password_hash == "$2b$12$hashed"
        mock_token_service.create_access_token.assert_called_once_with(sample_user.id, roles=["user"], permissions=[])
        mock_token_service.create_refresh_token.assert_called_once_with(sample_user.id)

    async def test_raises_if_email_exists(
        self,
        service: AuthenticationService,
        mock_repository: AsyncMock,
        registration_data: RegistrationData,
    ) -> None:
        mock_repository.exists.return_value = True

        with pytest.raises(EmailAlreadyExistsError):
            await service.register(registration_data)

    async def test_raises_if_username_exists(
        self,
        service: AuthenticationService,
        mock_repository: AsyncMock,
        registration_data: RegistrationData,
    ) -> None:
        mock_repository.exists.side_effect = [False, True]

        with pytest.raises(UsernameAlreadyExistsError):
            await service.register(registration_data)


class TestLogin:
    async def test_returns_tokens_on_valid_credentials(
        self,
        service: AuthenticationService,
        mock_repository: AsyncMock,
        mock_password_service: MagicMock,
        mock_token_service: MagicMock,
        sample_user: User,
    ) -> None:
        mock_repository.find_by_email.return_value = sample_user
        mock_password_service.verify_password.return_value = True

        result = await service.login("alice@example.com", "correct-password")

        assert isinstance(result, AuthResult)
        assert result.user == sample_user
        assert result.access_token == "access-token"
        assert result.refresh_token == "refresh-token"
        mock_password_service.verify_password.assert_called_once_with("correct-password", sample_user.password_hash)
        mock_token_service.create_access_token.assert_called_once_with(sample_user.id, roles=["user"], permissions=[])
        mock_token_service.create_refresh_token.assert_called_once_with(sample_user.id)

    async def test_raises_if_user_not_found(
        self,
        service: AuthenticationService,
        mock_repository: AsyncMock,
    ) -> None:
        mock_repository.find_by_email.return_value = None

        with pytest.raises(InvalidCredentialsError):
            await service.login("unknown@example.com", "password")

    async def test_raises_if_wrong_password(
        self,
        service: AuthenticationService,
        mock_repository: AsyncMock,
        mock_password_service: MagicMock,
        sample_user: User,
    ) -> None:
        mock_repository.find_by_email.return_value = sample_user
        mock_password_service.verify_password.return_value = False

        with pytest.raises(InvalidCredentialsError):
            await service.login("alice@example.com", "wrong-password")

    async def test_raises_if_user_not_active(
        self,
        service: AuthenticationService,
        mock_repository: AsyncMock,
        mock_password_service: MagicMock,
        sample_user: User,
    ) -> None:
        sample_user.is_active = False
        mock_repository.find_by_email.return_value = sample_user
        mock_password_service.verify_password.return_value = True

        with pytest.raises(UserNotActiveError):
            await service.login("alice@example.com", "correct-password")


class TestRefresh:
    async def test_returns_new_tokens_and_revokes_old(
        self,
        service: AuthenticationService,
        mock_repository: AsyncMock,
        mock_token_service: MagicMock,
        sample_user: User,
    ) -> None:
        token_family = str(uuid4())
        mock_token_service.verify.return_value = build_token_payload(sub=str(sample_user.id), type_="refresh")
        mock_token_service.verify.return_value.token_family = token_family
        mock_repository.find_by_id.return_value = sample_user

        result = await service.refresh("valid-refresh-token")

        assert isinstance(result, AuthResult)
        assert result.user == sample_user
        mock_token_service.verify.assert_called_once_with("valid-refresh-token", "refresh")
        mock_token_service.revoke.assert_awaited_once_with("valid-refresh-token")
        mock_token_service.create_access_token.assert_called_once_with(sample_user.id, roles=[], permissions=[])
        mock_token_service.create_refresh_token.assert_called_once_with(sample_user.id, token_family=token_family)

    async def test_raises_if_token_invalid(
        self,
        service: AuthenticationService,
        mock_token_service: MagicMock,
    ) -> None:
        mock_token_service.verify.side_effect = InvalidTokenError("bad token")

        with pytest.raises(InvalidTokenError):
            await service.refresh("bad-token")

    async def test_raises_if_user_not_found(
        self,
        service: AuthenticationService,
        mock_repository: AsyncMock,
        mock_token_service: MagicMock,
    ) -> None:
        mock_token_service.verify.return_value = build_token_payload(sub=str(uuid4()))
        mock_repository.find_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.refresh("valid-token-missing-user")

    async def test_raises_if_user_deleted(
        self,
        service: AuthenticationService,
        mock_repository: AsyncMock,
        mock_token_service: MagicMock,
        sample_user: User,
    ) -> None:
        sample_user.is_active = False
        sample_user.deleted_at = datetime.now(UTC)
        mock_token_service.verify.return_value = build_token_payload(sub=str(sample_user.id))
        mock_repository.find_by_id.return_value = sample_user

        with pytest.raises(UserNotActiveError):
            await service.refresh("valid-token-deleted-user")


class TestLogout:
    async def test_succeeds_with_valid_token(
        self,
        service: AuthenticationService,
        mock_token_service: MagicMock,
    ) -> None:
        mock_token_service.verify.return_value = build_token_payload(sub=str(uuid4()))

        result = await service.logout("valid-refresh-token")

        assert result is None
        mock_token_service.verify.assert_called_once_with("valid-refresh-token", "refresh")

    async def test_raises_if_token_invalid(
        self,
        service: AuthenticationService,
        mock_token_service: MagicMock,
    ) -> None:
        mock_token_service.verify.side_effect = InvalidTokenError("bad token")

        with pytest.raises(InvalidTokenError):
            await service.logout("bad-token")


class TestVerifyEmail:
    async def test_verifies_email(
        self,
        service: AuthenticationService,
        mock_repository: AsyncMock,
        mock_token_service: MagicMock,
        sample_user: User,
    ) -> None:
        mock_token_service.verify.return_value = build_token_payload(sub=str(sample_user.id), type_="email_verify")
        mock_repository.find_by_id.return_value = sample_user

        result = await service.verify_email("valid-verify-token")

        assert result is None
        mock_token_service.verify.assert_called_once_with("valid-verify-token", "email_verify")
        mock_repository.update_user.assert_called_once()
        args, _ = mock_repository.update_user.call_args
        assert args[0] == sample_user.id
        assert args[1].email_verified is True

    async def test_raises_if_token_invalid(
        self,
        service: AuthenticationService,
        mock_token_service: MagicMock,
    ) -> None:
        mock_token_service.verify.side_effect = InvalidTokenError("bad token")

        with pytest.raises(InvalidTokenError):
            await service.verify_email("bad-token")

    async def test_raises_if_user_not_found(
        self,
        service: AuthenticationService,
        mock_repository: AsyncMock,
        mock_token_service: MagicMock,
    ) -> None:
        mock_token_service.verify.return_value = build_token_payload(sub=str(uuid4()))
        mock_repository.find_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await service.verify_email("valid-token-missing-user")


class TestForgotPassword:
    async def test_does_not_raise_for_existing_user(
        self,
        service: AuthenticationService,
        mock_repository: AsyncMock,
        mock_token_service: MagicMock,
        sample_user: User,
    ) -> None:
        mock_repository.find_by_email.return_value = sample_user

        result = await service.forgot_password("alice@example.com")

        assert result is None
        mock_token_service.create_password_reset_token.assert_called_once_with(sample_user.id)

    async def test_does_not_reveal_if_email_missing(
        self,
        service: AuthenticationService,
        mock_repository: AsyncMock,
        mock_token_service: MagicMock,
    ) -> None:
        mock_repository.find_by_email.return_value = None

        result = await service.forgot_password("nobody@example.com")

        assert result is None
        mock_token_service.create_password_reset_token.assert_not_called()

    async def test_does_not_reveal_if_user_deleted(
        self,
        service: AuthenticationService,
        mock_repository: AsyncMock,
        mock_token_service: MagicMock,
        sample_user: User,
    ) -> None:
        sample_user.deleted_at = datetime.now(UTC)
        mock_repository.find_by_email.return_value = sample_user

        result = await service.forgot_password("alice@example.com")

        assert result is None
        mock_token_service.create_password_reset_token.assert_not_called()
