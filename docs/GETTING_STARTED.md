# 🚀 Getting Started with CalDAV Migration Tool

Welcome! This guide will get you up and running in 5 minutes.

## 🎯 What You Have

A complete CalDAV/CardDAV migration system with:
- ✅ Beautiful web interface with real-time monitoring
- ✅ Command-line tool for automation
- ✅ Support for ANY CalDAV/CardDAV server
- ✅ Queue system for multiple migrations
- ✅ Detailed logging and statistics
- ✅ SQLite database for persistence

## ⚡ 5-Minute Quick Start

### Step 1: Start the Web Interface

```bash
cd /home/mj/Hentet/mailcow/caldav-migration
./start-web.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Start the web server

### Step 2: Open Your Browser

Go to: **http://localhost:5000**

### Step 3: Add Your Accounts

Click **"Add Account"** and enter:

**Source Server (e.g., Carbonio):**
- Name: `Carbonio`
- URL: `https://carbonio.example.com`
- Username: `your@email.com`
- Password: `your-password`

**Destination Server (e.g., Mailcow):**
- Name: `Mailcow`
- URL: `https://mailcow.example.com`
- Username: `your@email.com`
- Password: `your-password`

### Step 4: Create a Sync Job

1. Switch to **"Synchronizations"** tab
2. Click **"New Sync Job"**
3. Fill in:
   - Name: `Carbonio to Mailcow`
   - Source: Select `Carbonio`
   - Destination: Select `Mailcow`
   - Check all options ✓

### Step 5: Start Migration

Click **"Start"** and watch it work! 🎉

## 📊 What You'll See

```
┌─────────────────────────────────────────┐
│ Carbonio to Mailcow    🔵 RUNNING      │
│ ████████████░░░░░░░░░░░░ 45%           │
│                                         │
│ [⏸️ Pause] [📄 Logs]                    │
└─────────────────────────────────────────┘
```

Click **"Logs"** to see real-time progress!

## 🎓 Next Steps

### Learn More
- **[EXAMPLES.md](EXAMPLES.md)** - Detailed tutorials
- **[WEB_README.md](WEB_README.md)** - Complete web guide
- **[INDEX.md](INDEX.md)** - Full documentation index

### Use Command Line
```bash
cp config.example.json config.json
# Edit config.json with your credentials
./migrate.py --config config.json --dry-run
./migrate.py --config config.json
```

### View Project Structure
```bash
./show-project.sh
```

## 🆘 Need Help?

### Common Issues

**Port 5000 already in use?**
```bash
# Edit app.py and change port to 5001
```

**Authentication failing?**
- Check URL includes `https://`
- Verify username/password
- Test with `--dry-run` first

**Can't see calendars?**
- Leave Principal Path empty
- Check account in original client
- Use `--verbose` for details

### Documentation

- **Quick questions**: Check [SUMMARY.md](SUMMARY.md)
- **Step-by-step**: Follow [EXAMPLES.md](EXAMPLES.md)
- **Technical details**: Read [STRUCTURE.md](STRUCTURE.md)
- **Everything**: Start with [INDEX.md](INDEX.md)

## ✨ Features Overview

### Web Interface
- 👥 Manage multiple accounts
- 🔄 Queue sync jobs
- ▶️ Start/Pause/Resume
- 📊 Real-time progress
- 📝 Detailed logs
- 💾 Persistent storage

### Migration
- 📅 Calendars + Events
- 👤 Contacts (vCards)
- 📦 Auto-create collections
- 🔄 Continue on errors
- 📈 Statistics tracking
- 🎯 Selective migration

## 🎉 You're Ready!

Start migrating your CalDAV data now:

```bash
./start-web.sh
```

Then open **http://localhost:5000** and begin! 🚀

---

**Happy Migrating!** For complete documentation, see [INDEX.md](INDEX.md)
