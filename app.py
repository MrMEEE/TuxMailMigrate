"""
Flask web application for CalDAV migration management.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from models import db, ServerConfig, Account, SyncJob, SyncLog
from worker import get_worker
import logging
import os
import json

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

# Suppress caldav library's XML parsing warnings for vCard data
# The caldav library expects XML but CardDAV returns vCard (text/vcard)
# These warnings don't indicate errors - they're expected behavior
logging.getLogger('caldav').setLevel(logging.ERROR)
logging.getLogger('caldav.davclient').setLevel(logging.ERROR)
# Suppress lxml XML parsing errors (from caldav trying to parse vCard as XML)
logging.getLogger('lxml').setLevel(logging.ERROR)
logging.getLogger('lxml.etree').setLevel(logging.ERROR)


# Initialize database tables
with app.app_context():
    db.create_all()
    logger.info("Database initialized")
    
    # Reset any jobs that were stuck in 'running' or 'queued' state
    # This happens when the application shuts down while jobs are active
    from models import SyncJob
    stuck_jobs = SyncJob.query.filter(SyncJob.status.in_(['running', 'queued'])).all()
    if stuck_jobs:
        logger.info(f"Found {len(stuck_jobs)} job(s) stuck in running/queued state, resetting...")
        for job in stuck_jobs:
            job.status = 'failed'
            job.error_message = 'Job was interrupted by application shutdown'
            logger.info(f"  Reset job {job.id} ({job.name}) to failed state")
        db.session.commit()
        logger.info("All stuck jobs have been reset")

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
        skip_dummy_events=data.get('skip_dummy_events', False),
        selected_calendars=json.dumps(data['selected_calendars']) if data.get('selected_calendars') else None,
        selected_addressbooks=json.dumps(data['selected_addressbooks']) if data.get('selected_addressbooks') else None
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
    if 'selected_calendars' in data:
        job.selected_calendars = json.dumps(data['selected_calendars']) if data['selected_calendars'] else None
    if 'selected_addressbooks' in data:
        job.selected_addressbooks = json.dumps(data['selected_addressbooks']) if data['selected_addressbooks'] else None
    if 'calendar_mapping' in data:
        job.calendar_mapping = json.dumps(data['calendar_mapping']) if data['calendar_mapping'] else None
    if 'addressbook_mapping' in data:
        job.addressbook_mapping = json.dumps(data['addressbook_mapping']) if data['addressbook_mapping'] else None
    
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
    """Cancel a running or queued sync job."""
    job = db.session.get(SyncJob, job_id)
    if not job:
        return jsonify({'error': 'Sync job not found'}), 404
    
    if job.status not in ('running', 'queued'):
        return jsonify({'error': 'Job is not running or queued'}), 400
    
    # If job is queued, just mark it as failed
    if job.status == 'queued':
        job.status = 'failed'
        job.error_message = 'Cancelled by user'
        job.progress = 0
        db.session.commit()
        logger.info(f"Queued sync job cancelled: {job.name}")
        return jsonify({'message': 'Queued job cancelled', 'job': job.to_dict()})
    
    # If running, request cancellation from worker
    if worker.current_job_id != job_id:
        return jsonify({'error': 'Job is not currently executing'}), 400
    
    # Request cancellation
    if worker.cancel_job():
        logger.info(f"Cancellation requested for running sync job: {job.name}")
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


@app.route('/api/accounts/<int:account_id>/discover', methods=['GET'])
def discover_collections(account_id):
    """Discover calendars and addressbooks from an account."""
    from caldav_client import CalDAVClient
    
    account = db.session.get(Account, account_id)
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    if not account.server:
        return jsonify({'error': 'Account has no server configuration'}), 400
    
    try:
        # Create CalDAV client
        client = CalDAVClient(
            url=account.server.url,
            username=account.username,
            password=account.password,
            principal_path=account.server.principal_path,
            verify_ssl=account.server.verify_ssl,
            server_type=account.server.server_type
        )
        
        # Connect to the server
        success, error = client.connect()
        if not success:
            return jsonify({'error': f'Failed to connect: {error}'}), 400
        
        # Get calendars
        calendars = []
        try:
            cal_list = client.get_calendars()
            for cal in cal_list:
                import caldav
                props = cal.get_properties([caldav.dav.DisplayName()])
                name = props.get('{DAV:}displayname', 'Unnamed Calendar')
                calendars.append({
                    'name': name,
                    'url': str(cal.url)
                })
        except Exception as e:
            logger.warning(f"Failed to get calendars: {e}")
        
        # Get addressbooks
        addressbooks = []
        try:
            ab_list = client.get_addressbooks()
            for ab in ab_list:
                import caldav
                props = ab.get_properties([caldav.dav.DisplayName()])
                name = props.get('{DAV:}displayname', 'Unnamed Address Book')
                addressbooks.append({
                    'name': name,
                    'url': str(ab.url)
                })
        except Exception as e:
            logger.warning(f"Failed to get addressbooks: {e}")
        
        return jsonify({
            'calendars': calendars,
            'addressbooks': addressbooks
        })
        
    except Exception as e:
        logger.error(f"Failed to discover collections: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/sync-jobs/<int:job_id>/discover-both', methods=['GET'])
def discover_both_accounts(job_id):
    """Discover calendars and addressbooks from both source and destination accounts."""
    from caldav_client import CalDAVClient
    import caldav
    
    job = db.session.get(SyncJob, job_id)
    if not job:
        return jsonify({'error': 'Sync job not found'}), 404
    
    source_account = job.source_account
    dest_account = job.destination_account
    
    if not source_account or not dest_account:
        return jsonify({'error': 'Source or destination account not found'}), 404
    
    result = {
        'source': {'calendars': [], 'addressbooks': []},
        'destination': {'calendars': [], 'addressbooks': []}
    }
    
    # Discover from source
    try:
        if source_account.server:
            source_client = CalDAVClient(
                url=source_account.server.url,
                username=source_account.username,
                password=source_account.password,
                principal_path=source_account.server.principal_path,
                verify_ssl=source_account.server.verify_ssl,
                server_type=source_account.server.server_type
            )
            success, error = source_client.connect()
            if success:
                try:
                    cal_list = source_client.get_calendars()
                    for cal in cal_list:
                        props = cal.get_properties([caldav.dav.DisplayName()])
                        name = props.get('{DAV:}displayname', 'Unnamed Calendar')
                        result['source']['calendars'].append({'name': name, 'url': str(cal.url)})
                except Exception as e:
                    logger.warning(f"Failed to get source calendars: {e}")
                
                try:
                    ab_list = source_client.get_addressbooks()
                    for ab in ab_list:
                        props = ab.get_properties([caldav.dav.DisplayName()])
                        name = props.get('{DAV:}displayname', 'Unnamed Address Book')
                        result['source']['addressbooks'].append({'name': name, 'url': str(ab.url)})
                except Exception as e:
                    logger.warning(f"Failed to get source addressbooks: {e}")
    except Exception as e:
        logger.error(f"Source discovery failed: {e}")
        result['source']['error'] = str(e)
    
    # Discover from destination
    try:
        if dest_account.server:
            dest_client = CalDAVClient(
                url=dest_account.server.url,
                username=dest_account.username,
                password=dest_account.password,
                principal_path=dest_account.server.principal_path,
                verify_ssl=dest_account.server.verify_ssl,
                server_type=dest_account.server.server_type
            )
            success, error = dest_client.connect()
            if success:
                try:
                    cal_list = dest_client.get_calendars()
                    for cal in cal_list:
                        props = cal.get_properties([caldav.dav.DisplayName()])
                        name = props.get('{DAV:}displayname', 'Unnamed Calendar')
                        result['destination']['calendars'].append({'name': name, 'url': str(cal.url)})
                except Exception as e:
                    logger.warning(f"Failed to get destination calendars: {e}")
                
                try:
                    ab_list = dest_client.get_addressbooks()
                    for ab in ab_list:
                        props = ab.get_properties([caldav.dav.DisplayName()])
                        name = props.get('{DAV:}displayname', 'Unnamed Address Book')
                        result['destination']['addressbooks'].append({'name': name, 'url': str(ab.url)})
                except Exception as e:
                    logger.warning(f"Failed to get destination addressbooks: {e}")
    except Exception as e:
        logger.error(f"Destination discovery failed: {e}")
        result['destination']['error'] = str(e)
    
    return jsonify(result)


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
