from zomato_analyzer.parsers.mbox_parser import MBoxParser
from zomato_analyzer.parsers.zomato import ZomatoEmailParser
import os, collections, re

out_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'failed_samples')
os.makedirs(out_dir, exist_ok=True)
parser = MBoxParser(os.path.join(os.path.dirname(__file__), '..', 'Zomato.mbox'))

counts = collections.Counter()
saved = collections.Counter()


def safe_name(s):
    s = re.sub(r'[^0-9A-Za-z _\-\\.]+', '_', (s or 'no_subject'))
    return s[:120]

idx = 0
for subject, from_addr, body in parser.parse():
    idx += 1
    order = ZomatoEmailParser.extract_order(subject or '', from_addr or '', body or '')
    if not order:
        counts[subject] += 1
        if saved[subject] < 3:
            fname = f"{saved[subject]+1:02d}_{safe_name(subject)}_{idx}.html"
            path = os.path.join(out_dir, fname)
            try:
                with open(path, 'wb') as f:
                    f.write((body or '').encode('utf-8', errors='ignore'))
            except Exception:
                with open(path, 'wb') as f:
                    f.write(b'')
            saved[subject] += 1

print('Total failed emails:', sum(counts.values()))
print('\nTop failing subjects:')
for subj, c in counts.most_common(60):
    print(f'{c:4d} - {subj}')

print('\nSaved samples to', out_dir)
