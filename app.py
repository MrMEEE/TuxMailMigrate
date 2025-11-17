"""
Flask web application for CalDAV migration management.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from models import db, ServerConfig, Account, SyncJob, SyncLog
from worker import get_worker
import logging
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///caldav_migration.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

# Initialize database
db.init_app(app)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize database tables
with app.app_context():
    db.create_all()
    logger.info("Database initialized")

# Initialize worker
worker = get_worker(app, db)


# ==================== Web Pages ====================

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


# ==================== Server Config API ====================

@app.route('/api/servers', methods=['GET'])
def get_servers():
    """Get all server configurations."""
    servers = ServerConfig.query.all()
    return jsonify([server.to_dict() for server in servers])


@app.route('/api/servers', methods=['POST'])
def create_server():
    """Create a new server configuration."""
    data = request.json
    
    # Validate required fields
    required = ['name', 'url']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Check for duplicate name
    existing = ServerConfig.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({'error': 'Server with this name already exists'}), 400
    
    server = ServerConfig(
        name=data['name'],
        url=data['url'],
        principal_path=data.get('principal_path'),
        description=data.get('description'),
        server_type=data.get('server_type'),
        verify_ssl=data.get('verify_ssl', True)
    )
    
    db.session.add(server)
    db.session.commit()
    
    logger.info(f"Created server config: {server.name}")
    return jsonify(server.to_dict()), 201


@app.route('/api/servers/<int:server_id>', methods=['GET'])
def get_server(server_id):
    """Get a specific server configuration."""
    server = db.session.get(ServerConfig, server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404
    return jsonify(server.to_dict())


@app.route('/api/servers/<int:server_id>', methods=['PUT'])
def update_server(server_id):
    """Update a server configuration."""
    server = db.session.get(ServerConfig, server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404
    
    data = request.json
    
    # Update fields
    if 'name' in data:
        server.name = data['name']
    if 'url' in data:
        server.url = data['url']
    if 'principal_path' in data:
        server.principal_path = data['principal_path']
    if 'description' in data:
        server.description = data['description']
    if 'server_type' in data:
        server.server_type = data['server_type']
    if 'verify_ssl' in data:
        server.verify_ssl = data['verify_ssl']
    
    db.session.commit()
    
    logger.info(f"Updated server config: {server.name}")
    return jsonify(server.to_dict())


@app.route('/api/servers/<int:server_id>', methods=['DELETE'])
def delete_server(server_id):
    """Delete a server configuration."""
    server = db.session.get(ServerConfig, server_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404
    
    # Check if server has accounts
    if len(server.accounts) > 0:
        return jsonify({'error': f'Cannot delete server with {len(server.accounts)} associated account(s)'}), 400
    
    name = server.name
    db.session.delete(server)
    db.session.commit()
    
    logger.info(f"Deleted server config: {name}")
    return jsonify({'message': 'Server deleted'}), 200


# ==================== Account API ====================

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """Get all accounts."""
    accounts = Account.query.all()
    return jsonify([account.to_dict() for account in accounts])


@app.route('/api/accounts', methods=['POST'])
def create_account():
    """Create a new account."""
    data = request.json
    
    # Validate required fields
    required = ['name', 'server_id', 'username', 'password']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate server exists
    server = db.session.get(ServerConfig, data['server_id'])
    if not server:
        return jsonify({'error': 'Server configuration not found'}), 404
    
    # Check for duplicate name
    existing = Account.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({'error': 'Account with this name already exists'}), 400
    
    account = Account(
        name=data['name'],
        server_id=data['server_id'],
        username=data['username'],
        password=data['password']
    )
    
    db.session.add(account)
    db.session.commit()
    
    logger.info(f"Created account: {account.name}")
    return jsonify(account.to_dict()), 201


@app.route('/api/accounts/<int:account_id>', methods=['GET'])
def get_account(account_id):
    """Get a specific account."""
    account = db.session.get(Account, account_id)
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    return jsonify(account.to_dict())


@app.route('/api/accounts/<int:account_id>', methods=['PUT'])
def update_account(account_id):
    """Update an account."""
    account = db.session.get(Account, account_id)
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    data = request.json
    
    # Update fields
    if 'name' in data:
        account.name = data['name']
    if 'server_id' in data:
        # Validate server exists
        server = db.session.get(ServerConfig, data['server_id'])
        if not server:
            return jsonify({'error': 'Server configuration not found'}), 404
        account.server_id = data['server_id']
    if 'username' in data:
        account.username = data['username']
    if 'password' in data:
        account.password = data['password']
    
    db.session.commit()
    
    logger.info(f"Updated account: {account.name}")
    return jsonify(account.to_dict())


@app.route('/api/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    """Delete an account."""
    account = db.session.get(Account, account_id)
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    name = account.name
    db.session.delete(account)
    db.session.commit()
    
    logger.info(f"Deleted account: {name}")
    return jsonify({'message': 'Account deleted'}), 200


# ==================== Sync Job API ====================

@app.route('/api/sync-jobs', methods=['GET'])
def get_sync_jobs():
    """Get all sync jobs."""
    jobs = SyncJob.query.order_by(SyncJob.created_at.desc()).all()
    return jsonify([job.to_dict() for job in jobs])


@app.route('/api/sync-jobs', methods=['POST'])
def create_sync_job():
    """Create a new sync job."""
    data = request.json
    
    # Validate required fields
    required = ['name', 'source_id', 'destination_id']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate accounts exist
    source = db.session.get(Account, data['source_id'])
    destination = db.session.get(Account, data['destination_id'])
    
    if not source:
        return jsonify({'error': 'Source account not found'}), 404
    if not destination:
        return jsonify({'error': 'Destination account not found'}), 404
    
    job = SyncJob(
        name=data['name'],
        source_id=data['source_id'],
        destination_id=data['destination_id'],
        migrate_calendars=data.get('migrate_calendars', True),
        migrate_contacts=data.get('migrate_contacts', True),
        create_collections=data.get('create_collections', True),
        dry_run=data.get('dry_run', False),
        skip_dummy_events=data.get('skip_dummy_events', False)
    )
    
    db.session.add(job)
    db.session.commit()
    
    logger.info(f"Created sync job: {job.name}")
    return jsonify(job.to_dict()), 201


@app.route('/api/sync-jobs/<int:job_id>', methods=['GET'])
def get_sync_job(job_id):
    """Get a specific sync job."""
    job = db.session.get(SyncJob, job_id)
    if not job:
        return jsonify({'error': 'Sync job not found'}), 404
    return jsonify(job.to_dict())


@app.route('/api/sync-jobs/<int:job_id>', methods=['PUT'])
def update_sync_job(job_id):
    """Update a sync job."""
    job = db.session.get(SyncJob, job_id)
    if not job:
        return jsonify({'error': 'Sync job not found'}), 404
    
    # Only allow updates if job is not running
    if job.status == 'running':
        return jsonify({'error': 'Cannot update running job'}), 400
    
    data = request.json
    
    if 'name' in data:
        job.name = data['name']
    if 'source_id' in data:
        job.source_id = data['source_id']
    if 'destination_id' in data:
        job.destination_id = data['destination_id']
    if 'migrate_calendars' in data:
        job.migrate_calendars = data['migrate_calendars']
    if 'migrate_contacts' in data:
        job.migrate_contacts = data['migrate_contacts']
    if 'create_collections' in data:
        job.create_collections = data['create_collections']
    if 'dry_run' in data:
        job.dry_run = data['dry_run']
    if 'skip_dummy_events' in data:
        job.skip_dummy_events = data['skip_dummy_events']
    
    db.session.commit()
    
    logger.info(f"Updated sync job: {job.name}")
    return jsonify(job.to_dict())


@app.route('/api/sync-jobs/<int:job_id>', methods=['DELETE'])
def delete_sync_job(job_id):
    """Delete a sync job."""
    job = db.session.get(SyncJob, job_id)
    if not job:
        return jsonify({'error': 'Sync job not found'}), 404
    
    # Don't allow deleting running jobs
    if job.status == 'running':
        return jsonify({'error': 'Cannot delete running job'}), 400
    
    name = job.name
    db.session.delete(job)
    db.session.commit()
    
    logger.info(f"Deleted sync job: {name}")
    return jsonify({'message': 'Sync job deleted'}), 200


# ==================== Sync Job Control ====================

@app.route('/api/sync-jobs/<int:job_id>/start', methods=['POST'])
def start_sync_job(job_id):
    """Start/queue a sync job."""
    job = db.session.get(SyncJob, job_id)
    if not job:
        return jsonify({'error': 'Sync job not found'}), 404
    
    if job.status == 'running':
        return jsonify({'error': 'Job is already running'}), 400
    
    # Get optional parameters for selective sync
    data = request.get_json() or {}
    calendars_only = data.get('calendars_only', False)
    contacts_only = data.get('contacts_only', False)
    
    # Store original settings to restore later
    original_calendars = job.migrate_calendars
    original_contacts = job.migrate_contacts
    
    # Apply selective sync if requested
    if calendars_only:
        job.migrate_calendars = True
        job.migrate_contacts = False
    elif contacts_only:
        job.migrate_calendars = False
        job.migrate_contacts = True
    
    # Reset job status
    job.status = 'pending'
    job.progress = 0
    job.error_message = None
    job.started_at = None
    job.completed_at = None
    db.session.commit()
    
    # Enqueue the job
    worker.enqueue_job(job_id)
    
    # Restore original settings after a short delay (they'll be used for display)
    # The worker will use the current settings when it processes the job
    if calendars_only or contacts_only:
        def restore_settings():
            import time
            time.sleep(2)  # Wait for worker to pick up the job
            with app.app_context():
                j = db.session.get(SyncJob, job_id)
                if j and j.status != 'pending':  # Only restore if job has started
                    j.migrate_calendars = original_calendars
                    j.migrate_contacts = original_contacts
                    db.session.commit()
        
        import threading
        threading.Thread(target=restore_settings, daemon=True).start()
    
    logger.info(f"Started sync job: {job.name}")
    return jsonify(job.to_dict())


@app.route('/api/sync-jobs/<int:job_id>/cancel', methods=['POST'])
def cancel_sync_job(job_id):
    """Cancel a running sync job."""
    job = db.session.get(SyncJob, job_id)
    if not job:
        return jsonify({'error': 'Sync job not found'}), 404
    
    if job.status != 'running':
        return jsonify({'error': 'Job is not running'}), 400
    
    if worker.current_job_id != job_id:
        return jsonify({'error': 'Job is not currently executing'}), 400
    
    # Request cancellation
    if worker.cancel_job():
        logger.info(f"Cancellation requested for sync job: {job.name}")
        return jsonify({'message': 'Cancellation requested', 'job': job.to_dict()})
    else:
        return jsonify({'error': 'Could not cancel job'}), 500


@app.route('/api/sync-jobs/<int:job_id>/pause', methods=['POST'])
def pause_sync_job(job_id):
    """Pause a sync job (pauses the worker)."""
    job = db.session.get(SyncJob, job_id)
    if not job:
        return jsonify({'error': 'Sync job not found'}), 404
    
    worker.pause()
    job.status = 'paused'
    db.session.commit()
    
    logger.info(f"Paused worker (job: {job.name})")
    return jsonify(job.to_dict())


@app.route('/api/sync-jobs/<int:job_id>/resume', methods=['POST'])
def resume_sync_job(job_id):
    """Resume a paused sync job."""
    job = db.session.get(SyncJob, job_id)
    if not job:
        return jsonify({'error': 'Sync job not found'}), 404
    
    worker.resume()
    job.status = 'running'
    db.session.commit()
    
    logger.info(f"Resumed worker (job: {job.name})")
    return jsonify(job.to_dict())


@app.route('/api/sync-jobs/<int:job_id>/logs', methods=['GET'])
def get_sync_logs(job_id):
    """Get logs for a sync job."""
    job = db.session.get(SyncJob, job_id)
    if not job:
        return jsonify({'error': 'Sync job not found'}), 404
    
    logs = SyncLog.query.filter_by(sync_job_id=job_id).order_by(SyncLog.timestamp.desc()).limit(100).all()
    return jsonify([log.to_dict() for log in logs])


# ==================== Worker Status ====================

@app.route('/api/worker/status', methods=['GET'])
def worker_status():
    """Get worker status."""
    return jsonify({
        'running': worker.running,
        'paused': worker.paused,
        'current_job_id': worker.current_job_id,
        'queue_size': worker.job_queue.qsize()
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
