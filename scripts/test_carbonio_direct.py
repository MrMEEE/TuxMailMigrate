#!/usr/bin/env python3
"""
Test direct calendar access for Carbonio
"""

import logging
import getpass
import caldav

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Server details
url = "https://mail.niamh.dk"
username = "m@rtinjuhl.dk"
password = getpass.getpass(f"Password for {username}: ")

print("\n" + "="*60)
print(f"Testing direct calendar access")
print("="*60 + "\n")

# Create client
client = caldav.DAVClient(
    url=url,
    username=username,
    password=password
)

# Try different calendar URLs
test_urls = [
    f"{url}/dav/{username}/Calendar",
    f"{url}/dav/{username}/calendar",
    f"{url}/dav/{username}",
]

for test_url in test_urls:
    print(f"\n{'='*60}")
    print(f"Trying: {test_url}")
    print('='*60)
    try:
        cal = caldav.Calendar(client=client, url=test_url)
        props = cal.get_properties(['{DAV:}displayname', '{DAV:}resourcetype'])
        print(f"✅ SUCCESS!")
        print(f"Properties: {props}")
        
        # Try to get events
        try:
            events = cal.events()
            print(f"📅 Found {len(events)} events")
            if events and len(events) > 0:
                print(f"   First event: {events[0].data if hasattr(events[0], 'data') else 'N/A'[:100]}")
        except Exception as e:
            print(f"   Could not get events: {e}")
            
    except Exception as e:
        print(f"❌ Failed: {type(e).__name__}: {e}")
