import pytest
from unittest.mock import MagicMock
from app.scheduler import Scheduler


@pytest.fixture
def scheduler():
    sched = Scheduler(jobs_db_url="sqlite:///:memory:")
    sched.start()
    yield sched
    sched.shutdown()


def test_schedule_followups_creates_four_jobs(scheduler):
    mock_fn = MagicMock()
    scheduler.schedule_followups(
        lead_id="opp_001",
        fn=mock_fn,
        fn_kwargs={"lead_id": "opp_001"},
    )
    jobs = scheduler.get_jobs_for_lead("opp_001")
    assert len(jobs) == 4


def test_cancel_followups_removes_all_jobs(scheduler):
    mock_fn = MagicMock()
    scheduler.schedule_followups(
        lead_id="opp_001",
        fn=mock_fn,
        fn_kwargs={"lead_id": "opp_001"},
    )
    scheduler.cancel_followups("opp_001")
    jobs = scheduler.get_jobs_for_lead("opp_001")
    assert len(jobs) == 0
