#!/usr/bin/env python3
"""
Database migration script to add server configurations.
This will migrate existing accounts to use the new ServerConfig model.
"""

import sqlite3
import sys
import os
from pathlib import Path

# Check both locations for the database
DB_PATH = 'instance/caldav_migration.db' if Path('instance/caldav_migration.db').exists() else 'caldav_migration.db'

def migrate_database():
    """Migrate database to add server configurations."""
    
    if not Path(DB_PATH).exists():
        print(f"✓ Database {DB_PATH} doesn't exist yet - nothing to migrate")
        return True
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if migration is needed
        cursor.execute("PRAGMA table_info(accounts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'server_id' in columns:
            print("✓ Database already migrated")
            return True
        
        print("🔄 Starting database migration...")
        
        # Create server_configs table
        print("  Creating server_configs table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS server_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL UNIQUE,
                url VARCHAR(500) NOT NULL,
                principal_path VARCHAR(500),
                description TEXT,
                server_type VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Get existing accounts
        cursor.execute("SELECT id, name, url, principal_path FROM accounts")
        existing_accounts = cursor.fetchall()
        
        if existing_accounts:
            print(f"  Found {len(existing_accounts)} existing account(s)")
            
            # Create a server config for each unique URL
            url_to_server = {}
            for account_id, account_name, url, principal_path in existing_accounts:
                if url not in url_to_server:
                    # Create server config from the account's URL
                    server_name = f"Server for {account_name}"
                    print(f"  Creating server config: {server_name}")
                    
                    cursor.execute('''
                        INSERT INTO server_configs (name, url, principal_path, description)
                        VALUES (?, ?, ?, ?)
                    ''', (server_name, url, principal_path, "Auto-generated from existing account"))
                    
                    url_to_server[url] = cursor.lastrowid
            
            # Create new accounts table with server_id
            print("  Creating new accounts table structure...")
            cursor.execute('''
                CREATE TABLE accounts_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(200) NOT NULL UNIQUE,
                    server_id INTEGER NOT NULL,
                    username VARCHAR(200) NOT NULL,
                    password VARCHAR(500) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (server_id) REFERENCES server_configs (id)
                )
            ''')
            
            # Migrate accounts to new structure
            print("  Migrating accounts...")
            cursor.execute("SELECT id, name, url, username, password, created_at, updated_at FROM accounts")
            for account_id, name, url, username, password, created_at, updated_at in cursor.fetchall():
                server_id = url_to_server.get(url)
                if server_id:
                    cursor.execute('''
                        INSERT INTO accounts_new (id, name, server_id, username, password, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (account_id, name, server_id, username, password, created_at, updated_at))
            
            # Drop old table and rename new one
            print("  Finalizing migration...")
            cursor.execute("DROP TABLE accounts")
            cursor.execute("ALTER TABLE accounts_new RENAME TO accounts")
            
        else:
            print("  No existing accounts found")
            # Just create the new accounts table
            cursor.execute("DROP TABLE IF EXISTS accounts")
            cursor.execute('''
                CREATE TABLE accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(200) NOT NULL UNIQUE,
                    server_id INTEGER NOT NULL,
                    username VARCHAR(200) NOT NULL,
                    password VARCHAR(500) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (server_id) REFERENCES server_configs (id)
                )
            ''')
        
        conn.commit()
        print("✓ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {str(e)}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    success = migrate_database()
    sys.exit(0 if success else 1)
