"""
Database models for the CalDAV migration web interface.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()


class ServerConfig(db.Model):
    """CalDAV/CardDAV server configuration."""
    
    __tablename__ = 'server_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    url = db.Column(db.String(500), nullable=False)
    principal_path = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    server_type = db.Column(db.String(100), nullable=True)  # e.g., "Carbonio", "Mailcow", "Nextcloud"
    verify_ssl = db.Column(db.Boolean, default=True)  # Verify SSL certificates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    accounts = db.relationship('Account', back_populates='server', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert server config to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'principal_path': self.principal_path,
            'description': self.description,
            'server_type': self.server_type,
            'verify_ssl': self.verify_ssl,
            'account_count': len(self.accounts),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Account(db.Model):
    """CalDAV/CardDAV account configuration."""
    
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    server_id = db.Column(db.Integer, db.ForeignKey('server_configs.id'), nullable=False)
    username = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(500), nullable=False)  # Consider encryption in production
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    server = db.relationship('ServerConfig', back_populates='accounts')
    source_syncs = db.relationship('SyncJob', foreign_keys='SyncJob.source_id', back_populates='source_account', cascade='all, delete-orphan')
    destination_syncs = db.relationship('SyncJob', foreign_keys='SyncJob.destination_id', back_populates='destination_account', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert account to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'server_id': self.server_id,
            'server_name': self.server.name if self.server else None,
            'server_url': self.server.url if self.server else None,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_caldav_config(self):
        """Convert to CalDAV client configuration."""
        return {
            'url': self.server.url if self.server else '',
            'username': self.username,
            'password': self.password,
            'principal_path': self.server.principal_path if self.server else None,
            'verify_ssl': self.server.verify_ssl if self.server else True,
            'server_type': self.server.server_type if self.server else None
        }


class SyncJob(db.Model):
    """Synchronization job configuration."""
    
    __tablename__ = 'sync_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    source_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    
    # Sync options
    migrate_calendars = db.Column(db.Boolean, default=True)
    migrate_contacts = db.Column(db.Boolean, default=True)
    create_collections = db.Column(db.Boolean, default=True)
    dry_run = db.Column(db.Boolean, default=False)
    skip_dummy_events = db.Column(db.Boolean, default=False)
    
    # Job status
    status = db.Column(db.String(50), default='pending')  # pending, queued, running, paused, completed, failed
    progress = db.Column(db.Integer, default=0)  # 0-100
    
    # Statistics (stored as JSON)
    stats = db.Column(db.Text, default='{}')
    error_message = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    source_account = db.relationship('Account', foreign_keys=[source_id], back_populates='source_syncs')
    destination_account = db.relationship('Account', foreign_keys=[destination_id], back_populates='destination_syncs')
    logs = db.relationship('SyncLog', back_populates='sync_job', cascade='all, delete-orphan', order_by='SyncLog.timestamp')
    
    def to_dict(self):
        """Convert sync job to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'source_id': self.source_id,
            'source_name': self.source_account.name if self.source_account else None,
            'destination_id': self.destination_id,
            'destination_name': self.destination_account.name if self.destination_account else None,
            'migrate_calendars': self.migrate_calendars,
            'migrate_contacts': self.migrate_contacts,
            'create_collections': self.create_collections,
            'dry_run': self.dry_run,
            'skip_dummy_events': self.skip_dummy_events,
            'status': self.status,
            'progress': self.progress,
            'stats': json.loads(self.stats) if self.stats else {},
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def update_stats(self, stats_dict):
        """Update statistics."""
        self.stats = json.dumps(stats_dict)
    
    def get_stats(self):
        """Get statistics as dictionary."""
        return json.loads(self.stats) if self.stats else {}


class SyncLog(db.Model):
    """Log entries for synchronization jobs."""
    
    __tablename__ = 'sync_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    sync_job_id = db.Column(db.Integer, db.ForeignKey('sync_jobs.id'), nullable=False)
    level = db.Column(db.String(20), nullable=False)  # INFO, WARNING, ERROR
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    sync_job = db.relationship('SyncJob', back_populates='logs')
    
    def to_dict(self):
        """Convert log entry to dictionary."""
        return {
            'id': self.id,
            'level': self.level,
            'message': self.message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
