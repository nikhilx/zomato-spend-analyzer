#!/usr/bin/env python3
"""Dump failed-to-parse Zomato emails for inspection.

Usage: python tools/dump_failed_samples.py [mbox_path] [max_samples]
"""
import os
import sys
import re
from pathlib import Path

from zomato_analyzer.parsers.mbox_parser import MBoxParser
from zomato_analyzer.parsers.zomato import ZomatoEmailParser


def sanitize(filename: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]", "_", filename)[:120]


def dump_failed(mbox_path: str, max_samples: int = 50):
    out_dir = Path('tools/failed_samples')
    out_dir.mkdir(parents=True, exist_ok=True)

    parser = MBoxParser(mbox_path)
    saved = 0
    total = 0

    for subject, from_addr, body in parser.parse():
        total += 1
        if not MBoxParser.validate_email(subject, from_addr):
            continue

        order = ZomatoEmailParser.extract_order(subject, from_addr, body, None)
        if order:
            continue

        # Save sample
        saved += 1
        name = f"{saved:03d}_{sanitize(subject or 'no_subject')}.html"
        path = out_dir / name
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"Subject: {subject}\nFrom: {from_addr}\n\n")
                f.write(body)
        except Exception as e:
            print('Failed to write', path, e)

        # Also save converted plain text for quick scanning
        try:
            clean = ZomatoEmailParser._convert_html_to_text(body)
            tpath = out_dir / (name + '.txt')
            with open(tpath, 'w', encoding='utf-8') as f:
                f.write(f'Subject: {subject}\nFrom: {from_addr}\n\n')
                f.write(clean)
        except Exception:
            pass

        if saved >= max_samples:
            break

    print('Saved samples to', out_dir, '(', saved, 'of', total, 'processed )')


if __name__ == '__main__':
    mbox = sys.argv[1] if len(sys.argv) > 1 else 'Zomato.mbox'
    max_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    dump_failed(mbox, max_samples)
