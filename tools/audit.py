"""미번역 표시 문자열 전수 집계 → work/untranslated.json"""
import sys, json, re, collections, os
sys.path.insert(0, os.path.dirname(__file__)); import ktext
B = chr(92)
tr = ktext.Translator(); m = tr.map
inv = json.load(open('work/inv_all.json', encoding='utf-8')); inv2 = json.load(open('work/inv_rel2.json', encoding='utf-8'))
allk = {**inv, **inv2}
names = set(f'{a} {b}' for a, b in tr.names) | set(a for a, b in tr.names) | set(b for a, b in tr.names)
MARK = re.compile(r'\^[a-z]\d*\^')
miss = collections.defaultdict(list)
for k, e in allk.items():
    if k in m: continue
    p = MARK.sub('', k).strip()
    if p in names: continue
    if not re.findall(r'[A-Za-z]{2,}', p): continue
    if re.fullmatch(r'[A-Z0-9/%.\- ]{1,6}', p): continue
    if any(x in p for x in ('.cpp', 'SKAT', 'fps', 'KHz', 'Generic', B)): continue
    miss[sorted(set(s.split(':')[0] for s in e['src']))[0]].append(k)
tot = 0
for g, L in miss.items():
    tot += len(L); print(g, len(L)); print('   ', [x[:50] for x in L[:80]])
print('total', tot)
json.dump(miss, open('work/untranslated.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
