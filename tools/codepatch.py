"""uiTextHandler::HandlePrintableChar 를 2바이트 한글 처리로 교체 + SetSymbolPage(3)→(10).
글꼴 페이지 구성(전역 번호): 0~2 영문, 3~9 한글(english.bin/tx2), 10 심볼, 11~15 한글(symbols.bin/tx2).
리드 L(0x80~0x8B): L<0x87 → 페이지 L-0x7d, 아니면 L-0x7c. 트레일(0x80~0xFF) = 그 페이지 글자.
같은 함수가 FE/GAME/HRDERBY.REL 세 곳에 있다."""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__)); import rel
from asm import *
KE = 7                  # english.bin 에 붙는 한글 페이지 수
SYMPAGE = 3 + KE        # 새 심볼 페이지 번호
# 모듈별 (HandlePrintableChar, AddInstrGlyph, HandleOutOfBounds, SetSymbolPage 인자 명령 위치)
ADDR = {'HRDERBY': (0xffef8, 0xff0c0, 0x100198, 0xa810c), 'FE': (0x244648, 0x243810, 0x2448e8, 0x53c1c),
        'GAME': (0x2b30f0, 0x2b22d0, 0x2b3390, 0x84e5c)}
SIZE = 168
def body():
    c = [addiu('sp', 'sp', -0x50), sq('s0', 0x10, 'sp'), sq('s1', 0x20, 'sp'), sq('s2', 0x30, 'sp'), sd('ra', 0, 'sp'),
         move('s1', 'a0'), move('s0', 'a1'), move('s2', 'a2'),
         lhu('a1', 4, 's1'), lw('v0', 0, 's1'), addu('v0', 'v0', 'a1'), lbu('a0', 0, 'v0'),
         lbu('v1', 0xd, 's2'), sb('v1', 0x40, 'sp'),
         sltiu('t0', 'a0', 0x80), None, move('a2', 's0'),
         addiu('v1', 'a0', 0x10000 - 0x7c), sltiu('t1', 'a0', 0x80 + KE), subu('v1', 'v1', 't1'),
         sb('v1', 0xd, 's2'), lbu('a0', 1, 'v0'),
         sltu('t1', 'zero', 'a0'), addu('a1', 'a1', 't1'), sh('a1', 4, 's1')]   # 트레일이 0(잘린 리드)이면 전진하지 않음
    L1 = len(c)
    c[15] = bne('t0', 'zero', L1 - 16)
    jal1 = len(c); c += [jal0(), move('a3', 's2'), lbu('v1', 0x40, 'sp'), sb('v1', 0xd, 's2'),
                         move('a0', 's1'), move('a1', 's0')]
    jal2 = len(c); c += [jal0(), move('a2', 's2'),
                         lhu('v0', 4, 's1'), addiu('v0', 'v0', 1), sh('v0', 4, 's1'),
                         ld('ra', 0, 'sp'), lq('s0', 0x10, 'sp'), lq('s1', 0x20, 'sp'), lq('s2', 0x30, 'sp'), jr('ra'), addiu('sp', 'sp', 0x50)]
    assert len(c) * 4 <= SIZE, len(c)
    c += [NOP] * (SIZE // 4 - len(c))
    return c, jal1, jal2
def patch(d, mod):
    d = bytearray(d)
    f, add, oob, ssp = ADDR[mod]
    h = struct.unpack_from('<12I', d, 0)
    c, j1, j2 = body()
    found = []
    for i in range(h[2]):
        o, info, a = struct.unpack_from('<3I', d, h[1] + 12 * i)
        if f <= o < f + SIZE:
            assert info == 4 and a in (add, oob), (mod, hex(o), info, hex(a))
            no = f + 4 * (j1 if a == add else j2)
            struct.pack_into('<I', d, h[1] + 12 * i, no); found.append(a)
    assert sorted(found) == sorted([add, oob]), found
    for k, w in enumerate(c): struct.pack_into('<I', d, f + 4 * k, w)
    assert struct.unpack_from('<I', d, ssp)[0] == addiu('a0', 'zero', 3), mod
    struct.pack_into('<I', d, ssp, addiu('a0', 'zero', SYMPAGE))
    return bytes(d)
