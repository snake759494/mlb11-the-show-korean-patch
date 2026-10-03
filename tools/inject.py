"""ASSH(UI 화면) 파일에 번역 주입.
- 표시 참조만 바꾼다: 문자열 요소(참조-16 위치 u16==2), 표 머리(참조-4 u16==1 이고 참조-6 u16==0),
  또는 마크업(^)이 들어 있는 문자열의 모든 참조.
- 새 문자열이 원래 자리에 들어가고 모든 참조가 표시용이면 제자리, 아니면 청크 끝에 붙이고 표시 참조만 옮긴다.
- 청크가 커지면 뒤 청크를 밀고 머리의 청크 오프셋·전체 크기를 갱신한다."""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__)); import assh
def is_disp_ref(c, k, s):
    if b'^' in s: return True
    if k >= 16 and struct.unpack_from('<H', c, k - 16)[0] == 2: return True
    if k >= 6 and struct.unpack_from('<H', c, k - 4)[0] == 1 and struct.unpack_from('<H', c, k - 6)[0] == 0: return True
    return False
def inject_chunk(c, tr, stats, force_all=False):
    """c: 청크 데이터. tr(bytes)->bytes 또는 None. 새 청크 반환."""
    c = bytearray(c); tail = bytearray()
    base = len(c)
    for o, s, refs in assh.strings(bytes(c), 0, len(c)):
        new = tr(s)
        if new is None or new == s: continue
        disp = [k for k in refs if force_all or is_disp_ref(c, k, s)]
        if not disp: continue
        stats['n'] += 1
        if len(disp) == len(refs) and len(new) <= len(s):
            c[o:o + len(s)] = new + bytes(len(s) - len(new)); stats['inplace'] += 1
        else:
            no = base + len(tail); tail += new + b'\0'
            for k in disp: struct.pack_into('<I', c, k, no)
            stats['moved'] += 1
    if tail:
        tail += bytes((-len(tail)) % 16)
    return bytes(c + tail)
def inject(d, tr, force_all=False):
    stats = {'n': 0, 'inplace': 0, 'moved': 0}
    C = assh.chunks(d)
    first = C[0][0]
    head = bytearray(d[:first])
    out = bytearray(); shift = {}
    pos = first
    for idx, (i, h, sz) in enumerate(C):
        end = C[idx + 1][0] if idx + 1 < len(C) else len(d)
        blob = d[i:end]
        if sz < 0x80000000 and sz > 0:
            nc = inject_chunk(d[i + 16:i + 16 + sz], tr, stats, force_all)
            rest = d[i + 16 + sz:end]
            blob = d[i:i + 12] + struct.pack('<I', len(nc)) + nc + rest
        shift[i] = first + len(out)
        out += blob
    # 머리의 청크 오프셋 갱신 (청크 시작과 같은 값의 u32)
    for k in range(0x10, first - 3, 4):
        v = struct.unpack_from('<I', head, k)[0]
        if v in shift and v != shift[v]: struct.pack_into('<I', head, k, shift[v])
    res = head + out
    struct.pack_into('<I', res, 0x0c, len(res) - 0x10 if struct.unpack_from('<I', d, 0x0c)[0] == len(d) - 0x10 else len(res))
    return bytes(res), stats
