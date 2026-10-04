import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from unicorn import *
from unicorn.mips_const import *
import disphook
MB = 0x100000; BLOB = 0x300000; PARSE = 0x200000; RET = 0x700000
ent = {b'Rookie': b'ROOKIE_KO', b'On': b'ON_KO', b'Rehab': b'REHAB_KO', b'^j1^OPTIONS': b'OPT_KO'}
for i in range(3000): ent[f'word{i}'.encode()] = f'ko{i}'.encode()
POOL = [0x400000]
STORE = {}
def place(b):
    a = (POOL[0] + 3) & ~3; STORE[a] = b; POOL[0] = a + len(b); return a
blob, entry, N = disphook.build(BLOB, PARSE, ent, place, lambda a, x: STORE.__setitem__(a, x))
print('blob', len(blob), 'entries', N)
mu = Uc(UC_ARCH_MIPS, UC_MODE_MIPS64 + UC_MODE_LITTLE_ENDIAN); mu.mem_map(0, 0x1000000)
mu.mem_write(MB + BLOB, blob)
for a, b in STORE.items(): mu.mem_write(MB + a, b)
# Parse 대역: v0 = a0 (넘어온 문자열 포인터), a1~t3 그대로
mu.mem_write(MB + PARSE, struct.pack('<2I', 0x03e00008, 0x00801021))   # jr ra ; addu v0,a0,zero
STR = 0x800000
def run(s):
    mu.mem_write(STR, s + b'\0')
    regs = {UC_MIPS_REG_A1: 11, UC_MIPS_REG_A2: 22, UC_MIPS_REG_A3: 33, UC_MIPS_REG_T0: 44, UC_MIPS_REG_T1: 55, UC_MIPS_REG_T2: 66, UC_MIPS_REG_T3: 77}
    for r, v in regs.items(): mu.reg_write(r, v)
    mu.reg_write(UC_MIPS_REG_A0, STR if s is not None else 0); mu.reg_write(UC_MIPS_REG_RA, RET); mu.reg_write(UC_MIPS_REG_SP, 0x900000)
    mu.emu_start(MB + entry, MB + PARSE + 8 if False else RET, count=100000)
    v0 = mu.reg_read(UC_MIPS_REG_V0)
    ok = all(mu.reg_read(r) == v for r, v in regs.items()) and mu.reg_read(UC_MIPS_REG_SP) == 0x900000
    b = bytes(mu.mem_read(v0, 32)); return b[:b.index(0)], ok
for s in (b'Rookie', b'On', b'Rehab', b'^j1^OPTIONS', b'Rookies', b'Ro', b'Hello', b'word123', b'word2999', b'word3000', b''):
    print(s, run(s))

# ---- GetQueryValue 감싸기 시험 ----
Q = 0x210000; B2 = 0x320000
mu.mem_write(MB + Q, struct.pack('<2I', 0x03e00008, 0x00801021))     # 원 함수 대역: v0 = a0
mu.mem_write(MB + B2, disphook.build_query(B2, BLOB, Q))
def runq(s):
    mu.mem_write(STR, s + b'\0'); mu.reg_write(UC_MIPS_REG_A0, STR); mu.reg_write(UC_MIPS_REG_A1, 5)
    mu.reg_write(UC_MIPS_REG_RA, RET); mu.reg_write(UC_MIPS_REG_SP, 0x900000)
    mu.emu_start(MB + B2, RET, count=100000)
    v0 = mu.reg_read(UC_MIPS_REG_V0); b = bytes(mu.mem_read(v0, 32))
    return b[:b.index(0)], mu.reg_read(UC_MIPS_REG_SP) == 0x900000
for s in (b'Rookie', b'Hello', b'word5', b''): print('Q', s, runq(s))
