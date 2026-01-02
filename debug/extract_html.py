#!/usr/bin/env python3
"""Find order ID pattern in Pro Plus email."""

from zomato_analyzer.parsers.mbox_parser import MBoxParser
import re

parser = MBoxParser('Zomato.mbox')

for subject, from_addr, body in parser.parse():
    if 'Pro Plus order from LunchBox' in subject:
        # Look for order ID
        print("Looking for order ID...")
        if '#' in body:
            idx = body.find('#')
            print(f"Found # at position {idx}")
            print(f"Context: ...{body[max(0,idx-50):idx+100]}...")
        
        # Look for numbers that might be order ID (7+ digits)
        numbers = re.findall(r'\b\d{7,}\b', body[:5000])
        print(f"\nFound numbers: {numbers[:10]}")
        
        # Look for price patterns
        prices = re.findall(r'[₹Rs]*\s*(\d+\.?\d*)', body[:3000])
        print(f"\nFound prices: {prices[:10]}")
        
        break
    
    # Save to file for inspection
    with open("sample_email.html", "w", encoding='utf-8') as f:
        f.write(body)
    
    print("Saved first email HTML to sample_email.html")
    print(f"Size: {len(body)} bytes")
    print("\nFirst 2000 characters:")
    print(body[:2000])
