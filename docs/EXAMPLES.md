# Quick Start Examples

## Example 1: Using the Web Interface

### Step-by-Step Guide

1. **Start the web interface:**
   ```bash
   cd /home/mj/Hentet/mailcow/caldav-migration
   ./start-web.sh
   ```

2. **Open browser to http://localhost:5000**

3. **Add your Carbonio (source) account:**
   - Click "Add Account"
   - Name: `Carbonio Production`
   - URL: `https://carbonio.example.com`
   - Username: `user@example.com`
   - Password: `your-password`
   - Click "Add Account"

4. **Add your Mailcow (destination) account:**
   - Click "Add Account"
   - Name: `Mailcow Server`
   - URL: `https://mailcow.example.com`
   - Username: `user@example.com`
   - Password: `your-password`
   - Click "Add Account"

5. **Create a sync job:**
   - Switch to "Synchronizations" tab
   - Click "New Sync Job"
   - Name: `Carbonio to Mailcow Migration`
   - Source: `Carbonio Production`
   - Destination: `Mailcow Server`
   - Check all options (Calendars, Contacts, Create Collections)
   - Click "Create Job"

6. **Start the migration:**
   - Click the "Start" button on your job
   - Watch the progress bar
   - Click "Logs" to see detailed progress
   - Wait for completion

## Example 2: Using the CLI

### One-Time Migration

1. **Create configuration file:**
   ```bash
   cp config.example.json config.json
   ```

2. **Edit config.json:**
   ```json
   {
     "source": {
       "url": "https://carbonio.example.com",
       "username": "user@example.com",
       "password": "carbonio-password",
       "principal_path": null
     },
     "destination": {
       "url": "https://mailcow.example.com",
       "username": "user@example.com",
       "password": "mailcow-password",
       "principal_path": null
     },
     "options": {
       "migrate_calendars": true,
       "migrate_contacts": true,
       "dry_run": false,
       "create_collections": true
     }
   }
   ```

3. **Test with dry-run:**
   ```bash
   ./migrate.py --config config.json --dry-run
   ```

4. **Run the migration:**
   ```bash
   ./migrate.py --config config.json
   ```

## Example 3: Common Scenarios

### Scenario A: Calendars Only (No Contacts)

**Web Interface:**
- Uncheck "Migrate Contacts" when creating sync job

**CLI:**
```bash
./migrate.py --config config.json --calendars-only
```

### Scenario B: Contacts Only (No Calendars)

**Web Interface:**
- Uncheck "Migrate Calendars" when creating sync job

**CLI:**
```bash
./migrate.py --config config.json --contacts-only
```

### Scenario C: Multiple Users Migration

**Web Interface:**
1. Add accounts for User 1 (source and destination)
2. Create sync job for User 1
3. Add accounts for User 2 (source and destination)
4. Create sync job for User 2
5. Start both jobs (they'll process sequentially)

### Scenario D: Test Before Migrating

**Always recommended!**

1. **Check connectivity:**
   ```bash
   ./migrate.py --config config.json --dry-run --verbose
   ```

2. **Review what will be migrated:**
   - Look at the output for calendar and contact counts
   - Verify the collections are detected correctly

3. **Run actual migration:**
   ```bash
   ./migrate.py --config config.json
   ```

## Example 4: Troubleshooting

### Problem: Authentication Failed

**Check:**
- URL is correct (include https://)
- Username is complete (include @domain if needed)
- Password is correct
- Server is accessible from your network

**Test manually:**
```bash
curl -u "user@example.com:password" https://carbonio.example.com/dav/
```

### Problem: No Calendars/Contacts Found

**Possible causes:**
- Principal path is incorrect
- Account doesn't have any calendars/contacts
- Permissions issue on the server

**Solution:**
- Try leaving principal_path empty for auto-discovery
- Check account in original client to verify data exists
- Use `--verbose` flag for more details

### Problem: Migration Stops/Hangs

**Web Interface:**
- Check browser console for errors
- Check terminal where Flask is running for Python errors
- Look at job logs in the UI

**CLI:**
- Run with `--verbose` for detailed output
- Check network connection
- Look for specific error messages in output

### Problem: Some Items Failed to Migrate

**This is normal!**
- Some events/contacts may have invalid data
- Server incompatibilities
- The migration continues despite individual failures

**Check:**
- Look at the statistics at the end
- Review failed item count
- Check logs for specific errors
- Failed items usually have minor issues that can be manually fixed

## Example 5: Production Use

### For Regular Backups

**Using Web Interface:**
1. Create accounts for source and backup destination
2. Create sync job named "Daily Backup"
3. Use curl to trigger via cron:
   ```bash
   # Add to crontab
   0 2 * * * curl -X POST http://localhost:5000/api/sync-jobs/1/start
   ```

### For Server Migration

**Recommended approach:**

1. **Week before migration:**
   - Set up both accounts in web interface
   - Run test migration with dry-run
   - Verify all calendars/contacts are detected

2. **Day before migration:**
   - Run actual migration to sync most data
   - Keep old server running

3. **Migration day:**
   - Run migration again to catch any new/updated items
   - Switch over to new server
   - Run one final migration to catch any last changes

4. **After migration:**
   - Verify data in new server
   - Keep old server running for a few days as backup
   - Monitor for any issues

### For Multiple Servers

**Managing many migrations:**

1. Add all source and destination accounts
2. Create sync jobs for each pair
3. Use naming convention: `[User] Source → Dest`
4. Queue all jobs at once
5. Monitor progress from dashboard

## Expected Output Examples

### Successful Migration (CLI)

```
2025-11-16 10:30:15 - INFO - Loading configuration...
2025-11-16 10:30:15 - INFO - Connecting to https://carbonio.example.com...
2025-11-16 10:30:16 - INFO - Successfully connected
2025-11-16 10:30:16 - INFO - Connecting to https://mailcow.example.com...
2025-11-16 10:30:17 - INFO - Successfully connected
============================================================
Starting calendar migration...
============================================================
2025-11-16 10:30:18 - INFO - Found 3 calendar(s)

Processing calendar: 'Personal'
  Found 42 events
  ✓ Migrated 42 event(s) to 'Personal'

Processing calendar: 'Work'
  Found 128 events
  ✓ Migrated 128 event(s) to 'Work'

============================================================
Calendar Migration Summary:
  Calendars migrated: 3
  Calendars failed: 0
  Events migrated: 170
  Events failed: 0
============================================================

============================================================
MIGRATION COMPLETE
============================================================
✓ Migration completed successfully!
```

### Web Interface - Job Status

**Running:**
- Blue progress bar animating
- Status: RUNNING
- Progress: 45%
- Worker indicator: Green pulsing

**Completed:**
- Status: COMPLETED (green badge)
- Stats showing:
  - Calendars: 3/3
  - Events: 170/170
  - Contacts: 45/45
- Logs available for review

## Tips & Best Practices

1. **Always test with dry-run first**
2. **Start with small test account before migrating large ones**
3. **Keep the old server available for a few days**
4. **Document your account credentials securely**
5. **Monitor the first few migrations closely**
6. **Use verbose logging when troubleshooting**
7. **Back up your database file regularly** (`caldav_migration.db`)
8. **Check the destination server after migration**
9. **For large migrations, expect it to take time**
10. **If migration fails, check logs and try again**
