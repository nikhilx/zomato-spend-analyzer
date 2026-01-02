import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zomato_analyzer.parsers.zomato import ZomatoEmailParser

def load_sample(path):
    raw = open(path, encoding='utf-8', errors='ignore').read()
    parts = raw.split('\n\n', 2)
    subject = ''
    from_addr = ''
    if parts:
        lines = parts[0].splitlines()
        for l in lines:
            if l.lower().startswith('subject:'):
                subject = l[len('Subject:'):].strip()
            if l.lower().startswith('from:'):
                from_addr = l[len('From:'):].strip()
    body = '\n'.join(parts[1:]) if len(parts) > 1 else raw
    return subject, from_addr, body

def main():
    sample = os.path.join(os.path.dirname(__file__), 'failed_samples', '050_Your_Zomato_Pro_Plus_order_from_Shree_Ganesh_Fast_Food.html')
    subject, from_addr, body = load_sample(sample)
    order = ZomatoEmailParser.extract_order(subject, from_addr, body)
    print('Subject:', subject)
    print('Order parsed:')
    print(order)

if __name__ == '__main__':
    main()
