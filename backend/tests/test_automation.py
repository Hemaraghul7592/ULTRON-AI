from datetime import UTC

import pytest

from app.automation.reminders import ReminderEngine
from app.automation.scheduler import SchedulerService
from app.automation.workers import BackgroundWorker


class TestSchedulerService:
    @pytest.mark.asyncio
    async def test_add_job(self):
        scheduler = SchedulerService()

        async def dummy():
            pass

        job = scheduler.add_job("j1", "test_job", dummy, interval_seconds=60)
        assert job.job_id == "j1"
        assert job.name == "test_job"
        assert job.enabled

    @pytest.mark.asyncio
    async def test_remove_job(self):
        scheduler = SchedulerService()

        async def dummy():
            pass

        scheduler.add_job("j1", "test_job", dummy, interval_seconds=60)
        assert scheduler.remove_job("j1")
        assert not scheduler.remove_job("j1")

    @pytest.mark.asyncio
    async def test_pause_resume(self):
        scheduler = SchedulerService()

        async def dummy():
            pass

        scheduler.add_job("j1", "test_job", dummy, interval_seconds=60)
        assert scheduler.pause_job("j1")
        job = scheduler.get_job("j1")
        assert not job.enabled

        assert scheduler.resume_job("j1")
        job = scheduler.get_job("j1")
        assert job.enabled

    def test_get_jobs(self):
        scheduler = SchedulerService()

        async def dummy():
            pass

        scheduler.add_job("j1", "job1", dummy, interval_seconds=60)
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0]["job_id"] == "j1"


class TestReminderEngine:
    @pytest.mark.asyncio
    async def test_add_reminder(self):
        from datetime import datetime, timedelta

        engine = ReminderEngine()
        remind_at = datetime.now(UTC) + timedelta(hours=1)
        reminder = engine.add_reminder("r1", "Test", "Test message", remind_at)
        assert reminder.reminder_id == "r1"

    @pytest.mark.asyncio
    async def test_remove_reminder(self):
        from datetime import datetime, timedelta

        engine = ReminderEngine()
        remind_at = datetime.now(UTC) + timedelta(hours=1)
        engine.add_reminder("r1", "Test", "Test message", remind_at)
        assert engine.remove_reminder("r1")
        assert not engine.remove_reminder("r1")

    @pytest.mark.asyncio
    async def test_check_no_triggered(self):
        from datetime import datetime, timedelta

        engine = ReminderEngine()
        remind_at = datetime.now(UTC) + timedelta(hours=1)
        engine.add_reminder("r1", "Test", "Test message", remind_at)
        triggered = await engine.check_reminders()
        assert len(triggered) == 0

    def test_get_pending(self):
        from datetime import datetime, timedelta

        engine = ReminderEngine()
        remind_at = datetime.now(UTC) + timedelta(hours=1)
        engine.add_reminder("r1", "Test", "Test message", remind_at)
        pending = engine.get_pending()
        assert len(pending) == 1


class TestBackgroundWorker:
    @pytest.mark.asyncio
    async def test_submit_task(self):
        worker = BackgroundWorker(max_concurrent=2)

        async def dummy():
            return "done"

        task_id = worker.submit("test", dummy)
        assert task_id.startswith("task-")

    @pytest.mark.asyncio
    async def test_worker_stats(self):
        worker = BackgroundWorker(max_concurrent=2)
        stats = worker.get_stats()
        assert stats["max_concurrent"] == 2
        assert stats["queue_size"] == 0
