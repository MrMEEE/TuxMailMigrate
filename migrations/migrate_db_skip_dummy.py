#!/usr/bin/env python3
"""
Database migration script to add skip_dummy_events column to sync_jobs table.
"""

import sqlite3
import os

def migrate():
    db_path = os.path.join('instance', 'caldav_migration.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(sync_jobs)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'skip_dummy_events' in columns:
        print("Column 'skip_dummy_events' already exists")
        conn.close()
        return
    
    print("Adding 'skip_dummy_events' column to sync_jobs table...")
    cursor.execute("ALTER TABLE sync_jobs ADD COLUMN skip_dummy_events BOOLEAN DEFAULT 0")
    conn.commit()
    conn.close()
    
    print("Migration completed successfully!")

if __name__ == '__main__':
    migrate()
