"""HRDERBY.REL(심볼 있음)의 함수를 FE/GAME.REL(심볼 없음)에서 재배치 칸을 가린 바이트 패턴으로 찾는다."""
import sys, os, struct, re
sys.path.insert(0, os.path.dirname(__file__)); import rel
def masked(fn):
    d, h, S = rel.load(fn); R = rel.relocs(d, h, S)
    m = bytearray(d)
    for o in R: m[o:o + 4] = b'\0\0\0\0'
    return d, h, S, R, bytes(m)
def funcs(S, lo=0, hi=1 << 31):
    L = sorted((a, n) for n, a, b in S if a and lo <= a < hi)
    return L
def find(name_sub, targets=('FE', 'GAME'), ref='extract/HRDERBY.REL', n=None):
    d, h, S, R, m = masked(ref)
    L = sorted(set((a, s) for s, a, b in S if a))
    out = {}
    for i, (a, s) in enumerate(L):
        if name_sub not in s: continue
        end = L[i + 1][0] if i + 1 < len(L) else a + 64
        pat = m[a:end] if n is None else m[a:a + n]
        res = {}
        for t in targets:
            td = masked(f'extract/{t}.REL')[4]
            hits = [x.start() for x in re.finditer(re.escape(pat), td)]
            res[t] = hits
        out[s] = (a, end - a, res)
    return out
if __name__ == '__main__':
    for k, v in find(sys.argv[1]).items(): print(k[:90], hex(v[0]), v[1], {t: [hex(x) for x in hs] for t, hs in v[2].items()})
