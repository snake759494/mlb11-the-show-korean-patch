"""필요한 만큼만 쓰는 R5900 어셈블러."""
R = {n: i for i, n in enumerate(['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
                                  's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra'])}
def _i(op, rs, rt, imm): return (op << 26) | (R[rs] << 21) | (R[rt] << 16) | (imm & 0xffff)
def _r(rs, rt, rd, sa, fn): return (R[rs] << 21) | (R[rt] << 16) | (R[rd] << 11) | (sa << 6) | fn
def addiu(rt, rs, imm): return _i(9, rs, rt, imm)
def sltiu(rt, rs, imm): return _i(11, rs, rt, imm)
def lbu(rt, off, base): return _i(36, base, rt, off)
def lhu(rt, off, base): return _i(37, base, rt, off)
def lw(rt, off, base): return _i(35, base, rt, off)
def sb(rt, off, base): return _i(40, base, rt, off)
def sh(rt, off, base): return _i(41, base, rt, off)
def sd(rt, off, base): return _i(63, base, rt, off)
def ld(rt, off, base): return _i(55, base, rt, off)
def sq(rt, off, base): return _i(31, base, rt, off)
def lq(rt, off, base): return _i(30, base, rt, off)
def addu(rd, rs, rt): return _r(rs, rt, rd, 0, 0x21)
def move(rd, rs): return _r(rs, 'zero', rd, 0, 0x2d)      # daddu rd, rs, zero
def jr(rs): return _r(rs, 'zero', 'zero', 0, 8)
def bne(rs, rt, off): return _i(5, rs, rt, off)
def beq(rs, rt, off): return _i(4, rs, rt, off)
def jal0(): return 3 << 26          # 대상은 재배치(R_MIPS_26)로 채움
NOP = 0
def xori(rt, rs, imm): return _i(14, rs, rt, imm)
def subu(rd, rs, rt): return _r(rs, rt, rd, 0, 0x23)
def sltu(rd, rs, rt): return _r(rs, rt, rd, 0, 0x2b)
