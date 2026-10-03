"""REL 내장 문자열: 재배치(R32/HI16/LO16, 구역 상대)로 시작 주소가 참조되는 문자열."""
import sys, os, re, collections
sys.path.insert(0, os.path.dirname(__file__)); import rel
FMT = re.compile(r'%[-0-9.]*[sdxfiucXl]|\|::|\.cpp|\.h\b|\(\)|->|==|!=|&&|\|\|')
def refs(d, h, S):
    R = rel.relocs(d, h, S)
    t = collections.defaultdict(list)
    for o, (ty, sym, a) in R.items():
        if sym is None and ty in (2, 5, 6): t[a].append((o, ty))
    return R, t
def strings(fn):
    d, h, S = rel.load(fn)
    R, t = refs(d, h, S)
    out = []
    for a in sorted(t):
        if a >= h[5] or a <= 0 or d[a - 1] != 0: continue
        e = d.find(b'\0', a); s = d[a:e]
        if not s or not all(32 <= c < 127 or c in (9, 10, 13) for c in s): continue
        out.append((a, s.decode('latin1'), t[a]))
    return d, h, S, R, out
def display_like(s):
    if FMT.search(s): return False
    p = re.sub(r'\^[a-z]\d*\^', '', s)
    if sum(c.isalpha() for c in p) < 3: return False
    if '_' in p or '/' in p and ' ' not in p: return False
    if ' ' not in p.strip() and '^' not in s: return False
    if re.search(r'[a-z][A-Z]', p) and ' ' not in p: return False
    return True
