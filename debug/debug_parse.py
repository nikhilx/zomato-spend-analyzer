#!/usr/bin/env python3
"""Sample one email to see the format."""

from zomato_analyzer.parsers.mbox_parser import MBoxParser

parser = MBoxParser('Zomato.mbox')

count = 0
for subject, from_addr, body in parser.parse():
    if 'Pro Plus order from LunchBox' in subject:
        print(f"Subject: {subject}\n")
        print("Body (first 1500 chars):")
        print(body[:1500])
        print("\n" + "="*60 + "\n")
        count += 1
        if count >= 2:
            break
