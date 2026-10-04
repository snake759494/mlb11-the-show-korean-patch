"""게임 내 키보드 2벌식 한글 입력 (FE.REL).

FE.REL 키보드 객체(kb): +0x10 입력 버퍼, +0x2034 시프트, +0x2038 CAPS(→ 한/영), +0x203c 시프트 고정,
+0x2040 최대 길이, +0x2044 허용 문자 플래그.  키 처리 함수 0x7e960 (s0=kb, s5=시프트, s7=키 번호).
- 문자 입력 경로 0x7eaa4 의 `jal strlen` 재배치를 BLOB_INSERT 로: 한글 모드에서 글자 키면 버퍼를 직접 조합하고
  0x1000 을 돌려 원래 삽입을 건너뜀. 아니면 strlen 결과를 그대로 돌려 원래 동작.
- 삭제 0x7f0c0 의 화면 갱신 `jal 0x7f1f8` 재배치를 BLOB_DELETE 로: 2바이트 한글이면 1바이트 더 지운 뒤 갱신으로 넘어감.
블롭은 모듈 안 어디에 놓여도 되도록 PC 기준으로 주소를 계산한다(새 재배치 항목 없음)."""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import hangul

REG = {n: i for i, n in enumerate(['zero', 'at', 'v0', 'v1', 'a0', 'a1', 'a2', 'a3', 't0', 't1', 't2', 't3', 't4', 't5', 't6', 't7',
                                   's0', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 't8', 't9', 'k0', 'k1', 'gp', 'sp', 'fp', 'ra'])}
CALL_INSERT, CALL_DELETE = 0x7eaa4, 0x7f0ec
F_REFRESH, F_SHIFTSET, F_VALID = 0x7f1f8, 0x7f128, 0x7dd70
NKEYS = 75

class Asm:
    def __init__(self): self.ops = []; self.labels = {}
    def L(self, name): self.labels[name] = len(self.ops)
    def _i(self, op, rs, rt, imm): self.ops.append(('w', (op << 26) | (REG[rs] << 21) | (REG[rt] << 16) | (imm & 0xffff)))
    def _r(self, rs, rt, rd, sa, fn): self.ops.append(('w', (REG[rs] << 21) | (REG[rt] << 16) | (REG[rd] << 11) | (sa << 6) | fn))
    def _b(self, op, rs, rt, lab): self.ops.append(('b', op, REG[rs], REG[rt], lab))
    # 산술·논리
    def addiu(self, rt, rs, i): self._i(9, rs, rt, i)
    def slti(self, rt, rs, i): self._i(10, rs, rt, i)
    def sltiu(self, rt, rs, i): self._i(11, rs, rt, i)
    def andi(self, rt, rs, i): self._i(12, rs, rt, i)
    def ori(self, rt, rs, i): self._i(13, rs, rt, i)
    def lui(self, rt, i): self._i(15, 'zero', rt, i)
    def addu(self, rd, rs, rt): self._r(rs, rt, rd, 0, 0x21)
    def subu(self, rd, rs, rt): self._r(rs, rt, rd, 0, 0x23)
    def sltu(self, rd, rs, rt): self._r(rs, rt, rd, 0, 0x2b)
    def slt(self, rd, rs, rt): self._r(rs, rt, rd, 0, 0x2a)
    def sll(self, rd, rt, sa): self._r('zero', rt, rd, sa, 0)
    def srl(self, rd, rt, sa): self._r('zero', rt, rd, sa, 2)
    def move(self, rd, rs): self._r(rs, 'zero', rd, 0, 0x21)
    def divu(self, rs, rt): self._r(rs, rt, 'zero', 0, 0x1b)
    def mflo(self, rd): self._r('zero', 'zero', rd, 0, 0x12)
    def mfhi(self, rd): self._r('zero', 'zero', rd, 0, 0x10)
    def li(self, rt, v): self.addiu(rt, 'zero', v) if -0x8000 <= v < 0x8000 else (self.lui(rt, v >> 16), self.ori(rt, rt, v & 0xffff))
    # 메모리
    def lb(self, rt, o, b): self._i(32, b, rt, o)
    def lbu(self, rt, o, b): self._i(36, b, rt, o)
    def lhu(self, rt, o, b): self._i(37, b, rt, o)
    def lw(self, rt, o, b): self._i(35, b, rt, o)
    def sb(self, rt, o, b): self._i(40, b, rt, o)
    def sw(self, rt, o, b): self._i(43, b, rt, o)
    def sd(self, rt, o, b): self._i(63, b, rt, o)
    def ld(self, rt, o, b): self._i(55, b, rt, o)
    # 분기 (지연 슬롯은 호출 쪽에서 직접 채움)
    def beq(self, a, b, lab): self._b(4, a, b, lab)
    def bne(self, a, b, lab): self._b(5, a, b, lab)
    def blez(self, a, lab): self._b(6, a, 'zero', lab)
    def bgtz(self, a, lab): self._b(7, a, 'zero', lab)
    def b(self, lab): self._b(4, 'zero', 'zero', lab)
    def bal(self, lab): self.ops.append(('b', 1, REG['zero'], 17, lab))     # bgezal zero
    def jr(self, rs): self._r(rs, 'zero', 'zero', 0, 8)
    def jalr(self, rs): self._r(rs, 'zero', 'ra', 0, 9)
    def nop(self): self.ops.append(('w', 0))
    def data(self, b):
        b = bytes(b) + bytes((-len(b)) % 4)
        for k in range(0, len(b), 4): self.ops.append(('w', struct.unpack_from('<I', b, k)[0]))
    def assemble(self):
        out = []
        for idx, o in enumerate(self.ops):
            if o[0] == 'w': out.append(o[1])
            else:
                _, op, rs, rt, lab = o
                off = self.labels[lab] - (idx + 1)
                assert -0x8000 <= off < 0x8000
                out.append((op << 26) | (rs << 21) | (rt << 16) | (off & 0xffff))
        return b''.join(struct.pack('<I', w) for w in out)

def tables(syl_sorted):
    """조합 표.  자모 번호 = 호환 자모 0x3131 기준."""
    J = hangul.COMPAT
    cho = [hangul.CHO.find(c) for c in J]
    jung = [hangul.JUNG.find(c) for c in J]
    jong = [hangul.JONG.find(c) if c in hangul.JONG[1:] else 0 for c in J]
    p_cho = bytes(c if c >= 0 else 0xff for c in cho)
    p_jung = bytes(c if c >= 0 else 0xff for c in jung)
    p_jong = bytes(jong)
    # 키 → 자모 (일반, 시프트), 2벌식
    lay = {'q': 'ㅂㅃ', 'w': 'ㅈㅉ', 'e': 'ㄷㄸ', 'r': 'ㄱㄲ', 't': 'ㅅㅆ', 'y': 'ㅛㅛ', 'u': 'ㅕㅕ', 'i': 'ㅑㅑ', 'o': 'ㅐㅒ', 'p': 'ㅔㅖ',
           'a': 'ㅁㅁ', 's': 'ㄴㄴ', 'd': 'ㅇㅇ', 'f': 'ㄹㄹ', 'g': 'ㅎㅎ', 'h': 'ㅗㅗ', 'j': 'ㅓㅓ', 'k': 'ㅏㅏ', 'l': 'ㅣㅣ',
           'z': 'ㅋㅋ', 'x': 'ㅌㅌ', 'c': 'ㅊㅊ', 'v': 'ㅍㅍ', 'b': 'ㅠㅠ', 'n': 'ㅜㅜ', 'm': 'ㅡㅡ'}
    fe = open(os.path.join(os.path.dirname(__file__), '..', 'extract', 'FE.REL'), 'rb').read()
    ktab = fe[0x2face0:0x2face0 + 2 * NKEYS]
    keyj = bytearray([0xff] * (2 * NKEYS))
    for k in range(NKEYS):
        ch = chr(ktab[2 * k])
        if ch in lay:
            keyj[2 * k] = J.index(lay[ch][0]); keyj[2 * k + 1] = J.index(lay[ch][1])
    # 겹모음 (중성1, 중성2) → 중성
    vc = []
    for a, b, r in (('ㅗ', 'ㅏ', 'ㅘ'), ('ㅗ', 'ㅐ', 'ㅙ'), ('ㅗ', 'ㅣ', 'ㅚ'), ('ㅜ', 'ㅓ', 'ㅝ'), ('ㅜ', 'ㅔ', 'ㅞ'), ('ㅜ', 'ㅣ', 'ㅟ'), ('ㅡ', 'ㅣ', 'ㅢ')):
        vc.append(bytes([hangul.JUNG.index(a), hangul.JUNG.index(b), hangul.JUNG.index(r)]))
    vcomb = b''.join(vc) + b'\xff\xff\xff'
    # 겹받침 (종성1, 자모2) → 종성, 그리고 분리용 (겹종성 → 종성1, 자모2)
    jc = []
    for a, b, r in (('ㄱ', 'ㅅ', 'ㄳ'), ('ㄴ', 'ㅈ', 'ㄵ'), ('ㄴ', 'ㅎ', 'ㄶ'), ('ㄹ', 'ㄱ', 'ㄺ'), ('ㄹ', 'ㅁ', 'ㄻ'), ('ㄹ', 'ㅂ', 'ㄼ'),
                    ('ㄹ', 'ㅅ', 'ㄽ'), ('ㄹ', 'ㅌ', 'ㄾ'), ('ㄹ', 'ㅍ', 'ㄿ'), ('ㄹ', 'ㅎ', 'ㅀ'), ('ㅂ', 'ㅅ', 'ㅄ')):
        jc.append(bytes([hangul.JONG.index(a), J.index(b), hangul.JONG.index(r)]))
    jcomb = b''.join(jc) + b'\xff\xff\xff'
    jong2jamo = bytes(J.index(hangul.JONG[j]) if j else 0xff for j in range(28))
    vjamo = bytes(J.index(hangul.JUNG[v]) for v in range(21))   # 중성 → 자모
    syl = b''.join(struct.pack('<H', ord(c) - 0xAC00) for c in syl_sorted)
    return dict(p_cho=p_cho, p_jung=p_jung, p_jong=p_jong, keyj=bytes(keyj), vcomb=vcomb, jcomb=jcomb,
                jong2jamo=jong2jamo, vjamo=vjamo, syl=syl, n=len(syl_sorted))

def build(blob_addr, syl_sorted):
    """blob_addr: 모듈 안 블롭 오프셋. (블롭 바이트, 입력 진입점, 삭제 진입점)"""
    T = tables(syl_sorted)
    N = T['n']
    a = Asm()
    FR = 0x60   # 프레임: 0 ra, 8 base, 0x10 buf, 0x18 len, 0x20 out1, 0x24 out2, 0x28 rm, 0x30 J, 0x38 last idx
    # ---------------- 삭제 진입점 (a0 = kb, 원래 1바이트는 이미 지워짐) ----------------
    a.L('DEL')
    a.addiu('t0', 'a0', 0x10)          # 버퍼
    a.move('t1', 't0')
    a.L('del_len'); a.lbu('t2', 0, 't1'); a.bne('t2', 'zero', 'del_len'); a.addiu('t1', 't1', 1)
    a.addiu('t1', 't1', -1)            # t1 = 끝(NUL)
    a.move('t3', 'zero')               # 끝쪽 0x80 이상 바이트 수
    a.L('del_run'); a.beq('t1', 't0', 'del_chk'); a.nop()
    a.lbu('t2', -1, 't1'); a.sltiu('t4', 't2', 0x80); a.bne('t4', 'zero', 'del_chk'); a.nop()
    a.addiu('t3', 't3', 1); a.b('del_run'); a.addiu('t1', 't1', -1)
    a.L('del_chk')
    a.andi('t3', 't3', 1)
    a.beq('t3', 'zero', 'del_go'); a.nop()
    # t1 은 런 시작까지 내려가 있으므로 다시 끝을 구해 마지막 1바이트 삭제
    a.move('t1', 't0')
    a.L('del_len2'); a.lbu('t2', 0, 't1'); a.bne('t2', 'zero', 'del_len2'); a.addiu('t1', 't1', 1)
    a.sb('zero', -2, 't1')
    a.L('del_go')
    a.move('t7', 'ra')
    a.bal('del_pc'); a.nop()
    a.L('del_pc')                       # ra = 여기 주소
    a.ops.append(('fixup_refresh',))
    a.jr('t9'); a.move('ra', 't7')      # 원래 복귀 주소로 갱신 함수에 넘김
    # ---------------- 입력 진입점 (a0 = 버퍼, s0 = kb, s5 = 시프트, s7 = 키) ----------------
    a.L('INS')
    a.addiu('sp', 'sp', -FR); a.sd('ra', 0, 'sp'); a.sw('a0', 0x10, 'sp')
    a.bal('ins_pc'); a.nop()
    a.L('ins_pc'); a.ops.append(('fixup_base',))       # t8 = 블롭 시작 주소
    a.sw('t8', 8, 'sp')
    # strlen
    a.move('t1', 'a0')
    a.L('ins_len'); a.lbu('t2', 0, 't1'); a.bne('t2', 'zero', 'ins_len'); a.addiu('t1', 't1', 1)
    a.addiu('t1', 't1', -1); a.subu('t1', 't1', 'a0'); a.sw('t1', 0x18, 'sp')
    a.move('v0', 't1')
    # 한글 모드 + 글자 키?
    a.lw('t2', 0x2038, 's0'); a.beq('t2', 'zero', 'ret'); a.nop()
    a.sltiu('t2', 's7', NKEYS); a.beq('t2', 'zero', 'ret'); a.nop()
    a.lw('t3', 0x2034, 's0'); a._r('t3', 's5', 't3', 0, 0x25)      # or t3, t3, s5 : 인자 또는 객체의 시프트 상태
    a.sll('t2', 's7', 1); a.sltu('t3', 'zero', 't3'); a.addu('t2', 't2', 't3')
    a.addu('t2', 't2', 't8'); a.ops.append(('lbu_tab', 't2', 't2', 'keyj'))   # J
    a.sltiu('t3', 't2', 0xff); a.beq('t3', 'zero', 'ret'); a.nop()
    a.sw('t2', 0x30, 'sp')
    # 허용 문자 검사: valid('a', flags)
    a.li('a0', 0x61); a.lw('a1', 0x2044, 's0')
    a.ops.append(('call', F_VALID)); a.nop()
    a.lw('t8', 8, 'sp')
    a.move('t2', 'v0'); a.lw('v0', 0x18, 'sp')          # 허용되지 않으면 길이를 돌려 원래 경로로
    a.beq('t2', 'zero', 'ret'); a.nop()
    # 마지막 글자 해석: t5 = 종류(0 없음, 1 음절, 2 자모), t6 = 인덱스
    a.li('t5', 0); a.li('t7', -1); a.sw('t7', 0x20, 'sp'); a.sw('t7', 0x24, 'sp'); a.sw('zero', 0x28, 'sp')
    a.lw('t0', 0x10, 'sp'); a.lw('t1', 0x18, 'sp')
    a.sltiu('t2', 't1', 2); a.bne('t2', 'zero', 'decided'); a.nop()
    a.addu('t3', 't0', 't1')            # 끝
    a.lbu('t4', -1, 't3'); a.sltiu('t2', 't4', 0x80); a.bne('t2', 'zero', 'decided'); a.nop()
    a.lbu('t2', -2, 't3'); a.addiu('t2', 't2', -0x80); a.sll('t2', 't2', 7); a.addiu('t4', 't4', -0x80); a.addu('t6', 't2', 't4')
    a.sltiu('t2', 't6', N); a.beq('t2', 'zero', 'is_jamo'); a.nop()
    a.b('decided'); a.li('t5', 1)
    a.L('is_jamo'); a.sltiu('t2', 't6', N + 51); a.beq('t2', 'zero', 'decided'); a.nop()
    a.li('t5', 2); a.addiu('t6', 't6', -N)
    a.L('decided')
    a.sw('t6', 0x38, 'sp')
    # 음절이면 초·중·종 분해: s? 사용 금지 → t0=cho t1=jung t2=jong
    a.li('t7', 1); a.bne('t5', 't7', 'no_split'); a.nop()
    a.sll('t3', 't6', 1); a.addu('t3', 't3', 't8'); a.ops.append(('lhu_tab', 't3', 't3', 'syl'))
    a.li('t4', 588); a.divu('t3', 't4'); a.mflo('t0'); a.mfhi('t3')
    a.li('t4', 28); a.divu('t3', 't4'); a.mflo('t1'); a.mfhi('t2')
    a.L('no_split')
    a.lw('t9', 0x30, 'sp')              # J
    a.addu('t3', 't9', 't8'); a.ops.append(('lbu_tab', 'a2', 't3', 'p_jung'))   # a2 = 입력 중성(0xff=자음)
    a.sltiu('t3', 'a2', 0xff); a.bne('t3', 'zero', 'vowel'); a.nop()
    # ===== 자음 입력 =====
    a.li('t7', 1); a.bne('t5', 't7', 'app_jamo'); a.nop()
    a.addu('t3', 't9', 't8'); a.ops.append(('lbu_tab', 'a3', 't3', 'p_jong'))   # a3 = 받침 가능한 종성
    a.bne('t2', 'zero', 'has_jong'); a.nop()
    a.beq('a3', 'zero', 'app_jamo'); a.nop()
    a.move('a1', 'a3'); a.b('comp_rep'); a.nop()
    a.L('has_jong')                      # 겹받침 (t2, J) 찾기
    a.ops.append(('la', 't3', 'jcomb'))
    a.L('jc_loop'); a.lbu('t4', 0, 't3'); a.li('t7', 0xff); a.beq('t4', 't7', 'app_jamo'); a.nop()
    a.bne('t4', 't2', 'jc_next'); a.nop()
    a.lbu('t4', 1, 't3'); a.bne('t4', 't9', 'jc_next'); a.nop()
    a.lbu('a1', 2, 't3'); a.b('comp_rep'); a.nop()
    a.L('jc_next'); a.b('jc_loop'); a.addiu('t3', 't3', 3)
    a.L('comp_rep')                      # (t0, t1, a1) 로 마지막 음절 교체
    a.move('a0', 't0'); a.move('a2', 't1'); a.ops.append(('call_local', 'FIND')); a.nop()
    a.lw('t8', 8, 'sp')
    a.slti('t3', 'v0', 0); a.bne('t3', 'zero', 'app_jamo_r'); a.nop()
    a.sw('v0', 0x20, 'sp'); a.li('t3', 2); a.b('emit'); a.sw('t3', 0x28, 'sp')
    a.L('app_jamo_r'); a.lw('t9', 0x30, 'sp')
    a.L('app_jamo')                      # 자모 그대로 덧붙임
    a.addiu('t3', 't9', N); a.b('emit'); a.sw('t3', 0x20, 'sp')
    # ===== 모음 입력 (a2 = 입력 중성) =====
    a.L('vowel')
    a.sw('a2', 0x40, 'sp')
    a.li('t7', 1); a.bne('t5', 't7', 'v_notsyl'); a.nop()
    a.bne('t2', 'zero', 'v_split'); a.nop()
    # 받침 없는 음절: 겹모음?
    a.move('a0', 't1'); a.move('a1', 'a2'); a.ops.append(('call_local', 'VCOMB')); a.nop()
    a.lw('t8', 8, 'sp'); a.lw('t9', 0x30, 'sp')
    a.li('t3', 0xff); a.beq('v0', 't3', 'app_jamo'); a.nop()
    a.lw('t6', 0x38, 'sp')               # 다시 분해 (호출 사이 t 레지스터 보존 안 됨)
    a.sll('t3', 't6', 1); a.addu('t3', 't3', 't8'); a.ops.append(('lhu_tab', 't3', 't3', 'syl'))
    a.li('t4', 588); a.divu('t3', 't4'); a.mflo('a0')
    a.move('a2', 'v0'); a.move('a1', 'zero')
    # FIND(cho=a0, jung=a2, jong=a1)
    a.ops.append(('call_local', 'FIND')); a.nop()
    a.lw('t8', 8, 'sp'); a.lw('t9', 0x30, 'sp')
    a.slti('t3', 'v0', 0); a.bne('t3', 'zero', 'app_jamo'); a.nop()
    a.sw('v0', 0x20, 'sp'); a.li('t3', 2); a.b('emit'); a.sw('t3', 0x28, 'sp')
    # 받침 있는 음절: 받침 분리
    a.L('v_split')
    a.sw('t0', 0x48, 'sp'); a.sw('t1', 0x4c, 'sp')
    a.ops.append(('la', 't3', 'jcomb'))
    a.L('js_loop'); a.lbu('t4', 0, 't3'); a.li('t7', 0xff); a.beq('t4', 't7', 'js_single'); a.nop()
    a.lbu('t4', 2, 't3'); a.bne('t4', 't2', 'js_next'); a.nop()
    a.lbu('t2', 0, 't3'); a.lbu('t4', 1, 't3'); a.b('js_have'); a.nop()   # t2 = 남는 종성, t4 = 넘어갈 자모
    a.L('js_next'); a.b('js_loop'); a.addiu('t3', 't3', 3)
    a.L('js_single')
    a.addu('t3', 't2', 't8'); a.ops.append(('lbu_tab', 't4', 't3', 'jong2jamo')); a.move('t2', 'zero')
    a.L('js_have')
    a.addu('t3', 't4', 't8'); a.ops.append(('lbu_tab', 't4', 't3', 'p_cho'))   # 넘어갈 초성
    a.sw('t4', 0x50, 'sp')
    a.lw('a0', 0x48, 'sp'); a.lw('a2', 0x4c, 'sp'); a.move('a1', 't2')
    a.ops.append(('call_local', 'FIND')); a.nop()
    a.lw('t8', 8, 'sp'); a.lw('t9', 0x30, 'sp')
    a.slti('t3', 'v0', 0); a.bne('t3', 'zero', 'app_jamo'); a.nop()
    a.sw('v0', 0x20, 'sp')
    a.lw('a0', 0x50, 'sp'); a.lw('a2', 0x40, 'sp'); a.move('a1', 'zero')
    a.ops.append(('call_local', 'FIND')); a.nop()
    a.lw('t8', 8, 'sp'); a.lw('t9', 0x30, 'sp')
    a.slti('t3', 'v0', 0); a.bne('t3', 'zero', 'app_jamo'); a.nop()
    a.sw('v0', 0x24, 'sp'); a.li('t3', 2); a.b('emit'); a.sw('t3', 0x28, 'sp')
    # 음절이 아님: 앞이 자음 자모면 초성+모음, 모음 자모면 겹모음
    a.L('v_notsyl')
    a.li('t7', 2); a.bne('t5', 't7', 'app_jamo'); a.nop()
    a.lw('t6', 0x38, 'sp')
    a.addu('t3', 't6', 't8'); a.ops.append(('lbu_tab', 'a0', 't3', 'p_cho'))
    a.li('t3', 0xff); a.beq('a0', 't3', 'v_jj'); a.nop()
    a.lw('a2', 0x40, 'sp'); a.move('a1', 'zero')
    a.ops.append(('call_local', 'FIND')); a.nop()
    a.lw('t8', 8, 'sp'); a.lw('t9', 0x30, 'sp')
    a.slti('t3', 'v0', 0); a.bne('t3', 'zero', 'app_jamo'); a.nop()
    a.sw('v0', 0x20, 'sp'); a.li('t3', 2); a.b('emit'); a.sw('t3', 0x28, 'sp')
    a.L('v_jj')
    a.addu('t3', 't6', 't8'); a.ops.append(('lbu_tab', 'a0', 't3', 'p_jung'))
    a.lw('a1', 0x40, 'sp'); a.ops.append(('call_local', 'VCOMB')); a.nop()
    a.lw('t8', 8, 'sp'); a.lw('t9', 0x30, 'sp')
    a.li('t3', 0xff); a.beq('v0', 't3', 'app_jamo'); a.nop()
    a.addu('t3', 'v0', 't8'); a.ops.append(('lbu_tab', 't3', 't3', 'vjamo'))
    a.addiu('t3', 't3', N); a.sw('t3', 0x20, 'sp'); a.li('t3', 2); a.b('emit'); a.sw('t3', 0x28, 'sp')
    # ===== 버퍼에 반영 =====
    a.L('emit')
    a.lw('t0', 0x10, 'sp'); a.lw('t1', 0x18, 'sp'); a.lw('t2', 0x28, 'sp')
    a.subu('t1', 't1', 't2')             # 새 기준 길이
    a.lw('t3', 0x20, 'sp'); a.lw('t4', 0x24, 'sp')
    a.addiu('t5', 't1', 2)
    a.slti('t6', 't4', 0); a.bne('t6', 'zero', 'e_len'); a.nop()
    a.addiu('t5', 't5', 2)
    a.L('e_len')
    a.lw('t6', 0x2040, 's0'); a.sltu('t6', 't6', 't5'); a.bne('t6', 'zero', 'done'); a.nop()   # 최대 길이 초과
    a.addu('t0', 't0', 't1')
    a.srl('t6', 't3', 7); a.addiu('t6', 't6', 0x80); a.sb('t6', 0, 't0')
    a.andi('t6', 't3', 0x7f); a.addiu('t6', 't6', 0x80); a.sb('t6', 1, 't0')
    a.slti('t6', 't4', 0); a.bne('t6', 'zero', 'e_term'); a.addiu('t0', 't0', 2)
    a.srl('t6', 't4', 7); a.addiu('t6', 't6', 0x80); a.sb('t6', 0, 't0')
    a.andi('t6', 't4', 0x7f); a.addiu('t6', 't6', 0x80); a.sb('t6', 1, 't0')
    a.addiu('t0', 't0', 2)
    a.L('e_term'); a.sb('zero', 0, 't0')
    # 화면 갱신, 시프트 자동 해제
    a.move('a0', 's0'); a.ops.append(('call', F_REFRESH)); a.nop()
    a.lw('t0', 0x2034, 's0'); a._r('t0', 's5', 't0', 0, 0x25)
    a.beq('t0', 'zero', 'done'); a.nop()
    a.lw('t0', 0x203c, 's0'); a.bne('t0', 'zero', 'done'); a.nop()
    a.lw('t8', 8, 'sp'); a.move('a0', 's0'); a.move('a1', 'zero'); a.ops.append(('call', F_SHIFTSET)); a.nop()
    a.L('done')
    a.li('v0', 0x1000)
    a.L('ret')
    a.ld('ra', 0, 'sp'); a.jr('ra'); a.addiu('sp', 'sp', FR)
    a.L('ret_len')
    a.b('ret'); a.nop()
    # ---------------- 보조: VCOMB(a0 중성1, a1 중성2) → v0 중성 또는 0xff ----------------
    a.L('VCOMB')
    a.ops.append(('la_ra', 't3', 'vcomb'))
    a.L('vc_loop'); a.lbu('t4', 0, 't3'); a.li('v0', 0xff); a.beq('t4', 'v0', 'vc_end'); a.nop()
    a.bne('t4', 'a0', 'vc_next'); a.nop()
    a.lbu('t4', 1, 't3'); a.bne('t4', 'a1', 'vc_next'); a.nop()
    a.lbu('v0', 2, 't3'); a.L('vc_end'); a.jr('ra'); a.nop()
    a.L('vc_next'); a.b('vc_loop'); a.addiu('t3', 't3', 3)
    # ---------------- 보조: FIND(a0 cho, a2 jung, a1 jong) → v0 인덱스 또는 -1 (이진 탐색) ----------------
    a.L('FIND')
    # key = cho*588 + jung*28 + jong  (곱셈 없이: 시프트·덧셈)
    a.sll('t4', 'a0', 9); a.sll('t5', 'a0', 6); a.addu('t4', 't4', 't5'); a.sll('t5', 'a0', 3); a.addu('t4', 't4', 't5')
    a.sll('t5', 'a0', 2); a.addu('t4', 't4', 't5')                 # 512+64+8+4 = 588
    a.sll('t5', 'a2', 4); a.addu('t4', 't4', 't5'); a.sll('t5', 'a2', 3); a.addu('t4', 't4', 't5')
    a.sll('t5', 'a2', 2); a.addu('t4', 't4', 't5')                 # 16+8+4 = 28
    a.addu('t4', 't4', 'a1')
    a.ops.append(('la_ra', 't7', 'syl'))
    a.li('t5', 0); a.li('t6', N)                                   # [lo, hi)
    a.L('f_loop'); a.subu('t0', 't6', 't5'); a.blez('t0', 'f_miss'); a.nop()
    a.addu('t0', 't5', 't6'); a.srl('t0', 't0', 1)
    a.sll('t1', 't0', 1); a.addu('t1', 't1', 't7'); a.lhu('t1', 0, 't1')
    a.beq('t1', 't4', 'f_hit'); a.nop()
    a.sltu('t2', 't1', 't4'); a.beq('t2', 'zero', 'f_lo'); a.nop()
    a.b('f_loop'); a.addiu('t5', 't0', 1)
    a.L('f_lo'); a.b('f_loop'); a.move('t6', 't0')
    a.L('f_hit'); a.jr('ra'); a.move('v0', 't0')
    a.L('f_miss'); a.jr('ra'); a.li('v0', -1)
    # ---------------- 데이터 ----------------
    order = ['keyj', 'p_cho', 'p_jung', 'p_jong', 'vcomb', 'jcomb', 'jong2jamo', 'vjamo', 'syl']
    for k in order:
        a.L(k); a.data(T[k])
    # FIND·VCOMB 은 자기 ra 로 주소를 구할 수 없으므로(호출 직후 ra=호출지) 'la_ra' 는 블롭 시작 주소 t8 기준
    # ---- 2차 조립: 의사 명령 확장 ----
    return _finalize(a, blob_addr)

def _finalize(a, blob_addr):
    """의사 명령 확장 후 조립.  t8 = 블롭 시작 주소(런타임).
    fixup_base(3): t8 = ra - off(ins_pc)          fixup_refresh(3): t9 = ra + (F_REFRESH - blob - off(del_pc))
    lbu_tab/lhu_tab(3): rd = mem[rs + off(tab)]   la/la_ra(3): rd = t8 + off(tab)
    call(4): t9 = t8 + (target - blob); jalr t9  (지연 슬롯은 호출 쪽 nop)
    call_local(1): bal label (지연 슬롯은 호출 쪽 nop)"""
    size = {'fixup_base': 3, 'fixup_refresh': 3, 'lbu_tab': 3, 'lhu_tab': 3, 'la': 3, 'la_ra': 3, 'call': 4, 'call_local': 1}
    pos = []; n = 0
    for o in a.ops:
        pos.append(n); n += size.get(o[0], 1)
    lab = {k: (pos[v] if v < len(pos) else n) for k, v in a.labels.items()}
    def off(name): return lab[name] * 4
    def hi(v): return ((v + 0x8000) >> 16) & 0xffff
    words = []
    for i, o in enumerate(a.ops):
        k = o[0]; here = pos[i]
        if k == 'w': words.append(o[1])
        elif k == 'b':
            _, op, rs, rt, l = o; offw = lab[l] - (here + 1); assert -0x8000 <= offw < 0x8000
            words.append((op << 26) | (rs << 21) | (rt << 16) | (offw & 0xffff))
        elif k == 'fixup_base':
            v = -off('ins_pc'); words += [_enc_lui('t8', hi(v)), _enc_addiu('t8', 't8', v & 0xffff), _enc_addu('t8', 'ra', 't8')]
        elif k == 'fixup_refresh':
            v = F_REFRESH - blob_addr - off('del_pc'); words += [_enc_lui('t9', hi(v)), _enc_addiu('t9', 't9', v & 0xffff), _enc_addu('t9', 'ra', 't9')]
        elif k in ('lbu_tab', 'lhu_tab'):
            _, rd, rs, t = o; v = off(t); ins = _enc_lbu if k == 'lbu_tab' else _enc_lhu
            words += [_enc_lui('at', hi(v)), _enc_addu('at', 'at', rs), ins(rd, v & 0xffff, 'at')]
        elif k in ('la', 'la_ra'):
            _, rd, t = o; v = off(t); words += [_enc_lui(rd, hi(v)), _enc_addiu(rd, rd, v & 0xffff), _enc_addu(rd, rd, 't8')]
        elif k == 'call':
            v = o[1] - blob_addr; words += [_enc_lui('t9', hi(v)), _enc_addiu('t9', 't9', v & 0xffff), _enc_addu('t9', 't9', 't8'), _enc_jalr('t9')]
        elif k == 'call_local':
            offw = lab[o[1]] - (here + 1); words.append((1 << 26) | (17 << 16) | (offw & 0xffff))
        else: raise ValueError(k)
    assert len(words) == n
    blob = b''.join(struct.pack('<I', w) for w in words)
    return blob, blob_addr + off('INS'), blob_addr + off('DEL')

def _enc_i(op, rs, rt, imm): return (op << 26) | (REG[rs] << 21) | (REG[rt] << 16) | (imm & 0xffff)
def _enc_lui(rt, imm): return _enc_i(15, 'zero', rt, imm)
def _enc_addiu(rt, rs, imm): return _enc_i(9, rs, rt, imm)
def _enc_lbu(rt, imm, b): return _enc_i(36, b, rt, imm)
def _enc_lhu(rt, imm, b): return _enc_i(37, b, rt, imm)
def _enc_addu(rd, rs, rt): return (REG[rs] << 21) | (REG[rt] << 16) | (REG[rd] << 11) | 0x21
def _enc_jalr(rs): return (REG[rs] << 21) | (REG['ra'] << 11) | 9

def patch_relocs(d, ins_addr, del_addr):
    """FE.REL 의 두 호출 재배치를 블롭으로."""
    d = bytearray(d); h = struct.unpack_from('<12I', d, 0); done = 0
    for i in range(h[2]):
        p = h[1] + 12 * i
        o, info, add = struct.unpack_from('<3I', d, p)
        if o == CALL_INSERT:
            assert info & 0xff == 4; struct.pack_into('<3I', d, p, o, 4, ins_addr); done += 1
        elif o == CALL_DELETE:
            assert info == 4 and add == F_REFRESH; struct.pack_into('<3I', d, p, o, 4, del_addr); done += 1
    assert done == 2, done
    return bytes(d)
