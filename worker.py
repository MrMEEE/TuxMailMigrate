"""
Background worker for processing synchronization jobs.
"""

import threading
import logging
import queue
from datetime import datetime
from typing import Optional

from caldav_client import CalDAVClient
from migration import MigrationEngine


class SyncWorker:
    """Background worker for processing sync jobs."""
    
    def __init__(self, app, db):
        """
        Initialize sync worker.
        
        Args:
            app: Flask application instance
            db: SQLAlchemy database instance
        """
        self.app = app
        self.db = db
        self.job_queue = queue.Queue()
        self.current_job_id = None
        self.cancel_current = False
        self.worker_thread = None
        self.running = False
        self.paused = False
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def start(self):
        """Start the worker thread."""
        if self.worker_thread and self.worker_thread.is_alive():
            self.logger.warning("Worker already running")
            return
        
        self.running = True
        self.paused = False
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        self.logger.info("Worker thread started")
    
    def stop(self):
        """Stop the worker thread."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        self.logger.info("Worker thread stopped")
    
    def pause(self):
        """Pause job processing."""
        self.paused = True
        self.logger.info("Worker paused")
    
    def resume(self):
        """Resume job processing."""
        self.paused = False
        self.logger.info("Worker resumed")
    
    def cancel_job(self):
        """Cancel the currently running job."""
        if self.current_job_id:
            self.cancel_current = True
            self.logger.info(f"Cancel requested for job {self.current_job_id}")
            return True
        return False
    
    def enqueue_job(self, job_id: int):
        """
        Add a job to the queue.
        
        Args:
            job_id: ID of the sync job to process
        """
        self.job_queue.put(job_id)
        self.logger.info(f"Job {job_id} added to queue")
        
        # Update job status to queued
        with self.app.app_context():
            from models import SyncJob
            job = self.db.session.get(SyncJob, job_id)
            if job:
                job.status = 'queued'
                self.db.session.commit()
    
    def get_current_job_id(self) -> Optional[int]:
        """Get the ID of the currently running job."""
        return self.current_job_id
    
    def _worker_loop(self):
        """Main worker loop."""
        while self.running:
            try:
                # Wait for a job (with timeout to allow checking running flag)
                try:
                    job_id = self.job_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Wait if paused
                while self.paused and self.running:
                    threading.Event().wait(0.5)
                
                if not self.running:
                    break
                
                # Process the job
                self.current_job_id = job_id
                self.cancel_current = False
                self._process_job(job_id)
                self.current_job_id = None
                self.cancel_current = False
                
                self.job_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Worker loop error: {str(e)}", exc_info=True)
    
    def _process_job(self, job_id: int):
        """
        Process a single sync job.
        
        Args:
            job_id: ID of the job to process
        """
        with self.app.app_context():
            from models import SyncJob, SyncLog
            
            job = self.db.session.get(SyncJob, job_id)
            if not job:
                self.logger.error(f"Job {job_id} not found")
                return
            
            try:
                # Update job status
                job.status = 'running'
                job.started_at = datetime.utcnow()
                job.progress = 0
                job.error_message = None
                self.db.session.commit()
                
                self._add_log(job, 'INFO', f"Starting synchronization: {job.name}")
                
                # Initialize source client
                self._add_log(job, 'INFO', f"Connecting to source: {job.source_account.name}")
                source = CalDAVClient(**job.source_account.to_caldav_config())
                
                success, error_msg = source.connect()
                if not success:
                    raise Exception(f"Failed to connect to source: {error_msg or job.source_account.name}")
                
                job.progress = 10
                self.db.session.commit()
                
                # Initialize destination client
                self._add_log(job, 'INFO', f"Connecting to destination: {job.destination_account.name}")
                destination = CalDAVClient(**job.destination_account.to_caldav_config())
                
                success, error_msg = destination.connect()
                if not success:
                    raise Exception(f"Failed to connect to destination: {error_msg or job.destination_account.name}")
                
                job.progress = 20
                self.db.session.commit()
                
                # Create migration engine with a progress callback so we can update job logs/progress
                def progress_cb(info: dict):
                    try:
                        stage = info.get('stage')
                        processed = int(info.get('processed', 0))
                        total = int(info.get('total', 0))
                        skipped = int(info.get('skipped', 0))

                        # Map stage progress to overall job progress ranges
                        if stage == 'calendars':
                            base = 20
                            rng = 40
                        elif stage == 'contacts':
                            base = 60
                            rng = 30
                        else:
                            base = 0
                            rng = 100

                        pct = base
                        if total > 0:
                            pct = base + int(rng * (processed / total))

                        # Update job progress periodically to avoid excessive writes
                        with self.app.app_context():
                            j = self.db.session.get(SyncJob, job_id)
                            if j:
                                # Only write progress if it's increased or it's the final item
                                if pct != j.progress or processed == total:
                                    j.progress = pct
                                    self.db.session.commit()

                                # Throttle logging: log for small totals every item, otherwise every ~10% or on completion
                                should_log = False
                                if total <= 20:
                                    should_log = True
                                else:
                                    step = max(1, total // 10)
                                    if processed % step == 0 or processed == total:
                                        should_log = True

                                if should_log:
                                    msg = f"[{stage}] {processed}/{total} processed, {skipped} skipped"
                                    self._add_log(j, 'INFO', msg)
                    except Exception as e:
                        self.logger.debug(f"Progress callback error: {e}")

                engine = MigrationEngine(
                    source=source,
                    destination=destination,
                    dry_run=job.dry_run,
                    skip_dummy_events=job.skip_dummy_events,
                    progress_callback=progress_cb
                )
                
                # Log dry-run mode if enabled
                if job.dry_run:
                    self._add_log(job, 'INFO', "🔍 DRY RUN MODE - No changes will be made")
                
                # Perform migration
                if job.migrate_calendars:
                    if self.cancel_current:
                        raise Exception("Job cancelled by user")
                    self._add_log(job, 'INFO', "Migrating calendars..." if not job.dry_run else "Analyzing calendars...")
                    engine.migrate_calendars(create_if_missing=job.create_collections)
                    job.progress = 60
                    self.db.session.commit()
                
                if job.migrate_contacts:
                    if self.cancel_current:
                        raise Exception("Job cancelled by user")
                    self._add_log(job, 'INFO', "Migrating contacts..." if not job.dry_run else "Analyzing contacts...")
                    engine.migrate_contacts(create_if_missing=job.create_collections)
                    job.progress = 90
                    self.db.session.commit()
                
                # Save statistics
                stats = engine.get_stats()
                
                # Add dry-run details if available
                if job.dry_run and hasattr(engine, 'dry_run_details'):
                    stats['dry_run_details'] = engine.dry_run_details
                    
                    # Log summary
                    self._add_log(job, 'INFO', "=== DRY RUN SUMMARY ===")
                    
                    total_events = 0
                    total_dummy_events = 0
                    total_contacts = 0
                    
                    if engine.dry_run_details['calendars']:
                        self._add_log(job, 'INFO', f"📅 Calendars found: {len(engine.dry_run_details['calendars'])}")
                        for cal in engine.dry_run_details['calendars']:
                            total_events += cal['event_count']
                            dummy_count = cal.get('dummy_count', 0)
                            total_dummy_events += dummy_count
                            if dummy_count > 0:
                                self._add_log(job, 'INFO', f"  - {cal['name']}: {cal['event_count']} events ({dummy_count} 'Dummy' events would be skipped)")
                            else:
                                self._add_log(job, 'INFO', f"  - {cal['name']}: {cal['event_count']} events")
                        self._add_log(job, 'INFO', f"  Total events: {total_events}")
                        if total_dummy_events > 0:
                            self._add_log(job, 'INFO', f"  ⏭️  Total 'Dummy' events that would be skipped: {total_dummy_events}")
                    else:
                        self._add_log(job, 'INFO', "📅 No calendars found")
                    
                    if engine.dry_run_details['addressbooks']:
                        self._add_log(job, 'INFO', f"📇 Address books found: {len(engine.dry_run_details['addressbooks'])}")
                        for ab in engine.dry_run_details['addressbooks']:
                            total_contacts += ab['contact_count']
                            self._add_log(job, 'INFO', f"  - {ab['name']}: {ab['contact_count']} contacts")
                        self._add_log(job, 'INFO', f"  Total contacts: {total_contacts}")
                    else:
                        self._add_log(job, 'INFO', "📇 No address books found")
                
                job.update_stats(stats)
                
                # Mark as completed
                job.status = 'completed'
                job.progress = 100
                job.completed_at = datetime.utcnow()
                self.db.session.commit()
                
                if job.dry_run:
                    self._add_log(job, 'INFO', f"🔍 Dry run completed - No changes were made")
                else:
                    self._add_log(job, 'INFO', f"Synchronization completed successfully")
                self._add_log(job, 'INFO', f"Stats: {stats}")
                
            except Exception as e:
                error_msg = str(e)
                self.logger.error(f"Job {job_id} failed: {error_msg}", exc_info=True)
                
                job.status = 'failed'
                job.error_message = error_msg
                job.completed_at = datetime.utcnow()
                self.db.session.commit()
                
                self._add_log(job, 'ERROR', f"Synchronization failed: {error_msg}")
    
    def _add_log(self, job, level: str, message: str):
        """
        Add a log entry for a job.
        
        Args:
            job: SyncJob instance
            level: Log level (INFO, WARNING, ERROR)
            message: Log message
        """
        from models import SyncLog
        
        log = SyncLog(
            sync_job_id=job.id,
            level=level,
            message=message
        )
        self.db.session.add(log)
        self.db.session.commit()
        
        self.logger.info(f"Job {job.id} [{level}]: {message}")


# Global worker instance
_worker = None


def get_worker(app=None, db=None):
    """Get or create the global worker instance."""
    global _worker
    if _worker is None and app and db:
        _worker = SyncWorker(app, db)
        _worker.start()
    return _worker
