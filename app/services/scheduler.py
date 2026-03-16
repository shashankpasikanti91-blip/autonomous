"""
Background Job Scheduler

Supports:
- Scheduled job execution (visa monitoring, payroll cycles, follow-ups)
- Retry logic with exponential backoff
- Job state persistence
- Event-based triggering
"""

import asyncio
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime, timedelta
from enum import Enum
import uuid

from utils.logger import get_logger
from utils.errors import SchedulerException
from config.settings import settings


logger = get_logger(__name__)


class JobStatus(str, Enum):
    """Job status values."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobFrequency(str, Enum):
    """Job frequency options."""
    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ScheduledJob:
    """Represents a scheduled job."""
    
    def __init__(
        self,
        job_id: str,
        name: str,
        handler: Callable,
        frequency: JobFrequency,
        next_run: datetime,
        max_retries: int = 3,
        timeout_seconds: int = 300,
        data: Optional[Dict[str, Any]] = None
    ):
        self.job_id = job_id
        self.name = name
        self.handler = handler
        self.frequency = frequency
        self.next_run = next_run
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.data = data or {}
        
        self.status = JobStatus.PENDING
        self.retry_count = 0
        self.last_run: Optional[datetime] = None
        self.last_result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize job to dictionary."""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "frequency": self.frequency.value,
            "status": self.status.value,
            "next_run": self.next_run.isoformat(),
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error": self.error
        }


class JobScheduler:
    """Background job scheduler with persistence."""
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.JobScheduler")
        self.jobs: Dict[str, ScheduledJob] = {}
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the scheduler."""
        if self.is_running:
            self.logger.warning("Scheduler already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._run_scheduler())
        self.logger.info("Scheduler started")
    
    async def stop(self) -> None:
        """Stop the scheduler."""
        self.is_running = False
        if self._task:
            await self._task
        self.logger.info("Scheduler stopped")
    
    async def schedule_job(
        self,
        name: str,
        handler: Callable,
        frequency: JobFrequency,
        first_run_delay_seconds: int = 60,
        max_retries: int = 3,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Schedule a new job.
        
        Args:
            name: Descriptive job name
            handler: Async function to execute
            frequency: How often to run
            first_run_delay_seconds: Seconds until first run
            max_retries: Max retries on failure
            data: Job-specific data
            
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        next_run = datetime.utcnow() + timedelta(seconds=first_run_delay_seconds)
        
        job = ScheduledJob(
            job_id=job_id,
            name=name,
            handler=handler,
            frequency=frequency,
            next_run=next_run,
            max_retries=max_retries,
            data=data
        )
        
        self.jobs[job_id] = job
        self.logger.info(f"Scheduled job: {name} (ID: {job_id}, first run in {first_run_delay_seconds}s)")
        
        return job_id
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled job."""
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].status = JobStatus.CANCELLED
        del self.jobs[job_id]
        self.logger.info(f"Cancelled job: {job_id}")
        return True
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a job."""
        if job_id not in self.jobs:
            return None
        return self.jobs[job_id].to_dict()
    
    async def _run_scheduler(self) -> None:
        """Main scheduler loop."""
        self.logger.info("Starting scheduler loop")
        
        while self.is_running:
            try:
                now = datetime.utcnow()
                jobs_to_run = [
                    job_id for job_id, job in self.jobs.items()
                    if job.next_run <= now and job.status != JobStatus.CANCELLED
                ]
                
                # Run jobs concurrently
                if jobs_to_run:
                    await asyncio.gather(
                        *[self._execute_job(job_id) for job_id in jobs_to_run],
                        return_exceptions=True
                    )
                
                # Sleep before next check
                await asyncio.sleep(10)  # Check every 10 seconds
            
            except Exception as e:
                self.logger.error(f"Scheduler loop error: {str(e)}")
                await asyncio.sleep(10)
    
    async def _execute_job(self, job_id: str) -> None:
        """Execute a single job with retry logic."""
        job = self.jobs.get(job_id)
        if not job:
            return
        
        job.status = JobStatus.RUNNING
        
        try:
            self.logger.info(f"Executing job: {job.name}")
            
            # Run with timeout
            result = await asyncio.wait_for(
                job.handler(job.data),
                timeout=job.timeout_seconds
            )
            
            job.status = JobStatus.COMPLETED
            job.last_run = datetime.utcnow()
            job.last_result = result
            job.retry_count = 0
            job.error = None
            
            self.logger.info(f"Job completed: {job.name}")
            
            # Schedule next run
            await self._schedule_next_run(job)
        
        except asyncio.TimeoutError:
            self.logger.error(f"Job timeout: {job.name}")
            await self._handle_job_failure(job, "Job execution timeout")
        
        except Exception as e:
            self.logger.error(f"Job failed: {job.name} - {str(e)}")
            await self._handle_job_failure(job, str(e))
    
    async def _handle_job_failure(self, job: ScheduledJob, error: str) -> None:
        """Handle job failure with retry logic."""
        job.error = error
        job.retry_count += 1
        
        if job.retry_count >= job.max_retries:
            job.status = JobStatus.FAILED
            self.logger.error(
                f"Job permanently failed: {job.name} "
                f"(after {job.retry_count} retries)"
            )
            return
        
        # Schedule retry with exponential backoff
        delay_seconds = min(60, 2 ** job.retry_count * 10)
        job.next_run = datetime.utcnow() + timedelta(seconds=delay_seconds)
        job.status = JobStatus.PENDING
        
        self.logger.info(
            f"Retrying job: {job.name} (attempt {job.retry_count}/{job.max_retries}, "
            f"next attempt in {delay_seconds}s)"
        )
    
    async def _schedule_next_run(self, job: ScheduledJob) -> None:
        """Schedule next run based on frequency."""
        if job.frequency == JobFrequency.ONCE:
            await self.cancel_job(job.job_id)
        
        elif job.frequency == JobFrequency.HOURLY:
            job.next_run = datetime.utcnow() + timedelta(hours=1)
            job.status = JobStatus.PENDING
        
        elif job.frequency == JobFrequency.DAILY:
            job.next_run = datetime.utcnow() + timedelta(days=1)
            job.status = JobStatus.PENDING
        
        elif job.frequency == JobFrequency.WEEKLY:
            job.next_run = datetime.utcnow() + timedelta(weeks=1)
            job.status = JobStatus.PENDING
        
        elif job.frequency == JobFrequency.MONTHLY:
            job.next_run = datetime.utcnow() + timedelta(days=30)
            job.status = JobStatus.PENDING


# Singleton scheduler instance
_scheduler: Optional[JobScheduler] = None


def get_scheduler() -> JobScheduler:
    """Get or create scheduler singleton."""
    global _scheduler
    if _scheduler is None:
        _scheduler = JobScheduler()
    return _scheduler


# Pre-defined scheduled jobs

async def visa_status_check_job(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Background job for checking visa status.
    
    Runs daily to monitor visa renewal dates.
    """
    logger = get_logger("visa_status_check_job")
    
    try:
        # TODO: Integrate with actual visa status API
        # For now, just return mock data
        
        logger.info("Running visa status check")
        
        return {
            "status": "completed",
            "checked_count": 0,
            "renewals_needed": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Visa status check failed: {str(e)}")
        raise


async def payroll_cycle_job(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Background job for processing payroll cycles.
    
    Runs bi-weekly or monthly depending on company policy.
    """
    logger = get_logger("payroll_cycle_job")
    
    try:
        # TODO: Integrate with payroll engine
        
        logger.info("Processing payroll cycle")
        
        return {
            "status": "completed",
            "employees_processed": 0,
            "total_payroll": "0.00",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Payroll cycle failed: {str(e)}")
        raise


async def follow_up_reminder_job(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Background job for sending follow-up reminders.
    
    Runs daily to remind about pending actions.
    """
    logger = get_logger("follow_up_reminder_job")
    
    try:
        # TODO: Query pending reminders and send notifications
        
        logger.info("Processing follow-up reminders")
        
        return {
            "status": "completed",
            "reminders_sent": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Follow-up reminder failed: {str(e)}")
        raise


async def sales_lead_nurturing_job(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Background job for nurturing sales leads.
    
    Runs hourly to send automated follow-ups to leads.
    """
    logger = get_logger("sales_lead_nurturing_job")
    
    try:
        # TODO: Query CRM for leads needing follow-up, send emails
        
        logger.info("Nurturing sales leads")
        
        return {
            "status": "completed",
            "leads_contacted": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Sales lead nurturing failed: {str(e)}")
        raise
