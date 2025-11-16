#!/usr/bin/env python3
"""
Add dry_run column to sync_jobs table
"""

import sqlite3
import sys
import os

def migrate_database():
    # Try instance folder first, then current directory
    db_paths = [
        'instance/caldav_migration.db',
        'caldav_migration.db'
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("Database not found. Looking for:", db_paths)
        return False
    
    print(f"Using database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if dry_run column already exists
        cursor.execute("PRAGMA table_info(sync_jobs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'dry_run' in columns:
            print("✓ dry_run column already exists")
            return True
        
        print("Adding dry_run column to sync_jobs table...")
        cursor.execute("""
            ALTER TABLE sync_jobs 
            ADD COLUMN dry_run BOOLEAN DEFAULT 0
        """)
        
        conn.commit()
        print("✓ Successfully added dry_run column")
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    success = migrate_database()
    sys.exit(0 if success else 1)
