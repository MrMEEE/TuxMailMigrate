# 📚 Documentation Index

Welcome to the CalDAV Migration Tool documentation! This index will help you find the information you need.

## 🚀 Getting Started (Start Here!)

1. **[README.md](README.md)** - Main overview and CLI usage
   - Features overview
   - Installation instructions
   - CLI usage examples
   - Configuration guide

2. **[SUMMARY.md](SUMMARY.md)** - Complete project overview
   - What's been built
   - All features list
   - Quick start for both CLI and Web
   - Technical highlights

## 🌐 Web Interface

3. **[WEB_README.md](WEB_README.md)** - Complete web interface guide
   - Feature walkthrough
   - Step-by-step setup
   - API documentation
   - Production deployment tips

4. **[UI_GUIDE.md](UI_GUIDE.md)** - Visual interface guide
   - Screen layouts
   - Button functions
   - Status indicators
   - User interaction flows

## 📖 Usage & Examples

5. **[EXAMPLES.md](EXAMPLES.md)** - Practical usage examples
   - Step-by-step tutorials
   - Common scenarios
   - Troubleshooting solutions
   - Expected outputs

## 🏗️ Architecture & Design

6. **[STRUCTURE.md](STRUCTURE.md)** - Technical architecture
   - System components
   - Data flow diagrams
   - Database schema
   - Extension points

## 📂 File Reference

### Core Application Files

| File | Purpose | Documentation |
|------|---------|---------------|
| `app.py` | Flask web server & REST API | [WEB_README.md](WEB_README.md) |
| `models.py` | Database models (accounts, jobs, logs) | [STRUCTURE.md](STRUCTURE.md) |
| `worker.py` | Background job queue processor | [STRUCTURE.md](STRUCTURE.md) |
| `caldav_client.py` | CalDAV/CardDAV client wrapper | Code comments |
| `migration.py` | Core migration logic | Code comments |
| `migrate.py` | CLI migration tool | [README.md](README.md) |

### Frontend Files

| File | Purpose | Documentation |
|------|---------|---------------|
| `templates/index.html` | Web interface HTML | [UI_GUIDE.md](UI_GUIDE.md) |
| `static/app.js` | Frontend JavaScript | [UI_GUIDE.md](UI_GUIDE.md) |
| `static/style.css` | Custom styling | [UI_GUIDE.md](UI_GUIDE.md) |

### Configuration Files

| File | Purpose | Documentation |
|------|---------|---------------|
| `config.example.json` | Example CLI config | [README.md](README.md) |
| `requirements.txt` | Python dependencies (CLI) | [README.md](README.md) |
| `requirements-web.txt` | Python dependencies (Web) | [WEB_README.md](WEB_README.md) |
| `start-web.sh` | Web server startup script | [WEB_README.md](WEB_README.md) |

## 🎯 Quick Navigation by Task

### "I want to..."

#### Get Started
- **"Install and run the web interface"**
  → [WEB_README.md - Quick Start](WEB_README.md#quick-start)
  
- **"Use the command-line tool"**
  → [README.md - Usage](README.md#usage)

#### Learn Features
- **"See what this tool can do"**
  → [SUMMARY.md - Core Features](SUMMARY.md#-core-features)
  
- **"Understand the web interface"**
  → [UI_GUIDE.md](UI_GUIDE.md)

#### Follow Tutorials
- **"Migrate from Carbonio to Mailcow"**
  → [EXAMPLES.md - Example 1](EXAMPLES.md#example-1-using-the-web-interface)
  
- **"Run a one-time CLI migration"**
  → [EXAMPLES.md - Example 2](EXAMPLES.md#example-2-using-the-cli)

#### Troubleshoot Problems
- **"My connection is failing"**
  → [EXAMPLES.md - Troubleshooting](EXAMPLES.md#example-4-troubleshooting)
  
- **"Some items failed to migrate"**
  → [EXAMPLES.md - Problem: Some Items Failed](EXAMPLES.md#problem-some-items-failed-to-migrate)

#### Deploy to Production
- **"Set up for production use"**
  → [WEB_README.md - Production Deployment](WEB_README.md#production-deployment)
  
- **"Security considerations"**
  → [WEB_README.md - Security Considerations](WEB_README.md#security-considerations)

#### Understand the Code
- **"How does it work internally?"**
  → [STRUCTURE.md - Data Flow](STRUCTURE.md#data-flow)
  
- **"What's the database schema?"**
  → [STRUCTURE.md - Database Tables](STRUCTURE.md#database-tables)

#### Extend & Customize
- **"Add new features"**
  → [STRUCTURE.md - Extending the System](STRUCTURE.md#extending-the-system)
  
- **"Use the REST API"**
  → [WEB_README.md - API Endpoints](WEB_README.md#api-endpoints)

## 📊 Documentation Map

```
README.md (Start here for overview)
    ├─→ WEB_README.md (For web interface details)
    │   └─→ UI_GUIDE.md (For visual/UX details)
    │
    └─→ EXAMPLES.md (For step-by-step guides)
        └─→ Practical usage scenarios

STRUCTURE.md (For technical deep-dive)
    └─→ Architecture & design decisions

SUMMARY.md (For complete feature list)
    └─→ Quick reference & cheat sheet
```

## 🎓 Learning Path

### For End Users
1. Read [SUMMARY.md](SUMMARY.md) for overview
2. Follow [EXAMPLES.md](EXAMPLES.md) for your use case
3. Check [UI_GUIDE.md](UI_GUIDE.md) for interface help
4. Refer to [WEB_README.md](WEB_README.md) when needed

### For Developers
1. Read [STRUCTURE.md](STRUCTURE.md) for architecture
2. Review [WEB_README.md - API Endpoints](WEB_README.md#api-endpoints)
3. Study source code with inline comments
4. Check [STRUCTURE.md - Extending the System](STRUCTURE.md#extending-the-system)

### For System Administrators
1. Read [WEB_README.md - Production Deployment](WEB_README.md#production-deployment)
2. Review [WEB_README.md - Security Considerations](WEB_README.md#security-considerations)
3. Check [EXAMPLES.md - Production Use](EXAMPLES.md#example-5-production-use)
4. Set up monitoring and backups

## 🔍 Search by Keyword

### Account Management
- Adding accounts: [EXAMPLES.md](EXAMPLES.md#step-by-step-guide) | [WEB_README.md](WEB_README.md#2-add-accounts)
- Account API: [WEB_README.md](WEB_README.md#account-api)

### Sync Jobs
- Creating jobs: [EXAMPLES.md](EXAMPLES.md#3-create-a-sync-job) | [WEB_README.md](WEB_README.md#3-create-a-sync-job)
- Job control: [WEB_README.md](WEB_README.md#4-run-the-synchronization)
- Job status: [WEB_README.md](WEB_README.md#job-status-flow)

### Configuration
- CLI config: [README.md](README.md#configuration)
- Web config: [WEB_README.md](WEB_README.md#configuration)

### API
- REST endpoints: [WEB_README.md](WEB_README.md#api-endpoints)
- API usage: [STRUCTURE.md](STRUCTURE.md#api-design)

### Database
- Schema: [STRUCTURE.md](STRUCTURE.md#database-tables)
- Models: [STRUCTURE.md](STRUCTURE.md#database-choice)

### Troubleshooting
- Common issues: [EXAMPLES.md](EXAMPLES.md#example-4-troubleshooting)
- Connection problems: [README.md](README.md#troubleshooting)

### Security
- Production security: [WEB_README.md](WEB_README.md#security-considerations)
- Password handling: [SUMMARY.md](SUMMARY.md#security-considerations)

## 📞 Support Resources

### Documentation Files
- All `.md` files in project root
- Inline code comments in `.py` files
- Example configuration in `config.example.json`

### Quick Commands
```bash
# View any documentation file
cat FILENAME.md

# Search across all docs
grep -r "search term" *.md

# List all documentation
ls -la *.md
```

## 🎯 Most Common Questions

1. **How do I start?**
   → Run `./start-web.sh` and open http://localhost:5000

2. **How do I migrate from Carbonio to Mailcow?**
   → See [EXAMPLES.md - Example 1](EXAMPLES.md#example-1-using-the-web-interface)

3. **Can I test before actually migrating?**
   → Yes! Use `--dry-run` flag for CLI

4. **What if some items fail?**
   → Normal! Check logs for details. Migration continues.

5. **How do I see what's happening?**
   → Click "Logs" button in web UI or use `--verbose` in CLI

6. **Can I migrate multiple users?**
   → Yes! Add all accounts and create jobs for each pair

7. **Is it safe for production?**
   → Yes, but review [Security Considerations](WEB_README.md#security-considerations)

8. **How do I stop a running job?**
   → Click "Pause" button in web UI

9. **Where is my data stored?**
   → SQLite database: `caldav_migration.db`

10. **Can I use this with other CalDAV servers?**
    → Absolutely! Works with any standard CalDAV/CardDAV server

## 📝 Document Version History

- **2025-11-16**: Initial complete documentation set
  - All features documented
  - Web interface fully described
  - Examples and guides included
  - Architecture documented

## 🎉 You're All Set!

Choose your path:
- 🏃 **Quick Start**: [SUMMARY.md](SUMMARY.md) → Run `./start-web.sh`
- 📖 **Learn**: [EXAMPLES.md](EXAMPLES.md) → Follow step-by-step
- 🔧 **Understand**: [STRUCTURE.md](STRUCTURE.md) → Deep dive
- 🌐 **Web UI**: [WEB_README.md](WEB_README.md) → Complete guide

**Happy migrating! 🚀**
