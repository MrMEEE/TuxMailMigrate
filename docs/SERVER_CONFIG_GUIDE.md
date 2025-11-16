# Server Configuration Feature

## Overview

The migration tool now supports **Server Configurations** - a way to define CalDAV/CardDAV servers separately from accounts. This allows you to:

- Define server settings once and reuse for multiple accounts
- Manage multiple user accounts on the same server easily
- Organize servers by type (Carbonio, Mailcow, Nextcloud, etc.)
- Keep server URLs and paths separate from user credentials

## Workflow

### Old Way (Before)
```
Account = Name + URL + Username + Password + Principal Path
```

### New Way (Now)
```
Server Config = Name + URL + Principal Path + Type + Description
Account = Name + Server Config (reference) + Username + Password
```

## Benefits

1. **Easier Multi-User Setup**: Create one server config, then add multiple accounts that use it
2. **Better Organization**: Group accounts by server
3. **Simplified Management**: Update server URL in one place, affects all accounts
4. **Clear Separation**: Server settings separate from user credentials

## Usage Guide

### Step 1: Add Server Configuration

1. Go to the **"Servers"** tab (first tab)
2. Click **"Add Server"**
3. Fill in:
   - **Server Name**: e.g., "Carbonio Production"
   - **Server Type**: Select from dropdown (Carbonio, Mailcow, etc.)
   - **Server URL**: e.g., `https://carbonio.example.com`
   - **Principal Path**: (Optional) Leave empty for auto-discovery
   - **Description**: (Optional) Notes about this server
4. Click **"Add Server"**

### Step 2: Add Accounts Using the Server

1. Go to the **"Accounts"** tab (second tab)
2. Click **"Add Account"**
3. Fill in:
   - **Account Name**: e.g., "john@example.com"
   - **Server**: Select the server you just created
   - **Username**: User's email or username
   - **Password**: User's password
4. Click **"Add Account"**

### Step 3: Create Sync Jobs (Same as Before)

1. Go to **"Synchronizations"** tab
2. Create sync jobs between accounts
3. Run migrations

## Examples

### Example 1: Migrate Multiple Users from Carbonio to Mailcow

1. **Add Servers:**
   - Server 1: "Carbonio Production" → `https://carbonio.company.com`
   - Server 2: "Mailcow Server" → `https://mailcow.company.com`

2. **Add Accounts:**
   - Account 1: "John (Carbonio)" → Server: Carbonio, User: john@company.com
   - Account 2: "John (Mailcow)" → Server: Mailcow, User: john@company.com
   - Account 3: "Mary (Carbonio)" → Server: Carbonio, User: mary@company.com
   - Account 4: "Mary (Mailcow)" → Server: Mailcow, User: mary@company.com

3. **Create Sync Jobs:**
   - Job 1: John (Carbonio) → John (Mailcow)
   - Job 2: Mary (Carbonio) → Mary (Mailcow)

### Example 2: Backup to Different Server

1. **Add Servers:**
   - Server 1: "Production Mailcow"
   - Server 2: "Backup Nextcloud"

2. **Add Accounts:**
   - Account 1: "Main Account" → Server: Production Mailcow
   - Account 2: "Backup Account" → Server: Backup Nextcloud

3. **Create Sync Job:**
   - Job: Main Account → Backup Account (run daily)

## Server Types

Predefined server types for easy identification:
- **Carbonio** - Zextras Carbonio
- **Mailcow** - Mailcow SOGo
- **Nextcloud** - Nextcloud CalDAV/CardDAV
- **SOGo** - Generic SOGo server
- **Other** - Any other CalDAV/CardDAV server

## API Changes

### New Endpoints

**Server Configurations:**
- `GET /api/servers` - List all servers
- `POST /api/servers` - Create server
- `GET /api/servers/<id>` - Get server details
- `PUT /api/servers/<id>` - Update server
- `DELETE /api/servers/<id>` - Delete server (if no accounts)

**Updated Account Endpoints:**
- `POST /api/accounts` - Now requires `server_id` instead of `url`
- Account response includes `server_name` and `server_url`

## Database Migration

For existing installations:

The migration script automatically runs when you start the web interface:
```bash
./start-web.sh
```

Or run manually:
```bash
python3 migrate_db.py
```

**What it does:**
- Creates `server_configs` table
- For each existing account, creates a corresponding server config
- Updates accounts to reference the new server configs
- Preserves all sync jobs and logs

**Note:** Existing databases are automatically migrated. No data is lost.

## UI Updates

### New "Servers" Tab
- First tab in the interface
- Manage all server configurations
- Shows account count for each server
- Cannot delete servers with existing accounts

### Updated "Accounts" Tab
- Account creation requires selecting a server
- Displays server name and URL for each account
- Simpler form (no URL/principal_path fields)

### "Synchronizations" Tab
- Unchanged - works the same as before

## Tips

1. **Create servers first**: The account form requires at least one server
2. **Use descriptive names**: e.g., "Carbonio (OLD)" vs "Mailcow (NEW)"
3. **One server per URL**: Even if it's the same software
4. **Server types help**: Use them to quickly identify server software
5. **Descriptions are useful**: Add notes like "Decommissioned 2026" or "Primary production server"

## Troubleshooting

### "Please add a server configuration first"
- You need to create at least one server before creating accounts
- Go to Servers tab → Add Server

### Cannot delete server
- Server has accounts using it
- Delete all accounts first, then delete the server

### Existing accounts after migration
- All existing accounts are preserved
- Each gets its own server config automatically
- You can consolidate later if needed

## Backward Compatibility

### CLI Tool (migrate.py)
The command-line tool is NOT affected by this change. It continues to work with the old `config.json` format:

```json
{
  "source": {
    "url": "https://carbonio.example.com",
    "username": "user@example.com",
    "password": "password"
  },
  "destination": {
    "url": "https://mailcow.example.com",
    "username": "user@example.com",
    "password": "password"
  }
}
```

The CLI tool is independent and doesn't use the database.

## Summary

The server configuration feature provides:
- ✅ Better organization
- ✅ Easier multi-user management
- ✅ Cleaner separation of concerns
- ✅ Reusable server definitions
- ✅ Automatic migration of existing data
- ✅ Backward compatible CLI tool

**Start using it today**: `./start-web.sh` → Servers tab → Add Server!
