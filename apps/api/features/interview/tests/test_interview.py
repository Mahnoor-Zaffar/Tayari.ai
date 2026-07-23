"""Tests for the interview feature.

Three test layers mirroring the module structure:
1. Repository integration tests (real SQLite)
2. Service unit tests (mocked repository)
3. API integration tests (httpx + dependency overrides)
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from features.auth.guard import CurrentUser, get_current_user
from features.interview.dependencies import get_interview_service
from features.interview.repository import InterviewRepository
from features.interview.schemas import (
    CreateInterviewRequest,
    DeviceCheckRequest,
    InterviewResponse,
)
from features.interview.service import InterviewService
from main import app

# ── Helpers ────────────────────────────────────────────────────────────────


def _make_user() -> CurrentUser:
    return CurrentUser(
        id=uuid.uuid4(),
        email="test@example.com",
        username="testuser",
        display_name="Test User",
        email_verified=True,
        is_active=True,
        roles=["user"],
        permissions=[],
    )


def _make_create_request(**overrides) -> CreateInterviewRequest:
    defaults = {
        "type": "coding",
        "company": "Google",
        "role": "Software Engineer",
        "experience_level": "mid-senior",
        "language": "python",
        "difficulty": "medium",
        "duration_minutes": 30,
    }
    defaults.update(overrides)
    return CreateInterviewRequest(**defaults)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Repository Integration Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestInterviewRepository:
    async def test_create_and_get_interview(self, repository: InterviewRepository, seeded_user_id: uuid.UUID) -> None:
        interview = await repository.create_interview(
            {
                "user_id": seeded_user_id,
                "type": "coding",
                "company": "Google",
                "role": "Software Engineer",
                "experience_level": "mid-senior",
                "language": "python",
                "difficulty": "medium",
                "duration_minutes": 30,
                "timer_remaining": 1800,
                "status": "pending",
            }
        )
        assert interview.id is not None
        assert interview.company == "Google"

        fetched = await repository.get_interview_by_id(interview.id, seeded_user_id)
        assert fetched is not None
        assert fetched.company == "Google"

    async def test_get_interview_wrong_user_returns_none(
        self, repository: InterviewRepository, seeded_user_id: uuid.UUID
    ) -> None:
        interview = await repository.create_interview(
            {
                "user_id": seeded_user_id,
                "type": "coding",
                "company": "Meta",
                "role": "Engineer",
                "experience_level": "junior",
                "language": "java",
                "difficulty": "easy",
                "duration_minutes": 15,
                "timer_remaining": 900,
                "status": "pending",
            }
        )
        other_user = uuid.uuid4()
        fetched = await repository.get_interview_by_id(interview.id, other_user)
        assert fetched is None

    async def test_list_interviews(self, repository: InterviewRepository, seeded_user_id: uuid.UUID) -> None:
        for i in range(3):
            await repository.create_interview(
                {
                    "user_id": seeded_user_id,
                    "type": "coding",
                    "company": f"Company{i}",
                    "role": "Engineer",
                    "experience_level": "junior",
                    "language": "python",
                    "difficulty": "medium",
                    "duration_minutes": 30,
                    "timer_remaining": 1800,
                    "status": "pending",
                }
            )
        interviews = await repository.list_interviews(seeded_user_id)
        assert len(interviews) == 3

    async def test_count_user_interviews(self, repository: InterviewRepository, seeded_user_id: uuid.UUID) -> None:
        assert await repository.count_user_interviews(seeded_user_id) == 0
        await repository.create_interview(
            {
                "user_id": seeded_user_id,
                "type": "coding",
                "company": "Google",
                "role": "Engineer",
                "experience_level": "junior",
                "language": "python",
                "difficulty": "medium",
                "duration_minutes": 30,
                "timer_remaining": 1800,
                "status": "pending",
            }
        )
        assert await repository.count_user_interviews(seeded_user_id) == 1

    async def test_create_and_find_resume_by_hash(
        self, repository: InterviewRepository, seeded_user_id: uuid.UUID
    ) -> None:
        resume = await repository.create_resume(
            {
                "user_id": seeded_user_id,
                "original_filename": "resume.pdf",
                "mime_type": "application/pdf",
                "file_size": 102400,
                "storage_path": f"uploads/{seeded_user_id}/resumes/abc123",
                "file_hash": "a" * 64,
            }
        )
        assert resume.id is not None

        found = await repository.find_resume_by_hash(seeded_user_id, "a" * 64)
        assert found is not None
        assert found.original_filename == "resume.pdf"

    async def test_find_resume_by_hash_not_found(
        self, repository: InterviewRepository, seeded_user_id: uuid.UUID
    ) -> None:
        found = await repository.find_resume_by_hash(seeded_user_id, "nonexistent")
        assert found is None

    async def test_create_and_find_job_description_by_hash(
        self, repository: InterviewRepository, seeded_user_id: uuid.UUID
    ) -> None:
        jd = await repository.create_job_description(
            {
                "user_id": seeded_user_id,
                "source": "text",
                "raw_content": "Looking for a Python engineer",
                "mime_type": "text/plain",
                "file_hash": "b" * 64,
            }
        )
        assert jd.id is not None

        found = await repository.find_job_description_by_hash(seeded_user_id, "b" * 64)
        assert found is not None
        assert found.raw_content == "Looking for a Python engineer"

    async def test_create_configuration(self, repository: InterviewRepository, seeded_user_id: uuid.UUID) -> None:
        config = await repository.create_configuration(
            {
                "user_id": seeded_user_id,
                "interview_type": "coding",
                "company": "Google",
                "role": "Engineer",
                "experience_level": "mid-senior",
                "language": "python",
                "difficulty": "medium",
                "duration_minutes": 30,
            }
        )
        assert config.id is not None
        assert config.interview_type == "coding"


# ═══════════════════════════════════════════════════════════════════════════
# 2. Service Unit Tests (mocked repository)
# ═══════════════════════════════════════════════════════════════════════════


class TestInterviewService:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        repo = MagicMock()
        repo.create_interview = AsyncMock()
        repo.create_configuration = AsyncMock()
        repo.count_user_interviews = AsyncMock(return_value=0)
        repo.list_active_templates = AsyncMock(return_value=[])
        repo.find_resume_by_hash = AsyncMock(return_value=None)
        repo.create_resume = AsyncMock()
        repo.find_job_description_by_hash = AsyncMock(return_value=None)
        repo.create_job_description = AsyncMock()
        repo.get_resume_by_id = AsyncMock(return_value=None)
        repo.get_job_description_by_id = AsyncMock(return_value=None)
        repo.list_interviews = AsyncMock(return_value=[])
        repo.get_interview_by_id = AsyncMock(return_value=None)
        repo.find_pending_duplicate = AsyncMock(return_value=None)
        return repo

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> InterviewService:
        return InterviewService(mock_repo)

    async def test_create_interview_success(self, service: InterviewService, mock_repo: MagicMock) -> None:
        mock_repo.create_configuration.return_value = MagicMock(id=uuid.uuid4())
        mock_repo.create_interview.return_value = MagicMock(
            id=uuid.uuid4(),
            type="coding",
            company="Google",
            role="Engineer",
            experience_level="mid-senior",
            language="python",
            framework=None,
            difficulty="medium",
            duration_minutes=30,
            custom_instructions=None,
            spoken_language="en",
            system_design_problem=None,
            status="pending",
            timer_remaining=1800,
            resume_id=None,
            job_description_id=None,
            template_id=None,
            created_at=datetime.now(UTC),
        )

        result = await service.create_interview(uuid.uuid4(), _make_create_request())
        assert isinstance(result, InterviewResponse)
        assert result.company == "Google"
        mock_repo.create_configuration.assert_called_once()
        mock_repo.create_interview.assert_called_once()

    async def test_create_interview_free_tier_limit(self, service: InterviewService, mock_repo: MagicMock) -> None:
        mock_repo.count_user_interviews.return_value = 10

        from core.errors import ConflictError

        with pytest.raises(ConflictError):
            await service.create_interview(uuid.uuid4(), _make_create_request())

    async def test_create_interview_coding_requires_language(
        self, service: InterviewService, mock_repo: MagicMock
    ) -> None:
        with pytest.raises(ValueError, match="language is required"):
            _make_create_request(type="coding", language=None)

    async def test_get_options_returns_all_lists(self, service: InterviewService) -> None:
        result = await service.get_options()
        assert len(result.interview_types) == 3
        assert len(result.languages) == 5
        assert len(result.experience_levels) == 3
        assert len(result.difficulties) == 3
        assert len(result.durations) == 3
        assert len(result.frameworks) == 9

    async def test_upload_resume_dedup(self, service: InterviewService, mock_repo: MagicMock) -> None:
        existing = MagicMock(
            id=uuid.uuid4(),
            original_filename="resume.pdf",
            mime_type="application/pdf",
            file_size=1024,
            file_hash="a" * 64,
            created_at=datetime.now(UTC),
        )
        mock_repo.find_resume_by_hash.return_value = existing

        result = await service.upload_resume(
            uuid.uuid4(),
            MagicMock(
                original_filename="resume.pdf",
                mime_type="application/pdf",
                file_size=1024,
                file_hash="a" * 64,
            ),
        )
        assert result.id == existing.id
        mock_repo.create_resume.assert_not_called()

    async def test_upload_resume_invalid_mime(self, service: InterviewService, mock_repo: MagicMock) -> None:
        from core.errors import ValidationError

        with pytest.raises(ValidationError):
            await service.upload_resume(
                uuid.uuid4(),
                MagicMock(
                    original_filename="resume.exe",
                    mime_type="application/octet-stream",
                    file_size=1024,
                    file_hash="a" * 64,
                ),
            )

    async def test_upload_jd_text(self, service: InterviewService, mock_repo: MagicMock) -> None:
        mock_repo.create_job_description.return_value = MagicMock(
            id=uuid.uuid4(),
            source="text",
            original_filename="",
            created_at=datetime.now(UTC),
        )

        result = await service.upload_job_description(
            uuid.uuid4(),
            MagicMock(
                source="text",
                raw_text="Looking for a Python dev",
                file_hash=None,
                mime_type=None,
                file_size=None,
                original_filename=None,
            ),
        )
        assert result.source == "text"
        mock_repo.create_job_description.assert_called_once()

    async def test_device_check_all_passed(self, service: InterviewService) -> None:
        result = await service.device_check(
            DeviceCheckRequest(microphone=True, camera=True, speaker=True, browser=True),
        )
        assert result.all_passed is True

    async def test_device_check_missing_mic_fails(self, service: InterviewService) -> None:
        result = await service.device_check(
            DeviceCheckRequest(microphone=False, camera=True, speaker=True, browser=True),
        )
        assert result.all_passed is False

    async def test_device_check_missing_camera_still_passes(self, service: InterviewService) -> None:
        result = await service.device_check(
            DeviceCheckRequest(microphone=True, camera=False, speaker=True, browser=True),
        )
        assert result.all_passed is True


# ═══════════════════════════════════════════════════════════════════════════
# 3. API Integration Tests
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def current_user() -> CurrentUser:
    return _make_user()


@pytest.fixture
def mock_service() -> MagicMock:
    svc = MagicMock()
    svc.create_interview = AsyncMock(
        return_value=InterviewResponse(
            id=uuid.uuid4(),
            type="coding",
            company="Google",
            role="Engineer",
            experience_level="mid-senior",
            language="python",
            framework=None,
            difficulty="medium",
            duration_minutes=30,
            custom_instructions=None,
            status="pending",
            timer_remaining=1800,
            resume_id=None,
            job_description_id=None,
            template_id=None,
            created_at=datetime.now(UTC),
        )
    )
    svc.get_options = AsyncMock(
        return_value=MagicMock(
            model_dump=MagicMock(
                return_value={
                    "interview_types": [{"value": "coding", "label": "Coding"}],
                    "companies": ["Google"],
                    "roles": ["Engineer"],
                    "languages": [{"value": "python", "label": "Python"}],
                    "frameworks": [{"value": "react", "label": "React"}],
                    "experience_levels": [{"value": "junior", "label": "Junior"}],
                    "difficulties": [{"value": "easy", "label": "Easy"}],
                    "durations": [{"value": 30, "label": "30 minutes"}],
                }
            )
        )
    )
    svc.upload_resume = AsyncMock(
        return_value=MagicMock(
            model_dump=MagicMock(
                return_value={
                    "id": str(uuid.uuid4()),
                    "original_filename": "resume.pdf",
                    "mime_type": "application/pdf",
                    "file_size": 1024,
                    "file_hash": "a" * 64,
                    "created_at": None,
                }
            )
        )
    )
    svc.upload_job_description = AsyncMock(
        return_value=MagicMock(
            model_dump=MagicMock(
                return_value={
                    "id": str(uuid.uuid4()),
                    "source": "text",
                    "original_filename": "",
                    "created_at": None,
                }
            )
        )
    )
    svc.device_check = AsyncMock(
        return_value=MagicMock(
            model_dump=MagicMock(
                return_value={
                    "microphone": True,
                    "camera": True,
                    "speaker": True,
                    "browser": True,
                    "all_passed": True,
                }
            )
        )
    )
    svc.list_interviews = AsyncMock(return_value=[])
    svc.get_interview = AsyncMock(
        return_value=InterviewResponse(
            id=uuid.uuid4(),
            type="coding",
            company="Google",
            role="Engineer",
            experience_level="mid-senior",
            language="python",
            framework=None,
            difficulty="medium",
            duration_minutes=30,
            custom_instructions=None,
            status="pending",
            timer_remaining=1800,
            resume_id=None,
            job_description_id=None,
            template_id=None,
            created_at=datetime.now(UTC),
        )
    )
    return svc


@pytest.fixture
def client(
    mock_service: MagicMock,
    current_user: CurrentUser,
) -> AsyncGenerator[AsyncClient]:
    app.dependency_overrides[get_interview_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: current_user
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test/api/v1")
    yield client
    app.dependency_overrides.clear()


class TestInterviewAPI:
    async def test_create_interview_returns_201(self, client: AsyncClient) -> None:
        response = await client.post(
            "/interviews",
            json={
                "type": "coding",
                "company": "Google",
                "role": "Engineer",
                "experience_level": "mid-senior",
                "language": "python",
                "difficulty": "medium",
                "duration_minutes": 30,
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["data"]["company"] == "Google"

    async def test_create_interview_missing_language_returns_422(self, client: AsyncClient) -> None:
        response = await client.post(
            "/interviews",
            json={
                "type": "coding",
                "company": "Google",
                "role": "Engineer",
                "experience_level": "mid-senior",
                "language": None,
                "difficulty": "medium",
                "duration_minutes": 30,
            },
        )
        assert response.status_code == 422

    async def test_get_options_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/interviews/options")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "interview_types" in body["data"]
        assert "companies" in body["data"]

    async def test_upload_resume_returns_201(self, client: AsyncClient) -> None:
        response = await client.post(
            "/interviews/upload-resume",
            json={
                "original_filename": "resume.pdf",
                "mime_type": "application/pdf",
                "file_size": 1024,
                "file_hash": "a" * 64,
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["data"]["original_filename"] == "resume.pdf"

    async def test_upload_resume_invalid_mime_returns_422(self, client: AsyncClient) -> None:
        response = await client.post(
            "/interviews/upload-resume",
            json={
                "original_filename": "resume.exe",
                "mime_type": "application/octet-stream",
                "file_size": 1024,
                "file_hash": "a" * 64,
            },
        )
        assert response.status_code == 422

    async def test_upload_jd_text_returns_201(self, client: AsyncClient) -> None:
        response = await client.post(
            "/interviews/upload-job-description",
            json={
                "source": "text",
                "raw_text": "Looking for a senior Python engineer with FastAPI experience.",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["data"]["source"] == "text"

    async def test_device_check_returns_200(self, client: AsyncClient) -> None:
        response = await client.post(
            "/interviews/device-check",
            json={
                "microphone": True,
                "camera": True,
                "speaker": True,
                "browser": True,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["all_passed"] is True

    async def test_list_interviews_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/interviews")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "interviews" in body["data"]

    async def test_get_interview_returns_200(self, client: AsyncClient, mock_service: MagicMock) -> None:
        response = await client.get(f"/interviews/{uuid.uuid4()}")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True

    async def test_endpoints_require_auth(self, mock_service: MagicMock) -> None:
        app.dependency_overrides[get_interview_service] = lambda: mock_service
        app.dependency_overrides.pop(get_current_user, None)
        transport = ASGITransport(app=app)
        unauth_client = AsyncClient(transport=transport, base_url="http://test/api/v1")
        response = await unauth_client.get("/interviews/options")
        assert response.status_code == 401
