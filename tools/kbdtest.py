"""블롭 단위 시험(unicorn MIPS64): 키 입력열 → 버퍼 → 문자열."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from unicorn import *
from unicorn.mips_const import *
import kbd, ktext
MB = 0x100000            # 모듈 기준 주소
BLOB = 0x300000          # 모듈 안 블롭 오프셋
KB = 0x800000; STK = 0x900000
tr = ktext.Translator()
blob, INS, DEL = kbd.build(BLOB, tr.syl_sorted)
codes = {v: k for k, v in tr.code.items()}
fe = open(os.path.join(os.path.dirname(__file__), '..', 'extract', 'FE.REL'), 'rb').read()
ktab = fe[0x2face0:0x2face0 + 150]
keyidx = {chr(ktab[2 * k]): k for k in range(75) if ktab[2 * k]}
mu = Uc(UC_ARCH_MIPS, UC_MODE_MIPS64 + UC_MODE_LITTLE_ENDIAN)
mu.mem_map(0, 0x1000000)
mu.mem_write(MB + BLOB, blob)
RET = 0x700000
for f in (kbd.F_REFRESH, kbd.F_SHIFTSET):
    mu.mem_write(MB + f, struct.pack('<2I', 0x03e00008, 0))           # jr ra; nop
mu.mem_write(MB + kbd.F_VALID, struct.pack('<2I', 0x03e00008, 0x24020001))  # jr ra; li v0,1
mu.mem_write(RET, struct.pack('<I', 0))
def reset(maxlen=15):
    mu.mem_write(KB, bytes(0x2100))
    mu.mem_write(KB + 0x2038, struct.pack('<I', 1)); mu.mem_write(KB + 0x2040, struct.pack('<I', maxlen))
def call(entry, a0, s7=0, s5=0):
    mu.reg_write(UC_MIPS_REG_SP, STK); mu.reg_write(UC_MIPS_REG_RA, RET)
    mu.reg_write(UC_MIPS_REG_A0, a0); mu.reg_write(UC_MIPS_REG_S0, KB)
    mu.reg_write(UC_MIPS_REG_S7, s7); mu.reg_write(UC_MIPS_REG_S5, s5)
    mu.emu_start(MB + entry, RET, count=200000)
    return mu.reg_read(UC_MIPS_REG_V0)
def buf():
    b = mu.mem_read(KB + 0x10, 64); b = bytes(b[:b.index(0)]); s = ''; i = 0
    while i < len(b):
        if b[i] >= 0x80: s += codes.get(b[i:i + 2], '?'); i += 2
        else: s += chr(b[i]); i += 1
    return s
def typ(seq):
    """seq: 영문 키 (대문자 = 시프트), '<' = 삭제"""
    for ch in seq:
        if ch == '<':
            b = bytearray(mu.mem_read(KB + 0x10, 64)); n = b.index(0)
            if n: b[n - 1] = 0; mu.mem_write(KB + 0x10, bytes(b))   # 원래 1바이트 삭제
            call(DEL, KB); continue
        k = keyidx[ch.lower()]; sh = 1 if ch.isupper() else 0
        mu.mem_write(KB + 0x2034, struct.pack('<I', sh))   # 게임처럼 객체에 시프트 저장, 인자는 0
        v = call(INS, KB + 0x10, k, 0)
        if v != 0x1000:   # 원래 경로: 문자 그대로 붙임(시험용)
            b = bytearray(mu.mem_read(KB + 0x10, 64)); n = b.index(0); b[n] = ord(ch); b[n + 1] = 0; mu.mem_write(KB + 0x10, bytes(b))
    return buf()
if __name__ == '__main__':
    cases = [('Rk', '까'), ('Ehd', '똥'), ('Qkd', '빵'), ('Tkd', '쌍'), ('Wkd', '짱'), ('dO', '얘'), ('dP', '예'), ('ekR', '닦'),('dkssudgktpdy', '안녕하세요'), ('rkqt', '값'), ('rkqtdl', '값이'), ('ekfr', '닭'), ('ekfrdl', '닭이'),
             ('Rk', '까'), ('rhk', '과'), ('dnjs', '원'), ('dmlwk', '의자'), ('r', 'ㄱ'), ('k', 'ㅏ'), ('hk', 'ㅘ'),
             ('rk<', ''), ('dks<', ''), ('rlawlgns', '김지훈'), ('qkrcksgh', '박찬호'), ('rkr', '각'), ('rkrk', '가가'),
             ('Tl', '씨'), ('dhk', '와'), ('rkssk', '간나')]
    bad = 0
    for seq, want in cases:
        reset(); got = typ(seq)
        ok = got == want; bad += not ok
        print('OK ' if ok else 'BAD', seq, repr(got), repr(want))
    reset(5); print('maxlen5:', repr(typ('dkssudgktpdy')))
    print('fail', bad)
