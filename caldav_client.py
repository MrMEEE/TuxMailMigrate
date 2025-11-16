"""
CalDAV/CardDAV Migration Tool
A generic tool for migrating calendars and contacts between servers.
"""

import logging
from typing import Optional, Dict, Any
import caldav
import caldav.objects
from caldav.lib.error import AuthorizationError, NotFoundError


class CalDAVClient:
    """Wrapper for CalDAV/CardDAV operations."""
    
    # Default principal paths for different server types
    DEFAULT_PRINCIPAL_PATHS = {
        'Carbonio': '/dav/{username}',
        'Zimbra': '/dav/{username}',
        'Nextcloud': '/remote.php/dav/principals/users/{username}',
        'Mailcow': '/SOGo/dav/{username}',
        'SOGo': '/SOGo/dav/{username}',
    }
    
    def __init__(self, url: str, username: str, password: str, principal_path: Optional[str] = None, 
                 verify_ssl: bool = True, server_type: Optional[str] = None):
        """
        Initialize CalDAV client.
        
        Args:
            url: Base URL of the CalDAV server
            username: Username for authentication
            password: Password for authentication
            principal_path: Optional principal path (auto-discovered if not provided).
                          Can include {username} placeholder which will be replaced.
                          If empty/None and server_type is provided, uses default for that type.
            verify_ssl: Whether to verify SSL certificates (set False for self-signed certs)
            server_type: Type of server (Carbonio, Zimbra, Mailcow, etc.) - used for default paths
        """
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        
        # Determine principal path with defaults
        if principal_path:
            # User provided a path - use it
            self.principal_path = principal_path.replace('{username}', username)
        elif server_type and server_type in self.DEFAULT_PRINCIPAL_PATHS:
            # Use default for server type
            default_path = self.DEFAULT_PRINCIPAL_PATHS[server_type]
            self.principal_path = default_path.replace('{username}', username) if default_path else None
        else:
            # No path and no recognized server type - use auto-discovery
            self.principal_path = None
            
        self.client = None
        self.principal = None
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def connect(self) -> tuple[bool, Optional[str]]:
        """
        Connect to the CalDAV server and verify authentication.
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            self.logger.info(f"Connecting to {self.url}... (SSL verify: {self.verify_ssl})")
            
            # Disable SSL warnings if verify_ssl is False
            if not self.verify_ssl:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            self.client = caldav.DAVClient(
                url=self.url,
                username=self.username,
                password=self.password,
                ssl_verify_cert=self.verify_ssl
            )
            
            # Get principal (user account)
            if self.principal_path:
                self.principal = caldav.Principal(self.client, url=f"{self.url}{self.principal_path}")
            else:
                self.principal = self.client.principal()
            
            self.logger.info(f"Successfully connected to {self.url}")
            return True, None
            
        except AuthorizationError as e:
            error_msg = f"Authentication failed for {self.url} (username: {self.username})"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Connection failed for {self.url}: {type(e).__name__}: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_calendars(self) -> list:
        """
        Get all calendars for the authenticated user.
        
        Returns:
            List of calendar objects
        """
        calendars = []
        try:
            self.logger.info(f"Retrieving calendars from principal: {self.principal.url if self.principal else 'None'}")
            calendars = self.principal.calendars()
            self.logger.info(f"Found {len(calendars)} calendar(s)")
            if calendars:
                for cal in calendars:
                    try:
                        props = cal.get_properties([caldav.dav.DisplayName()])
                        cal_name = props.get('{DAV:}displayname', 'Unknown')
                        self.logger.info(f"  - Calendar: {cal_name} at {cal.url}")
                    except Exception as e:
                        self.logger.warning(f"  - Calendar at {cal.url} (couldn't get name: {e})")
        except (IndexError, AttributeError, Exception) as e:
            # Standard discovery failed - this is common for Carbonio/Zimbra
            self.logger.warning(f"Standard calendar discovery failed: {type(e).__name__}: {str(e)}")
            calendars = []
        
        # If no calendars found via standard method, try PROPFIND to discover all (Carbonio/Zimbra)
        if not calendars:
            self.logger.warning("Trying PROPFIND for calendar discovery")
            try:
                import xml.etree.ElementTree as ET
                from urllib.parse import urljoin
                
                principal_url = self.principal.url if self.principal else self.url
                # Ensure principal_url is a string
                if not isinstance(principal_url, str):
                    principal_url = str(principal_url)
                
                # Use PROPFIND to discover all calendar collections
                propfind_body = '''<?xml version="1.0" encoding="utf-8" ?>
                <d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
                  <d:prop>
                    <d:resourcetype />
                    <d:displayname />
                  </d:prop>
                </d:propfind>'''
                
                response = self.client.request(
                    url=principal_url,
                    method='PROPFIND',
                    headers={'Depth': '1', 'Content-Type': 'application/xml; charset=utf-8'},
                    body=propfind_body
                )
                
                # Parse response to find calendar collections
                # response.raw can be str or bytes, handle both
                response_text = response.raw if isinstance(response.raw, str) else response.raw.decode('utf-8')
                root = ET.fromstring(response_text)
                ns = {'d': 'DAV:', 'c': 'urn:ietf:params:xml:ns:caldav'}
                
                for response_elem in root.findall('.//d:response', ns):
                    href = response_elem.find('d:href', ns)
                    if href is None:
                        continue
                    
                    # Check if this is a calendar collection
                    resourcetype = response_elem.find('.//d:resourcetype', ns)
                    if resourcetype is not None:
                        is_calendar = resourcetype.find('c:calendar', ns) is not None
                        if is_calendar:
                            cal_url = href.text
                            if cal_url and not cal_url.startswith('http'):
                                # Relative URL, make it absolute
                                cal_url = urljoin(principal_url, cal_url)
                            
                            try:
                                cal = caldav.Calendar(client=self.client, url=cal_url)
                                calendars.append(cal)
                                
                                displayname = response_elem.find('.//d:displayname', ns)
                                name = displayname.text if displayname is not None else 'Unknown'
                                self.logger.info(f"✅ Found calendar: {name} at {cal_url}")
                            except Exception as e:
                                self.logger.debug(f"Error creating calendar object for {cal_url}: {e}")
                
                self.logger.info(f"Found {len(calendars)} calendar(s) via PROPFIND")
            except Exception as e:
                self.logger.error(f"Failed to retrieve calendars via PROPFIND: {type(e).__name__}: {str(e)}")
        
        return calendars
    
    def get_calendar_by_name(self, name: str):
        """
        Get a calendar by its display name.
        
        Args:
            name: Display name of the calendar
            
        Returns:
            Calendar object or None if not found
        """
        calendars = self.get_calendars()
        for calendar in calendars:
            try:
                cal_name = calendar.get_properties([caldav.dav.DisplayName()])['{DAV:}displayname']
                if cal_name == name:
                    return calendar
            except:
                continue
        return None
    
    def create_calendar(self, name: str, **kwargs):
        """
        Create a new calendar.
        
        Args:
            name: Display name for the new calendar
            **kwargs: Additional properties (color, description, etc.)
            
        Returns:
            Created calendar object or None if failed
        """
        try:
            calendar = self.principal.make_calendar(name=name, **kwargs)
            self.logger.info(f"Created calendar: {name}")
            return calendar
        except Exception as e:
            self.logger.error(f"Failed to create calendar '{name}': {str(e)}")
            return None
    
    def get_addressbooks(self):
        """
        Get all address books for the user.
        
        Returns:
            List of address book objects
        """
        addressbooks = []
        try:
            # Address books are retrieved similarly to calendars
            self.logger.info(f"Retrieving address books from principal: {self.principal.url if self.principal else 'None'}")
            addressbooks = self.principal.addressbooks()
            self.logger.info(f"Found {len(addressbooks)} address book(s)")
            if addressbooks:
                for ab in addressbooks:
                    try:
                        props = ab.get_properties([caldav.dav.DisplayName()])
                        ab_name = props.get('{DAV:}displayname', 'Unknown')
                        self.logger.info(f"  - Address book: {ab_name} at {ab.url}")
                    except Exception as e:
                        self.logger.warning(f"  - Address book at {ab.url} (couldn't get name: {e})")
        except (AttributeError, Exception) as e:
            # Standard discovery failed - this is common for Carbonio/Zimbra
            self.logger.warning(f"Standard addressbook discovery failed: {type(e).__name__}: {str(e)}")
            addressbooks = []
        
        # If no addressbooks found via standard method, try PROPFIND (Carbonio/Zimbra)
        if not addressbooks:
            self.logger.warning("Trying PROPFIND for addressbook discovery")
            try:
                import xml.etree.ElementTree as ET
                from urllib.parse import urljoin
                
                principal_url = self.principal.url if self.principal else self.url
                # Ensure principal_url is a string
                if not isinstance(principal_url, str):
                    principal_url = str(principal_url)
                
                # Use PROPFIND to discover all addressbook collections
                propfind_body = '''<?xml version="1.0" encoding="utf-8" ?>
                <d:propfind xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
                  <d:prop>
                    <d:resourcetype />
                    <d:displayname />
                  </d:prop>
                </d:propfind>'''
                
                response = self.client.request(
                    url=principal_url,
                    method='PROPFIND',
                    headers={'Depth': '1', 'Content-Type': 'application/xml; charset=utf-8'},
                    body=propfind_body
                )
                
                # Parse response to find addressbook collections
                # response.raw can be str or bytes, handle both
                response_text = response.raw if isinstance(response.raw, str) else response.raw.decode('utf-8')
                root = ET.fromstring(response_text)
                ns = {'d': 'DAV:', 'card': 'urn:ietf:params:xml:ns:carddav'}
                
                for response_elem in root.findall('.//d:response', ns):
                    href = response_elem.find('d:href', ns)
                    if href is None:
                        continue
                    
                    # Check if this is an addressbook collection
                    resourcetype = response_elem.find('.//d:resourcetype', ns)
                    if resourcetype is not None:
                        is_addressbook = resourcetype.find('card:addressbook', ns) is not None
                        if is_addressbook:
                            ab_url = href.text
                            if ab_url and not ab_url.startswith('http'):
                                # Relative URL, make it absolute
                                ab_url = urljoin(principal_url, ab_url)
                            
                            try:
                                ab = caldav.Calendar(client=self.client, url=ab_url)
                                addressbooks.append(ab)
                                
                                displayname = response_elem.find('.//d:displayname', ns)
                                name = displayname.text if displayname is not None else 'Unknown'
                                self.logger.info(f"✅ Found addressbook: {name} at {ab_url}")
                            except Exception as e:
                                self.logger.debug(f"Error creating addressbook object for {ab_url}: {e}")
                
                self.logger.info(f"Found {len(addressbooks)} addressbook(s) via PROPFIND")
            except Exception as e:
                self.logger.error(f"Failed to retrieve addressbooks via PROPFIND: {type(e).__name__}: {str(e)}")
        
        return addressbooks
    
    def get_addressbook_by_name(self, name: str):
        """
        Get an address book by its display name.
        
        Args:
            name: Display name of the address book
            
        Returns:
            Address book object or None if not found
        """
        addressbooks = self.get_addressbooks()
        for addressbook in addressbooks:
            try:
                ab_name = addressbook.get_properties([caldav.dav.DisplayName()])['{DAV:}displayname']
                if ab_name == name:
                    return addressbook
            except:
                continue
        return None
    
    def create_addressbook(self, name: str, **kwargs):
        """
        Create a new address book.
        
        Args:
            name: Display name for the new address book
            **kwargs: Additional properties
            
        Returns:
            Created address book object or None if failed
        """
        try:
            addressbook = self.principal.make_addressbook(name=name, **kwargs)
            self.logger.info(f"Created address book: {name}")
            return addressbook
        except Exception as e:
            self.logger.error(f"Failed to create address book '{name}': {str(e)}")
            return None
