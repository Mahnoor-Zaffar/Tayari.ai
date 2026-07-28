"""Tests for the APScheduler-backed background worker."""

from unittest.mock import MagicMock, patch

import pytest


class TestScheduleEvaluation:
    @pytest.mark.asyncio
    async def test_adds_job_with_correct_id(self):
        mock_scheduler = MagicMock()
        mock_scheduler.get_job = MagicMock(return_value=None)
        mock_scheduler.add_job = MagicMock()

        with patch("workers.scheduler.scheduler", mock_scheduler):
            from workers.scheduler import schedule_evaluation

            await schedule_evaluation(
                interview_id="550e8400-e29b-41d4-a716-446655440000",
                user_id="660e8400-e29b-41d4-a716-446655440001",
            )

            mock_scheduler.add_job.assert_called_once()
            call_kwargs = mock_scheduler.add_job.call_args.kwargs
            assert call_kwargs["id"] == "evaluate_550e8400-e29b-41d4-a716-446655440000"
            assert call_kwargs["kwargs"]["interview_id"] == "550e8400-e29b-41d4-a716-446655440000"
            assert call_kwargs["kwargs"]["user_id"] == "660e8400-e29b-41d4-a716-446655440001"
            assert call_kwargs["replace_existing"] is True

    @pytest.mark.asyncio
    async def test_removes_existing_job_before_adding(self):
        mock_scheduler = MagicMock()
        mock_scheduler.get_job = MagicMock(return_value="existing-job")
        mock_scheduler.remove_job = MagicMock()
        mock_scheduler.add_job = MagicMock()

        with patch("workers.scheduler.scheduler", mock_scheduler):
            from workers.scheduler import schedule_evaluation

            await schedule_evaluation(
                interview_id="550e8400-e29b-41d4-a716-446655440000",
                user_id="660e8400-e29b-41d4-a716-446655440001",
            )

            mock_scheduler.remove_job.assert_called_once_with("evaluate_550e8400-e29b-41d4-a716-446655440000")
            mock_scheduler.add_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_points_to_correct_worker_function(self):
        mock_scheduler = MagicMock()
        mock_scheduler.get_job = MagicMock(return_value=None)
        mock_scheduler.add_job = MagicMock()

        with patch("workers.scheduler.scheduler", mock_scheduler):
            from workers.scheduler import schedule_evaluation

            await schedule_evaluation(
                interview_id="550e8400-e29b-41d4-a716-446655440000",
                user_id="660e8400-e29b-41d4-a716-446655440001",
            )

            call_args = mock_scheduler.add_job.call_args
            assert call_args[0][0] == "workers.evaluation:generate_evaluation"


class TestSchedulerConfig:
    def test_job_defaults(self):
        from workers.scheduler import job_defaults

        assert job_defaults["coalesce"] is True
        assert job_defaults["max_instances"] == 3
        assert job_defaults["misfire_grace_time"] == 300

    def test_sync_db_url_derived(self):
        from workers.scheduler import _SYNC_DB_URL

        assert "+asyncpg" not in _SYNC_DB_URL
