#!/usr/bin/env python3
"""
Test PROPFIND to discover calendar collections
"""

import requests
from requests.auth import HTTPBasicAuth
import getpass
from xml.etree import ElementTree as ET

url = "https://mail.niamh.dk"
username = "m@rtinjuhl.dk"
password = getpass.getpass(f"Password for {username}: ")

# PROPFIND request to discover calendar collections
propfind_body = '''<?xml version="1.0" encoding="utf-8" ?>
<d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav" xmlns:cs="http://calendarserver.org/ns/">
  <d:prop>
    <d:displayname />
    <d:resourcetype />
    <c:calendar-description />
    <c:supported-calendar-component-set />
  </d:prop>
</d:propfind>'''

test_paths = [
    f"/dav/{username}",
    f"/dav/{username}/Calendar",
    f"/dav/{username}/calendar",
]

for path in test_paths:
    full_url = url + path
    print(f"\n{'='*70}")
    print(f"PROPFIND on: {full_url}")
    print('='*70)
    
    try:
        response = requests.request(
            'PROPFIND',
            full_url,
            auth=HTTPBasicAuth(username, password),
            data=propfind_body,
            headers={
                'Content-Type': 'application/xml; charset=utf-8',
                'Depth': '1'
            },
            verify=True
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 207:  # Multi-Status
            print(f"\n✅ SUCCESS - Found resources:\n")
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # Define namespaces
            ns = {
                'd': 'DAV:',
                'c': 'urn:ietf:params:xml:ns:caldav'
            }
            
            for response_elem in root.findall('.//d:response', ns):
                href = response_elem.find('.//d:href', ns)
                displayname = response_elem.find('.//d:displayname', ns)
                resourcetype = response_elem.find('.//d:resourcetype', ns)
                
                if href is not None:
                    print(f"  Resource: {href.text}")
                    if displayname is not None and displayname.text:
                        print(f"    Name: {displayname.text}")
                    if resourcetype is not None:
                        types = [child.tag.split('}')[-1] for child in resourcetype]
                        print(f"    Types: {', '.join(types)}")
                    print()
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
