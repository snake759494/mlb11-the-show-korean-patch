"""선수 DB(TGDF)의 이름 칸: '이름 16바이트' + '성 16바이트' 가 붙어 있는 0 채움 문자열 쌍."""
import re
FILES = ['8382e1b8', '63163ce7', '1396c408', '65023f60', 'ac08628e']
PAT = re.compile(rb'(?<=[\x00-\x1f\x80-\xff])([A-Za-z][A-Za-z.\'\- ]{0,14})\x00')
def fld(d, o):
    e = d.find(b'\0', o)
    if e < 0 or e - o > 15 or e == o: return None
    s = d[o:e]
    if not re.fullmatch(rb"[A-Za-z][A-Za-z.'\- ]*", s): return None
    if any(d[e:o + 16]): return None
    return s.decode('latin1')
def pairs(d):
    out = []
    for m in PAT.finditer(d):
        o = m.start()
        a = fld(d, o)
        if a is None: continue
        b = fld(d, o + 16)
        if b is None: continue
        out.append((o, a, b))
    return out
