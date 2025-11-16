#!/usr/bin/env python3
"""
Simple test script to list calendars from Carbonio server
"""

import logging
import getpass
from caldav_client import CalDAVClient

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Server details
url = "https://mail.niamh.dk"
username = "m@rtinjuhl.dk"
principal_path = "/dav/m@rtinjuhl.dk"

# Get password
password = getpass.getpass(f"Password for {username}: ")

print("\n" + "="*60)
print(f"Testing connection to: {url}")
print(f"Principal path: {principal_path}")
print("="*60 + "\n")

# Create client
client = CalDAVClient(
    url=url,
    username=username,
    password=password,
    principal_path=principal_path,
    verify_ssl=True,
    server_type='Carbonio'
)

# Try to connect
print("Attempting to connect...")
success, error = client.connect()

if not success:
    print(f"\n❌ Connection failed: {error}")
    exit(1)

print("✅ Connection successful!\n")

# Get calendars
print("Retrieving calendars...")
calendars = client.get_calendars()

if calendars:
    print(f"\n✅ Found {len(calendars)} calendar(s):\n")
    for i, cal in enumerate(calendars, 1):
        try:
            props = cal.get_properties(['{DAV:}displayname'])
            name = props.get('{DAV:}displayname', 'Unknown')
            print(f"  {i}. {name}")
            print(f"     URL: {cal.url}")
            
            # Try to get some events
            events = cal.events()
            print(f"     Events: {len(events)}")
        except Exception as e:
            print(f"  {i}. Error reading calendar: {e}")
        print()
else:
    print("\n⚠️  No calendars found")

# Get address books
print("\nRetrieving address books...")
addressbooks = client.get_addressbooks()

if addressbooks:
    print(f"\n✅ Found {len(addressbooks)} address book(s):\n")
    for i, ab in enumerate(addressbooks, 1):
        try:
            props = ab.get_properties(['{DAV:}displayname'])
            name = props.get('{DAV:}displayname', 'Unknown')
            print(f"  {i}. {name}")
            print(f"     URL: {ab.url}")
            
            # Try to get some contacts
            contacts = ab.search()
            print(f"     Contacts: {len(contacts)}")
        except Exception as e:
            print(f"  {i}. Error reading address book: {e}")
        print()
else:
    print("\n⚠️  No address books found")

print("\n" + "="*60)
print("Test complete!")
print("="*60)
