# CalDAV Migration Tool - Web Interface

## Overview

A complete web-based interface for managing CalDAV/CardDAV migrations between servers. Built with Flask, SQLAlchemy, and Bootstrap 5.

## Features

### ✨ Core Functionality
- **Account Management**: Add multiple CalDAV/CardDAV server accounts
- **Sync Job Configuration**: Create synchronization jobs between any two accounts
- **Queue System**: Queue multiple synchronizations and process them sequentially
- **Real-time Monitoring**: Live status updates and progress tracking
- **Job Control**: Start, pause, and resume synchronizations
- **Persistent Storage**: All accounts and sync jobs saved to SQLite database
- **Detailed Logging**: View detailed logs for each synchronization

### 🎯 Use Cases
- Migrate from Carbonio to Mailcow
- Migrate from any CalDAV server to another
- Backup calendars and contacts
- Sync between multiple servers

## Quick Start

### 1. Install and Run

```bash
# Navigate to the project directory
cd /home/mj/Hentet/mailcow/caldav-migration

# Run the startup script (creates venv, installs deps, starts server)
./start-web.sh
```

The web interface will be available at: **http://localhost:5000**

### 2. Add Accounts

1. Click the "Accounts" tab
2. Click "Add Account"
3. Fill in your server details:
   - **Account Name**: Friendly name (e.g., "Carbonio Server")
   - **Server URL**: Full CalDAV URL (e.g., https://dav.example.com)
   - **Username**: Your account username
   - **Password**: Your account password
   - **Principal Path**: (Optional) Leave empty for auto-discovery

Add both your source and destination accounts.

### 3. Create a Sync Job

1. Switch to the "Synchronizations" tab
2. Click "New Sync Job"
3. Configure the job:
   - **Job Name**: Descriptive name (e.g., "Carbonio → Mailcow")
   - **Source Account**: Select your source server
   - **Destination Account**: Select your destination server
   - **Options**:
     - ☑ Migrate Calendars
     - ☑ Migrate Contacts
     - ☑ Create Missing Collections

### 4. Run the Synchronization

1. Click the "Start" button on your sync job
2. Watch the progress bar and status updates
3. Click "Logs" to see detailed information
4. Use "Pause" to temporarily halt the sync
5. View statistics after completion

## Architecture

### Backend Components

```
app.py              # Flask application and REST API
models.py           # SQLAlchemy database models
worker.py           # Background job queue worker
caldav_client.py    # CalDAV/CardDAV client wrapper
migration.py        # Migration engine logic
```

### Frontend Components

```
templates/index.html    # Main web interface
static/app.js          # JavaScript for UI interactions
static/style.css       # Custom styling
```

### Database Schema

**accounts** - Server account configurations
- id, name, url, username, password, principal_path
- created_at, updated_at

**sync_jobs** - Synchronization job definitions
- id, name, source_id, destination_id
- migrate_calendars, migrate_contacts, create_collections
- status, progress, stats, error_message
- created_at, started_at, completed_at

**sync_logs** - Detailed logs for each job
- id, sync_job_id, level, message, timestamp

## API Endpoints

### Accounts
- `GET /api/accounts` - List all accounts
- `POST /api/accounts` - Create new account
- `GET /api/accounts/<id>` - Get account details
- `PUT /api/accounts/<id>` - Update account
- `DELETE /api/accounts/<id>` - Delete account

### Sync Jobs
- `GET /api/sync-jobs` - List all sync jobs
- `POST /api/sync-jobs` - Create new sync job
- `GET /api/sync-jobs/<id>` - Get job details
- `PUT /api/sync-jobs/<id>` - Update job
- `DELETE /api/sync-jobs/<id>` - Delete job
- `POST /api/sync-jobs/<id>/start` - Start/queue job
- `POST /api/sync-jobs/<id>/pause` - Pause job
- `POST /api/sync-jobs/<id>/resume` - Resume job
- `GET /api/sync-jobs/<id>/logs` - Get job logs

### Worker
- `GET /api/worker/status` - Get worker status

## Job Status Flow

```
pending → queued → running → completed
                     ↓
                  paused → running
                     ↓
                  failed
```

- **pending**: Job created, not started
- **queued**: Job added to queue, waiting to run
- **running**: Job currently executing
- **paused**: Job temporarily paused
- **completed**: Job finished successfully
- **failed**: Job encountered an error

## Configuration

### Manual Installation

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-web.txt

# Run the application
python3 app.py
```

### Production Deployment

For production use, consider:

1. **Use a production WSGI server** (e.g., Gunicorn):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Secure the application**:
   - Use HTTPS (reverse proxy with nginx/Apache)
   - Implement proper authentication
   - Encrypt passwords in database
   - Set a strong SECRET_KEY

3. **Use a proper database**:
   - PostgreSQL or MySQL for better concurrency
   - Update `SQLALCHEMY_DATABASE_URI` in app.py

4. **Enable logging**:
   - Configure file logging
   - Set up log rotation

## Troubleshooting

### Port Already in Use
If port 5000 is in use, edit `app.py` and change:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Database Issues
Delete the database to start fresh:
```bash
rm caldav_migration.db
```
The database will be recreated on next startup.

### Connection Errors
- Verify server URLs are correct (include https://)
- Check firewall/network access
- Test credentials with the CLI tool first: `./migrate.py --dry-run`

### Worker Not Running
The worker starts automatically with the Flask app. Check:
- Look for errors in the terminal/console
- Check the worker status indicator in the navbar

## Security Considerations

⚠️ **Important**: This is a development version. For production:

1. **Passwords**: Currently stored in plain text. Implement encryption:
   ```python
   from cryptography.fernet import Fernet
   ```

2. **Authentication**: Add user login system
3. **HTTPS**: Always use HTTPS in production
4. **Secret Key**: Generate a secure random key
5. **CORS**: Configure properly if accessing from different domains

## Advanced Usage

### Multiple Simultaneous Syncs
The worker processes jobs sequentially. To run multiple syncs in parallel:
- Run multiple instances of the web app on different ports
- Or modify `worker.py` to use multiple threads

### Scheduling
Integrate with cron or systemd timers to run syncs automatically:
```bash
# Add to crontab
0 2 * * * curl -X POST http://localhost:5000/api/sync-jobs/1/start
```

### Export/Import Configuration
Save sync jobs to JSON:
```bash
curl http://localhost:5000/api/sync-jobs > backup.json
```

## License

MIT License - Feel free to use and modify as needed.
