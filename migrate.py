#!/usr/bin/env python3
"""
CalDAV/CardDAV Migration Tool - Main Script
Migrate calendars and contacts between CalDAV/CardDAV servers.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

from caldav_client import CalDAVClient
from migration import MigrationEngine


def setup_logging(verbose: bool = False):
    """
    Configure logging for the application.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Reduce noise from caldav library
    logging.getLogger('caldav').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Validate required fields
    required_fields = ['source', 'destination']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field in config: {field}")
        
        # Check server config
        for server_field in ['url', 'username', 'password']:
            if server_field not in config[field]:
                raise ValueError(f"Missing '{server_field}' in {field} configuration")
    
    return config


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Migrate calendars and contacts between CalDAV/CardDAV servers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config config.json
  %(prog)s --config config.json --dry-run
  %(prog)s --config config.json --calendars-only
  %(prog)s --config config.json --contacts-only --verbose
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry run without making changes'
    )
    
    parser.add_argument(
        '--calendars-only',
        action='store_true',
        help='Only migrate calendars (skip contacts)'
    )
    
    parser.add_argument(
        '--contacts-only',
        action='store_true',
        help='Only migrate contacts (skip calendars)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the migration tool."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config(args.config)
        
        # Apply command-line overrides
        options = config.get('options', {})
        
        if args.dry_run:
            options['dry_run'] = True
            logger.info("DRY RUN MODE - No changes will be made")
        
        if args.calendars_only:
            options['migrate_contacts'] = False
            logger.info("Calendars-only mode enabled")
        
        if args.contacts_only:
            options['migrate_calendars'] = False
            logger.info("Contacts-only mode enabled")
        
        # Initialize source client
        logger.info("\n" + "=" * 60)
        logger.info("CONNECTING TO SOURCE SERVER")
        logger.info("=" * 60)
        
        source = CalDAVClient(
            url=config['source']['url'],
            username=config['source']['username'],
            password=config['source']['password'],
            principal_path=config['source'].get('principal_path')
        )
        
        success, error_msg = source.connect()
        if not success:
            logger.error(f"Failed to connect to source server: {error_msg}")
            sys.exit(1)
        
        # Initialize destination client
        logger.info("\n" + "=" * 60)
        logger.info("CONNECTING TO DESTINATION SERVER")
        logger.info("=" * 60)
        
        destination = CalDAVClient(
            url=config['destination']['url'],
            username=config['destination']['username'],
            password=config['destination']['password'],
            principal_path=config['destination'].get('principal_path')
        )
        
        success, error_msg = destination.connect()
        if not success:
            logger.error(f"Failed to connect to destination server: {error_msg}")
            sys.exit(1)
        
        # Initialize migration engine
        logger.info("\n" + "=" * 60)
        logger.info("INITIALIZING MIGRATION ENGINE")
        logger.info("=" * 60)
        
        engine = MigrationEngine(
            source=source,
            destination=destination,
            dry_run=options.get('dry_run', False)
        )
        
        # Perform migration
        migrate_calendars = options.get('migrate_calendars', True)
        migrate_contacts = options.get('migrate_contacts', True)
        create_collections = options.get('create_collections', True)
        
        if migrate_calendars:
            engine.migrate_calendars(create_if_missing=create_collections)
        
        if migrate_contacts:
            engine.migrate_contacts(create_if_missing=create_collections)
        
        # Print final summary
        stats = engine.get_stats()
        
        logger.info("\n" + "=" * 60)
        logger.info("MIGRATION COMPLETE")
        logger.info("=" * 60)
        
        if migrate_calendars:
            logger.info(f"Calendars: {stats['calendars_migrated']} migrated, {stats['calendars_failed']} failed")
            logger.info(f"Events: {stats['events_migrated']} migrated, {stats['events_failed']} failed")
        
        if migrate_contacts:
            logger.info(f"Address Books: {stats['addressbooks_migrated']} migrated, {stats['addressbooks_failed']} failed")
            logger.info(f"Contacts: {stats['contacts_migrated']} migrated, {stats['contacts_failed']} failed")
        
        logger.info("=" * 60)
        
        # Determine exit code
        total_failed = (stats['calendars_failed'] + stats['events_failed'] + 
                       stats['addressbooks_failed'] + stats['contacts_failed'])
        
        if total_failed > 0:
            logger.warning(f"\nMigration completed with {total_failed} error(s)")
            sys.exit(1)
        else:
            logger.info("\n✓ Migration completed successfully!")
            sys.exit(0)
        
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {str(e)}")
        logger.info("\nCreate a config.json file with your server details.")
        logger.info("See config.example.json for reference.")
        sys.exit(1)
        
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        sys.exit(1)
        
    except KeyboardInterrupt:
        logger.warning("\n\nMigration interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == '__main__':
    main()
