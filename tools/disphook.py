"""표시 시점 번역 훅 (uiTextHandler::Parse 앞단).

안전 규칙: 게임 데이터(내부 키로도 쓰일 수 있는 문자열)는 바꾸지 않는다. 화면에 그리기 직전 Parse 에 넘어온
문자열이 번역표에 있으면 포인터만 한글 문자열로 바꿔 넘긴다. 비교·파일·텍스처 탐색 경로는 원래 영어를 그대로 본다.

블롭 = [코드][버킷 목록 16 × (버킷 표 위치 s32, 항목 수 u32)]
버킷 표(해시 상위 4비트별, 아무 곳에나) = n × (해시 u32, (길이<<24)|문자열 위치 s24), 해시 오름차순
위치는 모두 블롭 시작 기준. 해시 = h*31 + c (부호 없는 바이트), 최대 200바이트. 해시·길이가 모두 같을 때만 교체.
사용 레지스터: a0(교체), v0 v1 at t4~t9 (Parse 인자 a1~a3 t0~t3, 스택은 건드리지 않음). ra 보존.
호출부: 각 모듈의 jal Parse 재배치(R26) 4곳을 블롭 진입점으로 바꾼다."""
import struct
from collections import Counter

PARSE = {'HRDERBY': 0xff540, 'FE': 0x243c90, 'GAME': 0x2b2738}
NB = 16
R = {n: i for i, n in enumerate(['zero', 'at', 'v0', 'v1', 'a0', 'a1', 'a2', 'a3', 't0', 't1', 't2', 't3', 't4', 't5', 't6', 't7',
                                 's0', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 't8', 't9', 'k0', 'k1', 'gp', 'sp', 'fp', 'ra'])}
def I(op, rs, rt, imm): return (op << 26) | (R[rs] << 21) | (R[rt] << 16) | (imm & 0xffff)
def Rr(rs, rt, rd, sa, fn): return (R[rs] << 21) | (R[rt] << 16) | (R[rd] << 11) | (sa << 6) | fn
def addiu(rt, rs, i): return I(9, rs, rt, i)
def lui(rt, i): return I(15, 'zero', rt, i)
def lbu(rt, o, b): return I(36, b, rt, o)
def lw(rt, o, b): return I(35, b, rt, o)
def addu(rd, rs, rt): return Rr(rs, rt, rd, 0, 0x21)
def subu(rd, rs, rt): return Rr(rs, rt, rd, 0, 0x23)
def sltu(rd, rs, rt): return Rr(rs, rt, rd, 0, 0x2b)
def sll(rd, rt, sa): return Rr('zero', rt, rd, sa, 0)
def srl(rd, rt, sa): return Rr('zero', rt, rd, sa, 2)
def sra(rd, rt, sa): return Rr('zero', rt, rd, sa, 3)
def and_(rd, rs, rt): return Rr(rs, rt, rd, 0, 0x24)
def move(rd, rs): return addu(rd, rs, 'zero')
def jr(rs): return Rr(rs, 'zero', 'zero', 0, 8)
NOP = 0
def h31(b):
    h = 0
    for c in b[:200]: h = (h * 31 + c) & 0xffffffff
    return h
def select(entries):
    """충돌(같은 해시) 항목 제외 후 정렬된 (해시, 영문, 한글) 목록."""
    rows = [(h31(en), en, ko) for en, ko in entries.items() if en and len(en) <= 200]
    hc = Counter(r[0] for r in rows)
    return sorted(r for r in rows if hc[r[0]] == 1)
def code_size(): return len(_code(0, 0)[0]) * 4 + 8 * NB

def _code(blob_addr, parse_addr, mode='parse', base_addr=None, dir_off_ext=None):
    """mode='parse': Parse 앞단 (조회 후 Parse 로 꼬리 점프).
    mode='query': GetQueryValue 감싸기 (원 함수 호출 → 반환 문자열 v0 조회 → 반환). 동적 토큰(^d0^) 값용.
    base_addr: 표·문자열 위치의 기준(첫 블롭) 주소. dir_off_ext: 기준 주소에서 버킷 목록까지 거리."""
    base_addr = blob_addr if base_addr is None else base_addr
    code = []; L = {}; br = []
    def lab(n): L[n] = len(code)
    def B(op, rs, rt, name, slot=NOP): br.append((len(code), op, rs, rt, name)); code.append(None); code.append(slot)
    if mode == 'query':
        code += [addiu('sp', 'sp', -0x20), I(63, 'sp', 'ra', 0)]              # sd ra,0(sp)
        code += [(1 << 26) | (17 << 16) | 1, NOP]
        lab('pc')
        code += [None, None, addu('t9', 'ra', 't9'), I(63, 'sp', 't9', 8)]    # t9 = 기준, sd t9,8(sp)
        fix_pc = len(code) - 4
        code += [None, None, addu('at', 'at', 't9'), Rr('at', 'zero', 'ra', 0, 9), NOP]   # jalr at (원 함수, a0/a1 그대로)
        fix_call = len(code) - 5
        code += [I(55, 'sp', 't9', 8), move('a0', 'v0')]                     # ld t9 ; a0 = 반환 문자열
    else:
        code += [move('v1', 'ra'), (1 << 26) | (17 << 16) | 1, NOP]            # bgezal zero,+1 : ra = 'pc'
        lab('pc')
        code += [None, None, addu('t9', 'ra', 't9'), move('ra', 'v1')]        # t9 = 기준 주소
        fix_pc = len(code) - 4
    B(4, 'a0', 'zero', 'go')
    # 해시(v0)·길이(v1)
    code += [move('t4', 'a0'), move('v0', 'zero'), addiu('t7', 'zero', 200)]
    lab('hl')
    code += [lbu('t5', 0, 't4')]
    B(4, 't5', 'zero', 'hd')
    code += [sll('t6', 'v0', 5), subu('v0', 't6', 'v0'), addu('v0', 'v0', 't5'), addiu('t4', 't4', 1), addiu('t7', 't7', -1)]
    B(7, 't7', 'zero', 'hl')
    B(4, 'zero', 'zero', 'go')
    lab('hd')
    code += [subu('v1', 't4', 'a0')]
    # 버킷: t8 = 버킷 표 주소, t6 = 항목 수
    code += [srl('t7', 'v0', 28), sll('t7', 't7', 3), addu('t7', 't7', 't9'), None, None]   # lw t8, DIR(t7); lw t6, DIR+4(t7)
    fix_dir = len(code) - 2
    code += [addu('t8', 't8', 't9'), move('t5', 'zero')]
    lab('bs')
    code += [subu('t7', 't6', 't5')]
    B(6, 't7', 'zero', 'go')                                                  # blez → 없음
    code += [addu('t7', 't5', 't6'), srl('t7', 't7', 1), sll('t4', 't7', 3), addu('t4', 't4', 't8'), lw('at', 0, 't4')]
    B(4, 'at', 'v0', 'eq')
    code += [sltu('at', 'at', 'v0')]
    B(4, 'at', 'zero', 'left')
    B(4, 'zero', 'zero', 'bs', addiu('t5', 't7', 1))
    lab('left')
    B(4, 'zero', 'zero', 'bs', move('t6', 't7'))
    lab('eq')
    code += [lw('at', 4, 't4'), srl('t5', 'at', 24)]
    B(5, 't5', 'v1', 'go')                                                    # 길이 다르면 그대로
    code += [sll('at', 'at', 8), sra('at', 'at', 8), addu('a0', 'at', 't9')]  # 부호 있는 24비트 → a0
    lab('go')
    if mode == 'query':
        code += [move('v0', 'a0'), I(55, 'sp', 'ra', 0), jr('ra'), addiu('sp', 'sp', 0x20)]
    else:
        code += [None, None, addu('at', 'at', 't9'), jr('at'), NOP]
        fix_go = len(code) - 5
    dir_off = len(code) * 4 if dir_off_ext is None else dir_off_ext
    # t9 = 기준 주소 = ra - pc오프셋 + (블롭 - 기준)
    adj = -L['pc'] * 4 - (blob_addr - base_addr)        # 기준 = 블롭 시작 - (블롭 - 기준)
    code[fix_pc] = lui('t9', ((adj + 0x8000) >> 16) & 0xffff); code[fix_pc + 1] = addiu('t9', 't9', adj & 0xffff)
    assert dir_off + 8 * NB < 0x8000 and dir_off >= -0x8000
    code[fix_dir] = lw('t8', dir_off, 't7'); code[fix_dir + 1] = lw('t6', dir_off + 4, 't7')
    v = parse_addr - base_addr
    hi, lo = ((v + 0x8000) >> 16) & 0xffff, v & 0xffff
    if mode == 'query':
        code[fix_call] = lui('at', hi); code[fix_call + 1] = addiu('at', 'at', lo)
    else:
        code[fix_go] = lui('at', hi); code[fix_go + 1] = addiu('at', 'at', lo)
    for pos, op, rs, rt, name in br:
        off = L[name] - (pos + 1)
        code[pos] = (op << 26) | (R[rs] << 21) | (R[rt] << 16) | (off & 0xffff)
    assert None not in code
    return code, dir_off

def build(blob_addr, parse_addr, entries, place, write=None):
    """place(bytes) → 모듈 내 위치(배치하며 기록), write(위치, bytes) → 덮어쓰기.  (블롭, 진입 주소, 항목 수)
    버킷 표 자리를 먼저 확보(조각화 전에 큰 칸)하고, 문자열을 배치한 뒤 버킷 내용을 채운다."""
    rows = select(entries)
    code, dir_off = _code(blob_addr, parse_addr)
    groups = [[r for r in rows if r[0] >> 28 == b] for b in range(NB)]
    baddr = [place(bytes(8 * len(g))) if g else None for g in groups]
    groups = [g if baddr[b] is not None else [] for b, g in enumerate(groups)]     # 버킷 자리 없으면 그 버킷 생략
    dirb = bytearray(); n = 0; seen = {}; seen = {}
    for b, g in enumerate(groups):
        recs = bytearray()
        for h, en, ko in g:                                       # g 는 해시순 → 일부 생략해도 정렬 유지
            a = seen.get(ko)                                      # 같은 한글은 한 번만 배치
            if a is None: a = seen[ko] = place(ko + b'\0')
            if a is None: continue                                # 문자열 자리 없음 → 이 항목 생략
            so = a - blob_addr
            assert -(1 << 23) <= so < (1 << 23)
            recs += struct.pack('<2I', h, (len(en) << 24) | (so & 0xffffff))
        g = recs                                                  # 실제 기록된 항목
        n += len(recs) // 8
        if g:
            (write or (lambda a, x: None))(baddr[b], bytes(recs))
            dirb += struct.pack('<iI', baddr[b] - blob_addr, len(recs) // 8)
        else:
            dirb += struct.pack('<iI', 0, 0)
    blob = b''.join(struct.pack('<I', w) for w in code) + bytes(dirb)
    return blob, blob_addr, n

def patch_calls(d, parse_addr, entry):
    d = bytearray(d); h = struct.unpack_from('<12I', d, 0); n = 0
    for i in range(h[2]):
        p = h[1] + 12 * i
        o, info, a = struct.unpack_from('<3I', d, p)
        if info == 4 and a == parse_addr:
            struct.pack_into('<3I', d, p, o, 4, entry); n += 1
    assert n == 4, n
    return bytes(d)

# ---- 동적 토큰 값(GetQueryValue) 훅 ----
DELTA = {'HRDERBY': 0, 'FE': 0x144750, 'GAME': 0x1b31f8}       # HRDERBY 기준 UI 엔진 코드 이동량
QUERY_FN = 0x100420          # GetQueryValue__Q28uiEngine13uiTextHandlerPCci (HRDERBY)
QUERY_CALL = 0xffde0         # HandleControlDynamic 안의 jal GetQueryValue (HRDERBY)
def query_size(): return len(_code(0, 0, 'query', 0, 0)[0]) * 4
def build_query(blob2_addr, base_addr, query_addr):
    """첫 블롭(base_addr)의 버킷 목록·표를 공유하는 GetQueryValue 감싸기 코드."""
    code, _ = _code(blob2_addr, query_addr, 'query', base_addr, len(_code(base_addr, 0)[0]) * 4)
    return b''.join(struct.pack('<I', w) for w in code)
def patch_query_call(d, mod, entry):
    d = bytearray(d); h = struct.unpack_from('<12I', d, 0); n = 0
    site = QUERY_CALL + DELTA[mod]; fn = QUERY_FN + DELTA[mod]
    for i in range(h[2]):
        p = h[1] + 12 * i
        o, info, a = struct.unpack_from('<3I', d, p)
        if o == site:
            assert info == 4 and a == fn, (hex(o), info, hex(a))
            struct.pack_into('<3I', d, p, o, 4, entry); n += 1
    assert n == 1, n
    return bytes(d)
