#!/usr/bin/env python3
"""Debug script to analyze MBOX parsing."""

from zomato_analyzer.parsers.mbox_parser import MBoxParser
from zomato_analyzer.parsers.zomato import ZomatoEmailParser

def debug_mbox(mbox_path: str):
    """Debug MBOX file parsing."""
    parser = MBoxParser(mbox_path)
    
    validated = 0
    failed_parse = 0
    failed_validate = 0
    skipped_subjects = {}
    
    for subject, from_addr, body in parser.parse():
        # Check validation
        is_valid = MBoxParser.validate_email(subject, from_addr)
        
        if not is_valid:
            failed_validate += 1
            if subject not in skipped_subjects:
                skipped_subjects[subject] = 0
            skipped_subjects[subject] += 1
            continue
        
        validated += 1
        
        # Try to extract order
        order = ZomatoEmailParser.extract_order(subject, from_addr, body, None)
        
        if not order:
            failed_parse += 1
            if subject not in skipped_subjects:
                skipped_subjects[subject] = 0
            skipped_subjects[subject] += 1
    
    print(f"Total emails validated: {validated}")
    print(f"Failed to parse (passed validation): {failed_parse}")
    print(f"Failed validation: {failed_validate}")
    print("Top skipped subjects:")
    for subject, count in sorted(skipped_subjects.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"  {count:3d} - {subject[:80]}")

if __name__ == '__main__':
    debug_mbox('Zomato.mbox')
