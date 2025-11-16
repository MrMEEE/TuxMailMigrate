# Project Structure

```
caldav-migration/
│
├── 📱 Web Interface Components
│   ├── app.py                  # Flask application & REST API
│   ├── models.py               # Database models (SQLAlchemy)
│   ├── worker.py               # Background job queue worker
│   ├── templates/
│   │   └── index.html         # Main web UI
│   └── static/
│       ├── app.js             # Frontend JavaScript
│       └── style.css          # Custom styling
│
├── 🔧 Core Migration Engine
│   ├── caldav_client.py       # CalDAV/CardDAV client wrapper
│   └── migration.py           # Migration logic
│
├── 💻 Command-Line Interface
│   └── migrate.py             # CLI migration tool
│
├── 📋 Configuration & Setup
│   ├── requirements.txt       # CLI dependencies
│   ├── requirements-web.txt   # Web interface dependencies
│   ├── config.example.json    # Example config for CLI
│   ├── start-web.sh          # Web interface startup script
│   └── .gitignore
│
├── 📚 Documentation
│   ├── README.md              # Main documentation
│   ├── WEB_README.md          # Web interface guide
│   └── STRUCTURE.md           # This file
│
└── 💾 Runtime Data (generated)
    └── caldav_migration.db    # SQLite database
```

## Data Flow

```
┌─────────────────┐
│  Web Browser    │
│  (localhost:5000)│
└────────┬────────┘
         │ HTTP/AJAX
         ▼
┌─────────────────────────────┐
│   Flask App (app.py)        │
│   - REST API                │
│   - Request handling        │
└────────┬────────────────────┘
         │
         ├─────────────┬────────────────┐
         ▼             ▼                ▼
┌──────────────┐ ┌──────────┐ ┌────────────────┐
│   Database   │ │  Worker  │ │ CalDAV Client  │
│   (models.py)│ │(worker.py)│ │(caldav_client.py)│
│   SQLite     │ │  Thread  │ └────────────────┘
└──────────────┘ └─────┬────┘          │
                       │               │
                       ▼               ▼
              ┌─────────────────────────────┐
              │  Migration Engine           │
              │  (migration.py)             │
              └─────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│  Source Server   │        │ Destination Server│
│  (e.g. Carbonio) │        │  (e.g. Mailcow)  │
└──────────────────┘        └──────────────────┘
```

## Component Interactions

### Web Interface Workflow

1. **User adds accounts** via web UI
   - Frontend → API: `POST /api/accounts`
   - API → Database: Store account credentials

2. **User creates sync job**
   - Frontend → API: `POST /api/sync-jobs`
   - API → Database: Create job record (status: pending)

3. **User starts sync job**
   - Frontend → API: `POST /api/sync-jobs/{id}/start`
   - API → Worker: Enqueue job
   - Database: Update status (pending → queued)

4. **Worker processes job**
   - Worker picks job from queue
   - Database: Update status (queued → running)
   - Worker → Migration Engine: Execute sync
   - Migration Engine → CalDAV Clients: Connect to servers
   - CalDAV Clients → Servers: Fetch/upload data
   - Worker → Database: Update progress, logs, stats
   - Database: Update status (running → completed/failed)

5. **User monitors progress**
   - Frontend polls: `GET /api/sync-jobs`
   - Frontend polls: `GET /api/worker/status`
   - Display real-time updates in UI

### Database Tables

```sql
accounts
├── id (PK)
├── name
├── url
├── username
├── password
├── principal_path
├── created_at
└── updated_at

sync_jobs
├── id (PK)
├── name
├── source_id (FK → accounts)
├── destination_id (FK → accounts)
├── migrate_calendars
├── migrate_contacts
├── create_collections
├── status
├── progress
├── stats (JSON)
├── error_message
├── created_at
├── started_at
└── completed_at

sync_logs
├── id (PK)
├── sync_job_id (FK → sync_jobs)
├── level (INFO/WARNING/ERROR)
├── message
└── timestamp
```

## Key Design Decisions

### 1. Threading Model
- Single background worker thread
- Sequential job processing (one at a time)
- Thread-safe queue for job management
- Prevents database conflicts and resource contention

### 2. Database Choice
- SQLite for simplicity and zero configuration
- Suitable for single-user/small team usage
- Easy backup (single file)
- Can be upgraded to PostgreSQL/MySQL for production

### 3. API Design
- RESTful endpoints
- JSON request/response format
- Clear separation between frontend and backend
- Enables future mobile apps or CLI API clients

### 4. Frontend Architecture
- Vanilla JavaScript (no heavy frameworks)
- Bootstrap 5 for responsive design
- AJAX for async updates
- Auto-refresh every 3-5 seconds for status updates

### 5. Error Handling
- Graceful degradation on individual item failures
- Detailed logging at multiple levels
- User-friendly error messages
- Job continues even if some items fail

## Extending the System

### Adding New Features

1. **Email Notifications**
   - Modify `worker.py` to send emails on completion
   - Add SMTP config to database or settings

2. **Scheduling**
   - Add `schedule` field to sync_jobs
   - Implement cron-like scheduler in worker

3. **Multi-user Support**
   - Add `users` table
   - Add authentication middleware
   - Add user_id FK to accounts/jobs

4. **Dry-run in Web UI**
   - Add `dry_run` checkbox to sync job form
   - Pass through to migration engine

5. **Selective Migration**
   - Add calendar/contact picker UI
   - Store selection in sync_jobs
   - Filter in migration engine

### Performance Optimization

1. **Parallel Processing**
   - Use multiple worker threads
   - Process different jobs simultaneously
   - Add locking mechanism for shared resources

2. **Batch Operations**
   - Group calendar events for bulk upload
   - Reduce API calls to CalDAV servers

3. **Caching**
   - Cache server capabilities
   - Reduce redundant authentication

4. **Progress Streaming**
   - Use WebSockets instead of polling
   - Real-time log streaming
