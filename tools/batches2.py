"""REL 2차 묶음: work/batches/rel2_XX.json"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(__file__)); import rel2, inventory
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
WL = {'OK', 'YES', 'NO', 'CANCEL', 'CONFIRM', 'CONTINUE', 'WARNING', 'ERROR', 'NOTICE', 'DONE', 'SAVE', 'LOAD', 'RETRY'}
def main():
    inv_all = json.load(open(os.path.join(ROOT, 'work', 'inv_all.json'), encoding='utf-8'))
    items = {}
    nid = 100000
    for m in ('FE', 'GAME', 'HRDERBY', 'INITDLL'):
        for a, s, k in rel2.candidates(os.path.join(ROOT, 'extract', m + '.REL')):
            p = re.sub(r'\^[a-z]\d*\^', '', s).strip()
            if re.fullmatch(r'[A-Z0-9 \-]+', p) and ' ' not in p and p not in WL: continue
            if '\n' in s or '0x' in s: continue
            if s in inv_all: continue
            e = items.setdefault(s, {'en': s, 'max': len(s.encode('latin1')), 'src': set(), 'printf': k == 'printf'})
            e['src'].add('rel2:' + m); e['max'] = min(e['max'], len(s.encode('latin1')))
    L = list(items.values())
    out = []; b = []; n = 0; k = 0
    for i, e in enumerate(L):
        b.append({'id': nid + i, 'en': e['en'], 'max': e['max'], 'src': sorted(e['src']), 'printf': e['printf']}); n += len(e['en'])
        if n > 20000:
            json.dump(b, open(os.path.join(ROOT, 'work', 'batches', f'rel2_{k:02d}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0); k += 1; b = []; n = 0
    if b: json.dump(b, open(os.path.join(ROOT, 'work', 'batches', f'rel2_{k:02d}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0); k += 1
    print(len(L), sum(len(e['en']) for e in L), 'batches', k)
    inv2 = {e['en']: {'src': sorted(e['src']), 'max': e['max']} for e in L}
    json.dump(inv2, open(os.path.join(ROOT, 'work', 'inv_rel2.json'), 'w', encoding='utf-8'), ensure_ascii=False)
if __name__ == '__main__': main()
