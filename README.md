# TuxMailMigrate - CalDAV/CardDAV Migration Tool

A comprehensive web-based tool for migrating calendars and contacts between CalDAV/CardDAV servers (e.g., Carbonio → Mailcow, or any other compatible servers).

> 📚 **New to this project?** Start with **[docs/INDEX.md](docs/INDEX.md)** for complete documentation navigation!

## 🌟 Features

- **Web Interface**: Visual dashboard for managing servers, accounts, and sync jobs
- **Generic CalDAV/CardDAV support**: Works with any standard-compliant server
- **Server Presets**: Built-in configurations for Carbonio, Mailcow, Zimbra, SOGo, and Nextcloud
- **Calendar migration**: Migrates all calendars and their events
- **Contact migration**: Migrates all address books and their contacts (vCards)
- **Dry-run mode**: Test migration without making changes and get detailed statistics
- **Event filtering**: Skip specific events (e.g., "Dummy" events) during migration
- **SSL options**: Configure SSL certificate verification per server
- **Progress monitoring**: Real-time progress tracking with detailed logs
- **Queue management**: Start, pause, resume, and manage multiple sync jobs

## 🚀 Quick Start

### Installation

1. Clone the repository:
```bash
git clone git@github.com:MrMEEE/TuxMailMigrate.git
cd TuxMailMigrate
```

2. Install dependencies:
```bash
pip install -r requirements-web.txt
```

3. Start the web interface:
```bash
./scripts/start-web.sh
```

Then open http://localhost:5000 in your browser.

## 📖 Documentation

- **[docs/WEB_README.md](docs/WEB_README.md)** - Complete web interface guide
- **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)** - Step-by-step tutorial
- **[docs/SERVER_CONFIG_GUIDE.md](docs/SERVER_CONFIG_GUIDE.md)** - Server configuration reference
- **[docs/EXAMPLES.md](docs/EXAMPLES.md)** - Configuration examples

## 🔧 Server Support

Built-in presets for:
- **Carbonio** - `/dav/{username}`
- **Mailcow** - `/SOGo/dav/{username}`
- **Zimbra** - `/dav/{username}`
- **SOGo** - `/SOGo/dav/{username}`
- **Nextcloud** - `/remote.php/dav/principals/users/{username}`

Custom servers are also supported!


## 💻 CLI Usage (Alternative)

For one-time migrations, you can use the command-line interface:

```bash
python migrate.py --config config.json
```

See [docs/EXAMPLES.md](docs/EXAMPLES.md) for CLI configuration examples.

## 🛠️ Project Structure

```
├── app.py                 # Flask web application
├── caldav_client.py       # CalDAV/CardDAV client wrapper
├── migration.py           # Core migration engine
├── models.py              # Database models
├── worker.py              # Background job processor
├── migrate.py             # CLI migration tool
├── templates/             # Web interface HTML
├── static/                # CSS, JavaScript, images
├── migrations/            # Database migration scripts
├── scripts/               # Utility scripts
└── docs/                  # Documentation
```

## 📋 Requirements

- Python 3.7+
- Flask 3.0.0
- SQLAlchemy 3.1.1
- caldav 1.3.9

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📄 License

This project is open source and available for use in your migration projects.

## 🔧 Troubleshooting

### Authentication Issues
- Verify your username and password
- Some servers require app-specific passwords
- Check if your server uses basic auth or needs special headers

### Connection Issues
- Ensure the server URLs are correct (include https://)
- Try toggling SSL certificate verification in server settings
- Verify firewall/network access to both servers

### Migration Errors
- Use dry-run mode first to test connectivity and get statistics
- Check the sync logs for detailed error messages
- Verify that your source account has read access to calendars/contacts

- Some events/contacts may fail if they contain invalid data

## License

MIT License - feel free to use and modify as needed.
