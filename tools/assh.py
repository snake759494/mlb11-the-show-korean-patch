"""IFF0ASSH UI 화면 묶음.
머리: 'IFF0','ASSH',0,총크기 / 청크: 'VOID','ASS0', 해시, 크기, 데이터(크기 바이트).
청크 안의 문자열 포인터 = 청크 데이터 시작 기준 u32 오프셋(4바이트 정렬)."""
import struct, re
def chunks(d):
    out = []; i = 0
    while True:
        i = d.find(b'VOIDASS0', i)
        if i < 0: break
        h, sz = struct.unpack_from('<2I', d, i + 8)
        out.append((i, h, sz)); i += 16 + (sz if sz < 0x80000000 else 0)
    return out
def strings(d, cstart, csz):
    """청크 안에서 (상대 오프셋, 문자열, [참조 위치들]) — 정렬 u32 참조가 있는 것만."""
    c = d[cstart:cstart + csz]
    refs = {}
    for k in range(0, len(c) - 3, 4):
        v = struct.unpack_from('<I', c, k)[0]
        if 0 < v < len(c): refs.setdefault(v, []).append(k)
    out = []
    for m in re.finditer(rb'[\x09\x0a\x0d\x20-\x7e\x80-\xff]{1,}\x00', c):
        o = m.start()
        if o in refs and (o == 0 or c[o - 1] == 0):
            s = m.group()[:-1]
            out.append((o, s, refs[o]))
    return out
