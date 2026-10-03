"""D_TEAM_PROF: '[DATA]D_TEAM_PROF' + 패딩(16) + u32 개수 + 52바이트 레코드
[연고지 12][연고지 약칭 8][팀명 12][팀명 약칭 8][약어 4][기타 8]"""
import struct, json, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
LIMIT = {'Kansas City': '캔자스시티', 'St. Louis': 'St.루이스', 'San Francisco': '샌프란', 'Philadelphia': '필라델피아',
         'Diamondbacks': '디백스', 'Washington': '워싱턴', 'Cleveland': '클리블랜드', 'Tampa Bay': '탬파베이'}
def nb(s): return sum(2 if ord(c) > 127 else 1 for c in s)
def ko(T, s, lim):
    v = LIMIT.get(s) if s in LIMIT and nb(T.get(s, s)) > lim else T.get(s)
    if v is None: return None
    if nb(v) > lim:
        out = ''
        for c in v:
            if nb(out + c) > lim: break
            out += c
        v = out
    return v
def apply(d, T, enc):
    d = bytearray(d)
    c = 0
    for tag in (b'[DATA]D_TEAM_PROF', b'[DATA]ROSTERS'):
        i = d.find(tag)
        if i < 0: continue
        p = i + 6 + 16
        n = struct.unpack_from('<I', d, p)[0]; p += 4
        stride = 52 if b'TEAM_PROF' in tag else d.find(b'Boston\0', p) - p
        if not (52 <= stride < 4096): continue
        c += _recs(d, T, enc, p, n, stride)
    return bytes(d), c
def _recs(d, T, enc, p, n, stride):
    c = 0
    for k in range(n):
        r = p + stride * k
        for off, size in ((0, 12), (12, 8), (20, 12), (32, 8)):
            o = r + off; e = d.find(b'\0', o, o + size)
            if e <= o: continue
            s = d[o:e].decode('latin1')
            full = None
            if size == 8:   # 약칭: 같은 레코드의 전체 이름에서
                fo = r + (0 if off == 12 else 20); fe = d.find(b'\0', fo, fo + 12)
                full = d[fo:fe].decode('latin1')
            v = ko(T, full or s, size - 1)
            if not v: continue
            b = enc(v)
            if len(b) > size - 1: continue
            d[o:o + size] = b + bytes(size - len(b)); c += 1
    return c
