"""텍스트형 WAD 파일 번역 적용: 도움말 바(FE.txt), goals.txt, eggs.txt, RTTS 목표(레코드 스트림)."""
import struct
def helpbar(d, tr):
    """첫 줄 '개수 크기'(크기 = 나머지 바이트 - 2*개수), 줄마다 키,라벨1..5,설명. 키는 그대로."""
    lines = d.decode('latin1').split('\n')
    out = []
    for ln in lines[1:]:
        if not ln: out.append(ln); continue
        parts = ln.split(',', 6)
        if len(parts) < 7: out.append(ln); continue
        for k in range(1, 6):
            if parts[k].strip(): parts[k] = tr(parts[k])
        desc = parts[6]
        q = desc.startswith('"') and desc.endswith('"') and len(desc) >= 2
        body = desc[1:-1] if q else desc
        if body.strip(): body = tr(body)
        parts[6] = '"' + body + '"' if q else body
        out.append(','.join(parts))
    rest = '\n'.join(out).encode('latin1')
    cnt = int(lines[0].split()[0])
    head = f'{cnt} {len(rest) - 2 * cnt}\n'.encode()
    return head + rest
def tsv(d, tr, cols):
    txt = d.decode('latin1')
    out = []
    for ln in txt.split('\n'):
        cr = ln.endswith('\r'); body = ln[:-1] if cr else ln
        f = body.split('\t')
        for c in cols:
            if c < len(f) and f[c].strip(): f[c] = tr(f[c])
        out.append('\t'.join(f) + ('\r' if cr else ''))
    return '\n'.join(out).encode('latin1')
def recstream(d, tr):
    o = 0; out = bytearray()
    while o + 8 <= len(d):
        a, n = struct.unpack_from('<2I', d, o)
        if n > 4096: break
        s = d[o + 8:o + 8 + n].decode('latin1')
        b = tr(s).encode('latin1') if s.strip() else s.encode('latin1')
        out += struct.pack('<2I', a, len(b)) + b; o += 8 + n
    out += d[o:]
    return bytes(out)
def notable(d, tr):
    """notable.bin: u32 개수 + 200바이트 레코드, 문자열 칸 +100 ~ +187 (88바이트)."""
    d = bytearray(d)
    n = struct.unpack_from('<I', d, 0)[0]
    for i in range(n):
        o = 4 + 200 * i + 100
        e = d.index(b'\0', o); s = d[o:e].decode('latin1')
        if not s: continue
        b = tr(s).encode('latin1')
        if len(b) > 87: continue
        d[o:o + 88] = b + bytes(88 - len(b))
    return bytes(d)
