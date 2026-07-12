import bcrypt
import pytest

from features.auth.password.service import PasswordService


@pytest.fixture
def service() -> PasswordService:
    return PasswordService(rounds=12)


@pytest.fixture
def alt_service() -> PasswordService:
    """A service with a different work factor for needs_rehash tests."""
    return PasswordService(rounds=10)


class TestHashPassword:
    def test_returns_string(self, service: PasswordService) -> None:
        hashed = service.hash_password("my-secret-password")

        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_returns_different_hashes_for_same_password(self, service: PasswordService) -> None:
        h1 = service.hash_password("same-password")
        h2 = service.hash_password("same-password")

        assert h1 != h2

    def test_hash_contains_work_factor(self, service: PasswordService) -> None:
        hashed = service.hash_password("test")

        parts = hashed.split("$")
        assert parts[1] in ("2a", "2b", "2y")
        assert parts[2] == "12"

    def test_never_exposes_raw_bytes(self, service: PasswordService) -> None:
        hashed = service.hash_password("test")

        assert isinstance(hashed, str)
        # bcrypt output is always ASCII-safe base64
        hashed.encode("ascii")


class TestVerifyPassword:
    def test_returns_true_for_correct_password(self, service: PasswordService) -> None:
        hashed = service.hash_password("correct-horse-battery-staple")

        assert service.verify_password("correct-horse-battery-staple", hashed) is True

    def test_returns_false_for_wrong_password(self, service: PasswordService) -> None:
        hashed = service.hash_password("real-password")

        assert service.verify_password("wrong-password", hashed) is False

    def test_returns_false_for_garbage_hash(self, service: PasswordService) -> None:
        assert service.verify_password("anything", "not-a-valid-hash") is False

    def test_returns_false_for_empty_hash(self, service: PasswordService) -> None:
        assert service.verify_password("password", "") is False

    def test_verify_with_hash_from_different_factor(
        self, service: PasswordService, alt_service: PasswordService
    ) -> None:
        hashed = alt_service.hash_password("cross-version")

        assert service.verify_password("cross-version", hashed) is True


class TestNeedsRehash:
    def test_returns_false_for_current_parameters(self, service: PasswordService) -> None:
        hashed = service.hash_password("test")

        assert service.needs_rehash(hashed) is False

    def test_returns_true_for_different_work_factor(
        self, service: PasswordService, alt_service: PasswordService
    ) -> None:
        hashed = alt_service.hash_password("test")

        assert service.needs_rehash(hashed) is True

    def test_returns_true_for_invalid_hash(self, service: PasswordService) -> None:
        assert service.needs_rehash("not-a-hash") is True

    def test_returns_true_for_empty_string(self, service: PasswordService) -> None:
        assert service.needs_rehash("") is True

    def test_returns_true_for_unsupported_prefix(self, service: PasswordService) -> None:
        # $2x$ is not a standard bcrypt prefix
        bogus = "$2x$08$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ12"
        assert service.needs_rehash(bogus) is True

    def test_upgrade_flow(self, service: PasswordService, alt_service: PasswordService) -> None:
        password = "upgrade-me"
        old_hash = alt_service.hash_password(password)

        assert alt_service.needs_rehash(old_hash) is False
        assert service.needs_rehash(old_hash) is True

        new_hash = service.hash_password(password)
        assert service.verify_password(password, new_hash) is True
        assert service.needs_rehash(new_hash) is False


class TestBcryptCompatibility:
    """Verify our PasswordService produces hashes that bcrypt itself accepts."""

    def test_hash_compatible_with_bcrypt_library(self, service: PasswordService) -> None:
        hashed = service.hash_password("interop-test")

        assert bcrypt.checkpw(b"interop-test", hashed.encode("utf-8")) is True

    def test_verify_accepts_bcrypt_generated_hash(self, service: PasswordService) -> None:
        hashed = bcrypt.hashpw(b"bcrypt-test", bcrypt.gensalt(rounds=12)).decode("utf-8")

        assert service.verify_password("bcrypt-test", hashed) is True
