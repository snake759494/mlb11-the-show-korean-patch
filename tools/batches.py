"""전체 번역 대상 → work/batches/*.json  (각 항목 id, en, max, src)"""
import sys, os, json, re, collections, glob
sys.path.insert(0, os.path.dirname(__file__)); import relstr, inventory
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
W = os.path.join(ROOT, 'extract', 'wad')
def helpbar_fields(d):
    """FE.txt: 첫 줄 '개수 크기', 이후 줄마다 키,라벨1..5,설명(따옴표 가능)"""
    lines = d.decode('latin1').split('\n')
    out = []
    for ln in lines[1:]:
        if not ln: continue
        parts = ln.split(',', 6)
        if len(parts) < 7: continue
        for p in parts[1:6]:
            if p.strip(): out.append(p)
        desc = parts[6]
        if desc.startswith('"') and desc.endswith('"'): desc = desc[1:-1]
        if desc.strip(): out.append(desc)
    return out
def tsv_fields(d, cols):
    out = []
    for ln in d.decode('latin1').replace('\r', '').split('\n'):
        f = ln.split('\t')
        for c in cols:
            if c < len(f) and f[c].strip(): out.append(f[c])
    return out
def recstream(d):
    import struct
    o = 0; out = []
    while o + 8 <= len(d):
        a, n = struct.unpack_from('<2I', d, o)
        if n > 4096: break
        out.append(d[o + 8:o + 8 + n].decode('latin1')); o += 8 + n
    return out
def main():
    G = collections.OrderedDict()     # en -> {'src': set, 'max': None|int, 'grp': str}
    def add(t, src, grp, mx=None):
        if not inventory.wanted(t): return
        e = G.setdefault(t, {'src': set(), 'max': None, 'grp': grp})
        e['src'].add(src)
        if mx is not None: e['max'] = mx if e['max'] is None else min(e['max'], mx)
    inv = inventory.assh_inventory()
    for t, e in inv.items():
        add(t, 'assh', 'rtts' if e['files'] == ['97c92be3'] else 'ui')
    for t in helpbar_fields(open(os.path.join(W, 'bd3c4959.bin'), 'rb').read()): add(t, 'help', 'help')
    for t in tsv_fields(open(os.path.join(W, '64e8260a.bin'), 'rb').read(), [1, 2, 3, 4, 5]): add(t, 'goals', 'goals')
    for t in tsv_fields(open(os.path.join(W, 'f659e994.bin'), 'rb').read(), [2, 3]): add(t, 'eggs', 'goals')
    for t in recstream(open(os.path.join(W, '7a917520.bin'), 'rb').read()): add(t, 'cgoals', 'cgoals')
    for m in ('FE', 'GAME', 'HRDERBY', 'INITDLL'):
        d, h, S, R, out = relstr.strings(os.path.join(ROOT, 'extract', m + '.REL'))
        for a, s, r in out:
            if relstr.display_like(s): add(s, 'rel:' + m, 'rel_' + m, len(s.encode('latin1')))
    os.makedirs(os.path.join(ROOT, 'work', 'batches'), exist_ok=True)
    groups = collections.defaultdict(list)
    for i, (t, e) in enumerate(G.items()):
        groups[e['grp']].append({'id': i, 'en': t, 'max': e['max'], 'src': sorted(e['src'])})
    LIM = {'rtts': 30000, 'ui': 14000, 'help': 30000, 'goals': 30000, 'cgoals': 30000}
    for g, items in groups.items():
        lim = LIM.get(g, 22000)
        b = []; n = 0; k = 0
        for it in items:
            b.append(it); n += len(it['en'])
            if n >= lim:
                json.dump(b, open(os.path.join(ROOT, 'work', 'batches', f'{g}_{k:02d}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0); k += 1; b = []; n = 0
        if b: json.dump(b, open(os.path.join(ROOT, 'work', 'batches', f'{g}_{k:02d}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0); k += 1
        print(g, len(items), sum(len(x['en']) for x in items), 'batches', k)
    json.dump({t: {'src': sorted(e['src']), 'max': e['max']} for t, e in G.items()}, open(os.path.join(ROOT, 'work', 'inv_all.json'), 'w', encoding='utf-8'), ensure_ascii=False)
if __name__ == '__main__': main()
