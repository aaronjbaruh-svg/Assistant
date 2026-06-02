from datetime import datetime, timedelta, timezone
from typing import Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

FOLLOWUP_DAYS = [1, 2, 4, 7]


class Scheduler:
    def __init__(self, jobs_db_url: str):
        jobstores = {"default": SQLAlchemyJobStore(url=jobs_db_url)}
        self._scheduler = BackgroundScheduler(jobstores=jobstores)

    def start(self):
        self._scheduler.start()

    def shutdown(self):
        self._scheduler.shutdown(wait=False)

    def schedule_followups(
        self,
        lead_id: str,
        fn: Callable,
        fn_kwargs: dict,
    ) -> None:
        now = datetime.now(timezone.utc)
        for i, days in enumerate(FOLLOWUP_DAYS, start=1):
            run_at = now + timedelta(days=days)
            job_id = f"followup_{lead_id}_{i}"
            self._scheduler.add_job(
                fn,
                trigger="date",
                run_date=run_at,
                id=job_id,
                kwargs={**fn_kwargs, "followup_stage": i},
                replace_existing=True,
            )

    def cancel_followups(self, lead_id: str) -> None:
        for i in range(1, len(FOLLOWUP_DAYS) + 1):
            job_id = f"followup_{lead_id}_{i}"
            if self._scheduler.get_job(job_id):
                self._scheduler.remove_job(job_id)

    def get_jobs_for_lead(self, lead_id: str) -> list:
        prefix = f"followup_{lead_id}_"
        return [j for j in self._scheduler.get_jobs() if j.id.startswith(prefix)]
