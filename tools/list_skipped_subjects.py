"""List subjects of validated-but-unparsed Zomato emails."""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zomato_analyzer.parsers.mbox_parser import MBoxParser
from zomato_analyzer.parsers.zomato import ZomatoEmailParser


def main():
    mbox = os.path.join(os.path.dirname(__file__), '..', 'Zomato.mbox')
    mbox = os.path.abspath(mbox)
    parser = MBoxParser(mbox)

    skipped = []
    total = 0
    for subject, from_addr, body in parser.parse():
        if not MBoxParser.validate_email(subject or '', from_addr or ''):
            continue
        total += 1
        order = ZomatoEmailParser.extract_order(subject or '', from_addr or '', body or '')
        if order is None:
            subj = (subject or '').strip()
            skipped.append(subj or '(no subject)')

    counts = Counter(skipped)
    print(f'Total validated Zomato-like emails processed: {total}')
    print(f'Total validated-but-unparsed (skipped): {len(skipped)}')
    print('\nSubjects (grouped):')
    for s, c in counts.most_common():
        print(f'  {c:3d} - {s}')

    # Also print raw list for quick copy/paste
    print('\nRaw subjects:')
    for s in skipped:
        print(s)


if __name__ == '__main__':
    main()
