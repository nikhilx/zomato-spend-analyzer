import os
import re
from collections import Counter, defaultdict

def main():
    p = os.path.join(os.path.dirname(__file__), 'failed_samples')
    if not os.path.isdir(p):
        print('No failed_samples directory found at', p)
        return
    files = [f for f in os.listdir(p) if f.endswith('.txt')]
    templates = Counter()
    details = defaultdict(list)
    for fn in files:
        path = os.path.join(p, fn)
        try:
            txt = open(path, encoding='utf-8', errors='ignore').read()
        except Exception:
            txt = ''
        subj = ''
        m = re.search(r'Subject:\s*(.*)', txt)
        if m:
            subj = m.group(1).strip()
        kind = 'other'
        low = txt.lower()
        if 'refund' in subj.lower() or 'refund' in low:
            kind = 'refund'
        elif 'renewed' in low or 'gold' in low or 'membership' in low:
            kind = 'membership'
        elif 'login alert' in subj or 'login' in subj:
            kind = 'security'
        elif 'pro plus' in subj.lower() or 'pro plus' in low or 'pro +' in low:
            kind = 'pro_plus'
        elif 'order from' in subj.lower() or 'your order' in low:
            kind = 'order_subject'
        if '.pdf' in low or 'download order invoice' in low or 'invoice' in low:
            kind = kind + '|invoice'
        if len(txt.splitlines()) > 200 and '<style' in low:
            kind = kind + '|html-styled'
        templates[kind] += 1
        details[kind].append(subj)

    print('Template counts from', len(files), 'samples:')
    for k, c in templates.most_common():
        print(f'  {c:2d} - {k}')

    print('\nTop subjects per category (sample):')
    for k, subs in details.items():
        print(f'\n== {k} ({len(subs)}) ==')
        for s in subs[:5]:
            print('  -', (s or '(no subject)')[:120])

if __name__ == '__main__':
    main()
