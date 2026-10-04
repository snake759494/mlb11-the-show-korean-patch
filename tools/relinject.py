"""REL 문자열 번역 주입 (파일 크기 불변).
- 번역할 문자열의 원래 칸(문자열 + 뒤 0 패딩)을 모아 풀로 쓰고, 번역문을 다시 배치한 뒤
  그 문자열을 가리키는 재배치 항목(R32/HI16/LO16, 구역 상대)의 addend 를 새 주소로 바꾼다.
- 옮길 수 없는 문자열(내부를 가리키는 참조가 있거나, 칸 뒤가 다른 참조 대상이 아닌 배열 의심): 제자리에 들어가면 교체, 아니면 원문 유지."""
import struct, sys, os, collections
sys.path.insert(0, os.path.dirname(__file__)); import rel, relstr
def inject(d, enc_map, log=None, allow=None, reserve=0, extra=None):
    """d: REL bytes, enc_map: 원문(str) -> 게임 바이트(bytes). 새 REL bytes 와 통계."""
    d = bytearray(d)
    h = struct.unpack_from('<12I', d, 0)
    R = []
    for i in range(h[2]):
        o, info, a = struct.unpack_from('<3I', d, h[1] + 12 * i)
        R.append((i, o, info & 0xff, info >> 8, a))
    tgt = collections.defaultdict(list)       # 주소 -> 재배치 번호들
    for i, o, ty, si, a in R:
        if si == 0 and ty in (2, 5, 6): tgt[a].append(i)
    fields = set()
    for i, o, ty, si, a in R:
        for k in range(4): fields.add(o + k)
    addrs = sorted(tgt)
    import bisect
    end_img = h[5]
    cand = []
    for a in addrs:
        if a <= 0 or a >= end_img or d[a - 1] != 0: continue
        e = d.find(b'\0', a)
        s = bytes(d[a:e])
        if not s: continue
        try: t = s.decode('latin1')
        except: continue
        if t not in enc_map: continue
        if allow is not None and not allow(a, t): continue
        new = enc_map[t]
        if new == s: continue
        # 칸 끝: 다음 0 아닌 바이트
        z = e
        while z < end_img and d[z] == 0: z += 1
        # 칸 안쪽(시작 제외)을 가리키는 참조 / 재배치 필드가 있으면 안 됨
        j = bisect.bisect_right(addrs, a)
        nxt = addrs[j] if j < len(addrs) else end_img
        interior = nxt < e + 1
        slot_end = min(z, nxt)
        movable = (not interior) and (z == nxt or z >= end_img) and not any(x in fields for x in range(a, slot_end))
        cand.append((a, e, slot_end, t, new, movable))
    st = {'inplace': 0, 'moved': 0, 'kept': 0, 'kept_list': [], 'done': set()}
    pool = []                 # (start, end) 쓸 수 있는 칸
    moves = []
    for a, e, se, t, new, mv in cand:
        if mv:
            pool.append([a, se]); moves.append((a, t, new))
        elif len(new) <= e - a:
            d[a:e] = new + bytes(e - a - len(new)); st['inplace'] += 1; st['done'].add(t)
        else:
            st['kept'] += 1; st['kept_list'].append(t)
    st['pool'] = sum(se - a for a, se in pool); st['need'] = sum(len(n) + 1 for a, t, n in moves)
    # 원래 칸을 비우고 큰 것부터 배치(first-fit decreasing)
    for a, se in pool: d[a:se] = bytes(se - a)
    pool.sort()
    # 인접한 칸을 합쳐 연속 공간으로
    merged = []
    for a0, b0 in pool:
        if merged and merged[-1][1] == a0: merged[-1][1] = b0
        else: merged.append([a0, b0])
    free = merged
    st['reserved'] = None
    if reserve:
        for f in sorted(free, key=lambda f: f[1] - f[0], reverse=True):
            s0 = (f[0] + 15) & ~15
            if f[1] - s0 >= reserve:
                st['reserved'] = s0; f[0] = s0 + reserve; break
        if st['reserved'] is None:
            big = sorted((f[1] - f[0] for f in free), reverse=True)[:5]
            raise AssertionError(f'no contiguous space for reserve {reserve}; largest free {big}, total free {sum(f[1]-f[0] for f in free)}')
    newaddr = {}
    for a, t, new in sorted(moves, key=lambda x: -len(x[2])):
        need = len(new) + 1
        for f in free:
            if f[1] - f[0] >= need:
                newaddr[a] = (f[0], new); f[0] += need; break
        else:
            newaddr[a] = None
    for a, t, new in moves:
        r = newaddr[a]
        if r is None:
            st['kept'] += 1; st['kept_list'].append(t); r = None
        if r is None:
            # 원문을 다시 어딘가에 둔다: 원래 칸이 비었으므로 풀에서 원문 길이만큼 확보
            orig = t.encode('latin1'); need = len(orig) + 1
            for f in free:
                if f[1] - f[0] >= need:
                    r = (f[0], orig); f[0] += need; break
            assert r is not None, 'pool exhausted for original'
        else:
            st['moved'] += 1; st['done'].add(t)
        na, b = r
        d[na:na + len(b)] = b; d[na + len(b)] = 0
        for i in tgt[a]:
            struct.pack_into('<I', d, h[1] + 12 * i + 8, na)
    # 추가 배치(표시 번역 문자열 등): 남은 칸에 first-fit, 주소 기록
    st['extra'] = {}
    for b in sorted(set(extra or ()), key=len, reverse=True):
        for f in free:
            if f[1] - f[0] >= len(b):
                st['extra'][b] = f[0]; d[f[0]:f[0] + len(b)] = b; f[0] += len(b); break
        else:
            raise AssertionError(f'pool exhausted for extra string ({len(b)} bytes)')
    st['free'] = [f for f in free if f[1] > f[0]]
    return bytes(d), st
