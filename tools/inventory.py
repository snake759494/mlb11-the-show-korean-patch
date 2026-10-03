"""번역 대상 목록 생성 → work/inv_assh.json  {원문: {"n": 횟수, "files": [...]}}"""
import sys, os, glob, json, re, struct, collections
sys.path.insert(0, os.path.dirname(__file__)); import assh, inject
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MARK = re.compile(r'\^[a-z]\d*\^')
def plain(t): return MARK.sub('', t)
def wanted(t):
    p = plain(t)
    if sum(c.isalpha() for c in p) < 2: return False
    if any(ord(c) > 126 or (ord(c) < 32 and c not in '\n\r\t') for c in t): return False
    if re.fullmatch(r'[A-Z0-9_]+', p) and '_' in p: return False
    if re.fullmatch(r'[Wx0-9 ]+', p): return False
    return True
def assh_inventory():
    inv = collections.OrderedDict()
    for fn in sorted(glob.glob(os.path.join(ROOT, 'extract', 'wad', '*.bin'))):
        d = open(fn, 'rb').read()
        if d[:8] != b'IFF0ASSH': continue
        h = os.path.basename(fn)[:8]
        for (i, hh, sz) in assh.chunks(d):
            if sz >= 0x80000000 or sz == 0: continue
            c = d[i + 16:i + 16 + sz]
            for o, s, refs in assh.strings(d, i + 16, sz):
                t = s.decode('latin1')
                if not wanted(t): continue
                rtts = (h == '97c92be3' and ' ' in plain(t))
                if not rtts and not any(inject.is_disp_ref(c, k, s) for k in refs): continue
                e = inv.setdefault(t, {'n': 0, 'files': []})
                e['n'] += 1
                if h not in e['files']: e['files'].append(h)
    return inv
if __name__ == '__main__':
    inv = assh_inventory()
    json.dump(inv, open(os.path.join(ROOT, 'work', 'inv_assh.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    by = collections.Counter()
    for t, e in inv.items():
        for f in e['files']: by[f] += 1
    print(len(inv), sum(len(t) for t in inv), by.most_common(15))
