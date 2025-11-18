"""
Migration logic for calendars and contacts.
"""

import logging
import uuid
import re
from typing import Dict, Any, Optional, List
from caldav_client import CalDAVClient
import caldav


class MigrationEngine:
    """Core migration engine for CalDAV/CardDAV data."""
    
    def __init__(self, source: CalDAVClient, destination: CalDAVClient, dry_run: bool = False, skip_dummy_events: bool = False, progress_callback=None, selected_calendars: List[str] = None, selected_addressbooks: List[str] = None, calendar_mapping: dict = None, addressbook_mapping: dict = None):
        """
        Initialize migration engine.
        
        Args:
            source: Source CalDAV client
            destination: Destination CalDAV client
            dry_run: If True, only simulate migration without making changes
            skip_dummy_events: If True, skip events with summary "Dummy"
            selected_calendars: List of calendar names to migrate (None = all)
            selected_addressbooks: List of addressbook names to migrate (None = all)
            calendar_mapping: Dict mapping source calendar names to destination names (None = use same name)
            addressbook_mapping: Dict mapping source addressbook names to destination names (None = use same name)
        """
        self.source = source
        self.destination = destination
        self.dry_run = dry_run
        self.skip_dummy_events = skip_dummy_events
        self.selected_calendars = selected_calendars
        self.selected_addressbooks = selected_addressbooks
        self.calendar_mapping = calendar_mapping or {}
        self.addressbook_mapping = addressbook_mapping or {}
        # Optional callback to report progress while migrating. Called with a dict payload:
        # { 'stage': 'calendars'|'contacts', 'processed': int, 'total': int, 'skipped': int }
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.stats = {
            'calendars_migrated': 0,
            'calendars_failed': 0,
            'events_migrated': 0,
            'events_failed': 0,
            'events_skipped': 0,
            'addressbooks_migrated': 0,
            'addressbooks_failed': 0,
            'contacts_migrated': 0,
            'contacts_failed': 0,
            'contacts_skipped': 0,
        }
        
        # Detailed dry-run information
        self.dry_run_details = {
            'calendars': [],  # List of {name, event_count, url}
            'addressbooks': []  # List of {name, contact_count, url}
        }
    
    def migrate_calendars(self, create_if_missing: bool = True) -> Dict[str, Any]:
        """
        Migrate all calendars and their events.
        
        Args:
            create_if_missing: Create calendars on destination if they don't exist
            
        Returns:
            Dictionary with migration statistics
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting calendar migration...")
        self.logger.info("=" * 60)
        
        source_calendars = self.source.get_calendars()
        
        if not source_calendars:
            self.logger.warning("No calendars found on source server")
            return self.stats
        
        # Filter calendars if selective sync is enabled
        if self.selected_calendars is not None:
            if len(self.selected_calendars) == 0:
                self.logger.info("Selective sync enabled: 0 calendars selected - skipping all calendars")
                return self.stats
            
            self.logger.info(f"Selective sync enabled: {len(self.selected_calendars)} calendar(s) selected")
            filtered_calendars = []
            for cal in source_calendars:
                props = cal.get_properties([caldav.dav.DisplayName()])
                cal_name = props.get('{DAV:}displayname', 'Unnamed Calendar')
                if cal_name in self.selected_calendars:
                    filtered_calendars.append(cal)
                else:
                    self.logger.info(f"Skipping calendar '{cal_name}' (not selected)")
            source_calendars = filtered_calendars
            self.logger.info(f"Processing {len(source_calendars)} selected calendar(s)")
        
        if not source_calendars:
            self.logger.warning("No calendars to migrate after filtering")
            return self.stats
        
        for src_calendar in source_calendars:
            try:
                # Get calendar properties
                props = src_calendar.get_properties([caldav.dav.DisplayName()])
                calendar_name = props.get('{DAV:}displayname', 'Unnamed Calendar')
                
                self.logger.info(f"\nProcessing calendar: '{calendar_name}'")
                
                # Apply mapping if configured
                dest_calendar_name = self.calendar_mapping.get(calendar_name, calendar_name)
                if dest_calendar_name != calendar_name:
                    self.logger.info(f"  🗺️ Mapping '{calendar_name}' → '{dest_calendar_name}'")
                
                # Get or create destination calendar using mapped name
                dest_calendar = self.destination.get_calendar_by_name(dest_calendar_name)
                
                if not dest_calendar:
                    if create_if_missing:
                        if self.dry_run:
                            self.logger.info(f"  [DRY RUN] Would create calendar: '{dest_calendar_name}'")
                            # Still process events to count them
                            events = src_calendar.events()
                            event_count = len(events)
                            
                            # Count Dummy events if skip_dummy_events is enabled
                            dummy_count = 0
                            if self.skip_dummy_events:
                                for event in events:
                                    try:
                                        if hasattr(event, 'instance') and hasattr(event.instance, 'vevent'):
                                            summary = event.instance.vevent.summary.value if hasattr(event.instance.vevent, 'summary') else ""
                                            if summary and summary.strip().lower() == "dummy":
                                                dummy_count += 1
                                    except:
                                        pass
                            
                            self.dry_run_details['calendars'].append({
                                'name': dest_calendar_name,
                                'event_count': event_count,
                                'dummy_count': dummy_count,
                                'url': str(src_calendar.url)
                            })
                            if dummy_count > 0:
                                self.logger.info(f"  [DRY RUN] Found {event_count} event(s), {dummy_count} 'Dummy' event(s) would be skipped")
                            else:
                                self.logger.info(f"  [DRY RUN] Found {event_count} event(s) in '{calendar_name}'")
                            self.stats['calendars_migrated'] += 1
                            continue
                        else:
                            self.logger.info(f"  Creating calendar: '{dest_calendar_name}'")
                            dest_calendar = self.destination.create_calendar(dest_calendar_name)
                            if not dest_calendar:
                                self.logger.error(f"  Failed to create calendar: '{dest_calendar_name}'")
                                self.stats['calendars_failed'] += 1
                                continue
                    else:
                        self.logger.warning(f"  Calendar '{calendar_name}' not found on destination (skipping)")
                        self.stats['calendars_failed'] += 1
                        continue
                
                # Migrate events
                self._migrate_calendar_events(src_calendar, dest_calendar, calendar_name)
                self.stats['calendars_migrated'] += 1
                
            except Exception as e:
                self.logger.error(f"  Error processing calendar: {str(e)}")
                self.stats['calendars_failed'] += 1
        
        self._log_calendar_stats()
        return self.stats
    
    def _migrate_calendar_events(self, src_calendar, dest_calendar, calendar_name: str):
        """
        Migrate all events from source calendar to destination calendar.
        
        Args:
            src_calendar: Source calendar object
            dest_calendar: Destination calendar object
            calendar_name: Name of the calendar (for logging)
        """
        try:
            events = src_calendar.events()
            event_count = len(events)
            self.logger.info(f"  Found {event_count} event(s)")
            
            # In dry-run mode, just count and store details
            if self.dry_run:
                props = src_calendar.get_properties([caldav.dav.DisplayName()])
                cal_name = props.get('{DAV:}displayname', 'Unnamed Calendar')
                
                # Count Dummy events if skip_dummy_events is enabled
                dummy_count = 0
                if self.skip_dummy_events:
                    for event in events:
                        try:
                            if hasattr(event, 'instance') and hasattr(event.instance, 'vevent'):
                                summary = event.instance.vevent.summary.value if hasattr(event.instance.vevent, 'summary') else ""
                                if summary and summary.strip().lower() == "dummy":
                                    dummy_count += 1
                        except:
                            pass
                
                self.dry_run_details['calendars'].append({
                    'name': cal_name,
                    'event_count': event_count,
                    'dummy_count': dummy_count,
                    'url': str(src_calendar.url)
                })
                if dummy_count > 0:
                    self.logger.info(f"  [DRY RUN] Found {event_count} event(s), {dummy_count} 'Dummy' event(s) would be skipped")
                else:
                    self.logger.info(f"  [DRY RUN] Would migrate {event_count} event(s)")
                return
            
            # Get existing events in destination calendar to check for duplicates
            existing_uids = set()
            try:
                dest_events = dest_calendar.events()
                for dest_event in dest_events:
                    try:
                        if hasattr(dest_event, 'instance') and hasattr(dest_event.instance, 'vevent'):
                            uid = dest_event.instance.vevent.uid.value
                            existing_uids.add(uid)
                    except:
                        pass
                self.logger.debug(f"  Found {len(existing_uids)} existing event(s) in destination calendar")
            except Exception as e:
                self.logger.debug(f"  Could not retrieve existing events: {e}")
            
            processed = 0
            for idx, event in enumerate(events, 1):
                try:
                    # Get event data (iCalendar format)
                    event_data = event.data
                    event_uid = event.instance.vevent.uid.value if hasattr(event, 'instance') and hasattr(event.instance, 'vevent') else None
                    
                    # Check for duplicate by UID
                    if event_uid and event_uid in existing_uids:
                        self.logger.debug(f"    [{idx}/{event_count}] Skipping duplicate event: {event_uid}")
                        self.stats['events_skipped'] += 1
                        processed += 1
                        # report progress
                        if self.progress_callback:
                            try:
                                self.progress_callback({'stage': 'calendars', 'processed': processed, 'total': event_count, 'skipped': self.stats['events_skipped']})
                            except Exception:
                                pass
                        continue
                    
                    # Check if we should skip this event
                    if self.skip_dummy_events:
                        try:
                            # Parse the event to get the summary
                            if hasattr(event, 'instance') and hasattr(event.instance, 'vevent'):
                                summary = event.instance.vevent.summary.value if hasattr(event.instance.vevent, 'summary') else ""
                                if summary and summary.strip().lower() == "dummy":
                                    self.logger.debug(f"    [{idx}/{event_count}] Skipping event with summary 'Dummy'")
                                    self.stats['events_skipped'] += 1
                                    continue
                        except:
                            pass  # If we can't parse, don't skip
                    
                    # Add event to destination calendar
                    dest_calendar.save_event(event_data)
                    self.logger.debug(f"    [{idx}/{event_count}] Migrated event: {event_uid or f'event_{idx}'}")
                    self.stats['events_migrated'] += 1
                    processed += 1
                    # report progress
                    if self.progress_callback:
                        try:
                            self.progress_callback({'stage': 'calendars', 'processed': processed, 'total': event_count, 'skipped': self.stats['events_skipped']})
                        except Exception:
                            pass
                    
                except Exception as e:
                    self.logger.warning(f"    [{idx}/{event_count}] Failed to migrate event: {str(e)}")
                    self.stats['events_failed'] += 1
                    processed += 1
                    if self.progress_callback:
                        try:
                            self.progress_callback({'stage': 'calendars', 'processed': processed, 'total': event_count, 'skipped': self.stats['events_skipped']})
                        except Exception:
                            pass
            
            if self.skip_dummy_events and self.stats['events_skipped'] > 0:
                self.logger.info(f"  ⏭  Skipped {self.stats['events_skipped']} 'Dummy' event(s)")
            self.logger.info(f"  ✓ Migrated {self.stats['events_migrated']} event(s) to '{dest_calendar_name}'")
                
        except Exception as e:
            self.logger.error(f"  Failed to retrieve events: {str(e)}")
    
    def migrate_contacts(self, create_if_missing: bool = True) -> Dict[str, Any]:
        """
        Migrate all address books and their contacts.
        
        Args:
            create_if_missing: Create address books on destination if they don't exist
            
        Returns:
            Dictionary with migration statistics
        """
        self.logger.info("\n" + "=" * 60)
        self.logger.info("Starting contact migration...")
        self.logger.info("=" * 60)
        
        # Check if addressbooks are selected BEFORE retrieving them
        if self.selected_addressbooks is not None:
            if len(self.selected_addressbooks) == 0:
                self.logger.info("Selective sync enabled: 0 addressbooks selected - skipping all addressbooks")
                return self.stats
        
        source_addressbooks = self.source.get_addressbooks()
        
        if not source_addressbooks:
            self.logger.warning("No address books found on source server")
            return self.stats
        
        # Filter addressbooks if selective sync is enabled
        if self.selected_addressbooks is not None:
            self.logger.info(f"Selective sync enabled: {len(self.selected_addressbooks)} addressbook(s) selected")
            filtered_addressbooks = []
            for ab in source_addressbooks:
                props = ab.get_properties([caldav.dav.DisplayName()])
                ab_name = props.get('{DAV:}displayname', 'Unnamed Address Book')
                if ab_name in self.selected_addressbooks:
                    filtered_addressbooks.append(ab)
                else:
                    self.logger.info(f"Skipping addressbook '{ab_name}' (not selected)")
            source_addressbooks = filtered_addressbooks
            self.logger.info(f"Processing {len(source_addressbooks)} selected addressbook(s)")
        
        if not source_addressbooks:
            self.logger.warning("No addressbooks to migrate after filtering")
            return self.stats
        
        for src_addressbook in source_addressbooks:
            try:
                # Get address book properties
                props = src_addressbook.get_properties([caldav.dav.DisplayName()])
                addressbook_name = props.get('{DAV:}displayname', 'Unnamed Address Book')
                
                self.logger.info(f"\nProcessing address book: '{addressbook_name}'")
                
                # Apply mapping if configured
                dest_addressbook_name = self.addressbook_mapping.get(addressbook_name, addressbook_name)
                if dest_addressbook_name != addressbook_name:
                    self.logger.info(f"  🗺️ Mapping '{addressbook_name}' → '{dest_addressbook_name}'")
                
                # Get or create destination address book using mapped name
                dest_addressbook = self.destination.get_addressbook_by_name(dest_addressbook_name)
                
                if not dest_addressbook:
                    if create_if_missing:
                        if self.dry_run:
                            self.logger.info(f"  [DRY RUN] Would create address book: '{dest_addressbook_name}'")
                            # Still process contacts to count them
                            contact_count = 0
                            try:
                                # For Carbonio/CardDAV, try PROPFIND to list children first
                                self.logger.info(f"  Trying PROPFIND to list contacts...")
                                propfind_body = '''<?xml version="1.0" encoding="utf-8" ?>
                                <d:propfind xmlns:d="DAV:">
                                  <d:prop>
                                    <d:getetag/>
                                    <d:getcontenttype/>
                                  </d:prop>
                                </d:propfind>'''
                                
                                try:
                                    response = self.source.client.request(
                                        url=str(src_addressbook.url),
                                        method='PROPFIND',
                                        headers={'Depth': '1', 'Content-Type': 'application/xml; charset=utf-8'},
                                        body=propfind_body
                                    )
                                    
                                    # Parse response to count vCard files
                                    import xml.etree.ElementTree as ET
                                    response_text = response.raw if isinstance(response.raw, str) else response.raw.decode('utf-8')
                                    root = ET.fromstring(response_text)
                                    ns = {'d': 'DAV:'}
                                    
                                    # Count responses with text/vcard content type
                                    contact_count = 0
                                    for resp in root.findall('.//d:response', ns):
                                        contenttype = resp.find('.//d:getcontenttype', ns)
                                        if contenttype is not None and contenttype.text and 'vcard' in contenttype.text.lower():
                                            contact_count += 1
                                    
                                    self.logger.info(f"  PROPFIND returned {contact_count} contacts")
                                except Exception as e_propfind:
                                    self.logger.info(f"  PROPFIND method failed: {e_propfind}")
                                    # Fallback to other methods
                                    try:
                                        contacts = src_addressbook.objects()
                                        contact_count = len(contacts)
                                        self.logger.info(f"  objects() returned {contact_count} contacts")
                                    except Exception as e1:
                                        self.logger.info(f"  objects() failed: {e1}")
                                        try:
                                            contacts = list(src_addressbook.search(comp_class="VCARD"))
                                            contact_count = len(contacts)
                                            self.logger.info(f"  search(comp_class='VCARD') returned {contact_count} contacts")
                                        except Exception as e2:
                                            self.logger.info(f"  search(comp_class='VCARD') failed: {e2}")
                                            try:
                                                result = src_addressbook.objects_by_sync_token()
                                                contacts = result[1] if isinstance(result, tuple) else result
                                                contact_count = len(contacts) if contacts else 0
                                                self.logger.info(f"  objects_by_sync_token() returned {contact_count} contacts")
                                            except Exception as e3:
                                                self.logger.warning(f"  All contact retrieval methods failed: PROPFIND={e_propfind}, objects()={e1}, search()={e2}, sync_token()={e3}")
                                                contact_count = 0
                            except Exception as e:
                                self.logger.warning(f"  Could not count contacts in '{addressbook_name}': {e}")
                                contact_count = 0
                            self.dry_run_details['addressbooks'].append({
                                'name': dest_addressbook_name,
                                'contact_count': contact_count,
                                'url': str(src_addressbook.url)
                            })
                            self.logger.info(f"  [DRY RUN] Found {contact_count} contact(s) in '{addressbook_name}'")
                            self.stats['addressbooks_migrated'] += 1
                            continue
                        else:
                            # Real migration - try to find or create addressbook
                            self.logger.info(f"  Looking for address book: '{dest_addressbook_name}' on destination")
                            dest_addressbook = self.destination.find_addressbook(dest_addressbook_name)
                            if not dest_addressbook:
                                if create_if_missing:
                                    self.logger.info(f"  Address book '{dest_addressbook_name}' not found, attempting to create it...")
                                    dest_addressbook = self.destination.create_addressbook(dest_addressbook_name)
                                    if not dest_addressbook:
                                        self.logger.error(f"  ✗ Failed to create address book '{dest_addressbook_name}'")
                                        self.logger.warning(f"  SOGo may not support creating addressbooks via CardDAV API")
                                        self.logger.warning(f"  Skipping this addressbook. Please create it manually in SOGo.")
                                        self.stats['addressbooks_failed'] += 1
                                        continue
                                    else:
                                        self.logger.info(f"  ✓ Successfully created address book '{dest_addressbook_name}'")
                                else:
                                    # create_if_missing is False - skip this addressbook
                                    self.logger.warning(f"  Address book '{dest_addressbook_name}' not found on destination")
                                    self.logger.warning(f"  Skipping (create_if_missing=False)")
                                    self.stats['addressbooks_failed'] += 1
                                    continue
                            else:
                                self.logger.info(f"  ✓ Found existing address book '{dest_addressbook_name}' on destination")
                else:
                    # create_if_missing is False and addressbook doesn't exist
                    if not dest_addressbook:
                        self.logger.warning(f"  Address book '{dest_addressbook_name}' not found (create_if_missing=False)")
                        self.stats['addressbooks_failed'] += 1
                        continue
                    else:
                        # Addressbook found on destination
                        self.logger.info(f"  Found address book '{dest_addressbook_name}' on destination")
                
                # Migrate contacts
                self._migrate_addressbook_contacts(src_addressbook, dest_addressbook, addressbook_name)
                self.stats['addressbooks_migrated'] += 1
                
            except Exception as e:
                self.logger.error(f"  Error processing address book: {str(e)}")
                self.stats['addressbooks_failed'] += 1
        
        self._log_contact_stats()
        return self.stats
    
    def _migrate_addressbook_contacts(self, src_addressbook, dest_addressbook, addressbook_name: str):
        """
        Migrate all contacts from source address book to destination.
        
        Args:
            src_addressbook: Source address book object
            dest_addressbook: Destination address book object
            addressbook_name: Name of the address book (for logging)
        """
        try:
            # Get all contacts (vCards) - use PROPFIND which works reliably for Carbonio
            contacts = []
            try:
                # Use PROPFIND to list all vCard resources
                import xml.etree.ElementTree as ET
                propfind_body = '''<?xml version="1.0" encoding="utf-8" ?>
                <d:propfind xmlns:d="DAV:">
                  <d:prop>
                    <d:getetag/>
                    <d:getcontenttype/>
                  </d:prop>
                </d:propfind>'''
                
                response = self.source.client.request(
                    url=str(src_addressbook.url),
                    method='PROPFIND',
                    headers={'Depth': '1', 'Content-Type': 'application/xml; charset=utf-8'},
                    body=propfind_body
                )
                
                # Parse response to get vCard URLs
                response_text = response.raw if isinstance(response.raw, str) else response.raw.decode('utf-8')
                root = ET.fromstring(response_text)
                ns = {'d': 'DAV:'}
                
                # Find all resources with content-type text/vcard
                for response_elem in root.findall('.//d:response', ns):
                    contenttype = response_elem.find('.//d:getcontenttype', ns)
                    if contenttype is not None and contenttype.text and 'vcard' in contenttype.text.lower():
                        href = response_elem.find('.//d:href', ns)
                        if href is not None and href.text:
                            # Create a simple object to hold the vCard URL
                            class VCardRef:
                                def __init__(self, url, parent_client):
                                    self.url = url
                                    self.client = parent_client
                                    self._data = None
                                    self._instance = None
                                
                                @property
                                def data(self):
                                    if self._data is None:
                                        # Fetch the vCard data
                                        resp = self.client.request(url=self.url, method='GET')
                                        self._data = resp.raw if isinstance(resp.raw, str) else resp.raw.decode('utf-8')
                                    return self._data
                                
                                @property
                                def instance(self):
                                    if self._instance is None:
                                        try:
                                            import vobject
                                            self._instance = vobject.readOne(self.data)
                                        except:
                                            pass
                                    return self._instance
                            
                            vcard_url = href.text
                            if not vcard_url.startswith('http'):
                                from urllib.parse import urljoin
                                vcard_url = urljoin(str(src_addressbook.url), vcard_url)
                            
                            contacts.append(VCardRef(vcard_url, self.source.client))
                
                self.logger.info(f"  PROPFIND returned {len(contacts)} contacts")
            except Exception as e_propfind:
                self.logger.warning(f"  PROPFIND failed: {e_propfind}, trying caldav library methods...")
                # Fallback to standard caldav methods
                try:
                    contacts = src_addressbook.objects()
                except Exception as e1:
                    try:
                        contacts = list(src_addressbook.search(comp_class="VCARD"))
                    except Exception as e2:
                        try:
                            result = src_addressbook.objects_by_sync_token()
                            contacts = result[1] if isinstance(result, tuple) else result
                            contacts = contacts if contacts else []
                        except Exception as e3:
                            self.logger.warning(f"  All contact retrieval methods failed: PROPFIND={e_propfind}, objects()={e1}, search()={e2}, sync_token()={e3}")
                            contacts = []
            
            contact_count = len(contacts)
            self.logger.info(f"  Found {contact_count} contact(s)")
            
            # In dry-run mode, just count and store details
            if self.dry_run:
                props = src_addressbook.get_properties([caldav.dav.DisplayName()])
                ab_name = props.get('{DAV:}displayname', 'Unnamed Address Book')
                self.dry_run_details['addressbooks'].append({
                    'name': ab_name,
                    'contact_count': contact_count,
                    'url': str(src_addressbook.url)
                })
                self.logger.info(f"  [DRY RUN] Would migrate {contact_count} contact(s)")
                return
            
            # Get existing contacts in destination addressbook to check for duplicates
            existing_uids = set()
            try:
                dest_contacts = dest_addressbook.objects()
                for dest_contact in dest_contacts:
                    try:
                        if hasattr(dest_contact, 'instance') and hasattr(dest_contact.instance, 'uid'):
                            uid = dest_contact.instance.uid.value
                            existing_uids.add(uid)
                    except:
                        pass
                self.logger.debug(f"  Found {len(existing_uids)} existing contact(s) in destination address book")
            except Exception as e:
                self.logger.debug(f"  Could not retrieve existing contacts: {e}")
            
            processed = 0
            for idx, contact in enumerate(contacts, 1):
                try:
                    # Get contact data (vCard format)
                    contact_data = contact.data
                    contact_name = "Unknown"
                    contact_uid = None
                    
                    # Try to extract name and UID for better logging and duplicate detection
                    try:
                        if hasattr(contact, 'instance'):
                            if hasattr(contact.instance, 'fn'):
                                contact_name = contact.instance.fn.value
                            if hasattr(contact.instance, 'uid'):
                                contact_uid = contact.instance.uid.value
                    except:
                        pass
                    
                    # Check for duplicate by UID
                    if contact_uid and contact_uid in existing_uids:
                        self.logger.debug(f"    [{idx}/{contact_count}] Skipping duplicate contact: {contact_name}")
                        self.stats['contacts_skipped'] += 1
                        processed += 1
                        if self.progress_callback:
                            try:
                                self.progress_callback({'stage': 'contacts', 'processed': processed, 'total': contact_count, 'skipped': self.stats['contacts_skipped']})
                            except Exception:
                                pass
                        continue
                    
                    # Add contact to destination address book
                    # SOGo requires PUT to /Contacts/personal/{uid}.vcf (not just /Contacts/{uid}.vcf)
                    try:
                        # Get the addressbook URL
                        addressbook_url = str(dest_addressbook.url).rstrip('/')
                        
                        # Extract UID from vCard
                        vcard_uid = contact.uid.value if hasattr(contact, 'uid') and hasattr(contact.uid, 'value') else None
                        if not vcard_uid:
                            uid_match = re.search(r'UID:([^\r\n]+)', contact_data)
                            vcard_uid = uid_match.group(1) if uid_match else str(uuid.uuid4())
                        
                        # Create safe filename from UID
                        safe_uid = vcard_uid.replace(':', '_').replace('/', '_')
                        
                        # SOGo requires /Contacts/personal/ path (not just /Contacts/)
                        # If URL ends with /Contacts, append /personal
                        if addressbook_url.endswith('/Contacts'):
                            vcard_url = f"{addressbook_url}/personal/{safe_uid}.vcf"
                        else:
                            vcard_url = f"{addressbook_url}/{safe_uid}.vcf"
                        
                        # PUT request with vCard data
                        import requests
                        response = requests.put(
                            vcard_url,
                            data=contact_data.encode('utf-8'),
                            headers={'Content-Type': 'text/vcard; charset=utf-8'},
                            auth=(self.destination.username, self.destination.password),
                            verify=False
                        )
                        
                        if response.status_code in (200, 201, 204):
                            self.logger.debug(f"    [{idx}/{contact_count}] Migrated contact: {contact_name} (status: {response.status_code})")
                        else:
                            raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")
                    except Exception as save_err:
                        raise Exception(f"Failed to save contact: {str(save_err)}")
                    self.stats['contacts_migrated'] += 1
                    processed += 1
                    if self.progress_callback:
                        try:
                            self.progress_callback({'stage': 'contacts', 'processed': processed, 'total': contact_count, 'skipped': self.stats['contacts_skipped']})
                        except Exception:
                            pass
                    
                except Exception as e:
                    self.logger.warning(f"    [{idx}/{contact_count}] Failed to migrate contact: {str(e)}")
                    self.stats['contacts_failed'] += 1
                    processed += 1
                    if self.progress_callback:
                        try:
                            self.progress_callback({'stage': 'contacts', 'processed': processed, 'total': contact_count, 'skipped': self.stats['contacts_skipped']})
                        except Exception:
                            pass
            
            self.logger.info(f"  ✓ Migrated {self.stats['contacts_migrated']} contact(s) to '{dest_addressbook_name}'")
                
        except Exception as e:
            self.logger.error(f"  Failed to retrieve contacts: {str(e)}")
    
    def _log_calendar_stats(self):
        """Log calendar migration statistics."""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("Calendar Migration Summary:")
        self.logger.info(f"  Calendars migrated: {self.stats['calendars_migrated']}")
        self.logger.info(f"  Calendars failed: {self.stats['calendars_failed']}")
        self.logger.info(f"  Events migrated: {self.stats['events_migrated']}")
        self.logger.info(f"  Events failed: {self.stats['events_failed']}")
        if self.stats['events_skipped'] > 0:
            self.logger.info(f"  Events skipped (duplicates/filtered): {self.stats['events_skipped']}")
        self.logger.info("=" * 60)
    
    def _log_contact_stats(self):
        """Log contact migration statistics."""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("Contact Migration Summary:")
        self.logger.info(f"  Address books migrated: {self.stats['addressbooks_migrated']}")
        self.logger.info(f"  Address books failed: {self.stats['addressbooks_failed']}")
        self.logger.info(f"  Contacts migrated: {self.stats['contacts_migrated']}")
        self.logger.info(f"  Contacts failed: {self.stats['contacts_failed']}")
        if self.stats['contacts_skipped'] > 0:
            self.logger.info(f"  Contacts skipped (duplicates): {self.stats['contacts_skipped']}")
        self.logger.info("=" * 60)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get migration statistics."""
        return self.stats
