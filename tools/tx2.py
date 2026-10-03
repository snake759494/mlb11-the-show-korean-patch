"""IFF0TX00 단일 프레임 8bpp 텍스처 (PSMT8, CT32로 스위즐 업로드) 읽기·쓰기."""
import struct, numpy as np, os, sys
sys.path.insert(0, os.path.dirname(__file__)); import swz
_csm = np.arange(256); _csm = (_csm & 0xe7) | ((_csm & 8) << 1) | ((_csm & 16) >> 1)
PAL, PIX = 0x2b0, 0x700
def read(d):
    w, h = struct.unpack_from('<2H', d, 0x20)
    pal = np.frombuffer(d[PAL:PAL + 0x400], np.uint8).reshape(256, 4)[_csm].copy()
    px = swz.unswizzle8(d[PIX:PIX + w * h], w, h)
    return px, pal
def rgba(px, pal):
    a = pal[px].astype(np.uint16); a[..., 3] = np.minimum(a[..., 3] * 2, 255); return a.astype(np.uint8)
def _blocks8(w, h):
    """PSMT8 VRAM 블록 수(TBW 기준 페이지 128x64, 블록 16x16 스위즐 배치) + CLUT 4."""
    BL = [[0, 1, 4, 5, 16, 17, 20, 21], [2, 3, 6, 7, 18, 19, 22, 23], [8, 9, 12, 13, 24, 25, 28, 29], [10, 11, 14, 15, 26, 27, 30, 31]]
    tbw = max(2, w // 64)
    pw = (tbw * 64) // 128
    mx = 0
    for y in range(0, h, 16):
        for x in range(0, w, 16):
            page = (y // 64) * pw + x // 128
            b = page * 32 + BL[(y % 64) // 16][(x % 128) // 16]
            mx = max(mx, b)
    return mx + 1 + 4
def write(tpl, px, pal):
    """tpl: 같은 형식(8bpp 1프레임)의 원본 파일 바이트를 틀로 사용."""
    h, w = px.shape
    d = bytearray(tpl[:PIX])
    size = PIX + w * h + 0x20
    tbw = max(2, w // 64)
    struct.pack_into('<I', d, 0x0c, size - 0x30)
    struct.pack_into('<2H', d, 0x20, w, h)
    struct.pack_into('<I', d, 0x4c, size - 0x70)
    struct.pack_into('<H', d, 0x5a, _blocks8(w, h))
    struct.pack_into('<I', d, 0x68, w * h + 0x4a0)
    lw = {8: 3, 16: 4, 32: 5, 64: 6, 128: 7, 256: 8, 512: 9, 1024: 10}
    tex0 = struct.unpack_from('<Q', d, 0x78)[0]
    tex0 &= ~((0x3f << 14) | (0xf << 26) | (0xf << 30))
    tex0 |= (tbw << 14) | (lw[w] << 26) | (lw[h] << 30)
    struct.pack_into('<Q', d, 0x78, tex0)
    struct.pack_into('<I', d, 0x110, 0x30000005 | (w * h // 16))
    for o in (0x100, 0x190):    # BITBLTBUF SBW / DBW
        d[o + 2] = tbw; d[o + 6] = max(1, tbw // 2)
    struct.pack_into('<2I', d, 0x1b0, w // 2, h // 2)   # TRXREG (팔레트 패킷 쪽 사본)
    struct.pack_into('<2I', d, 0x6d0, w // 2, h // 2)   # TRXREG (이미지 전송)
    assert w * h // 16 < 0x8000
    struct.pack_into('<H', d, 0x6f0, w * h // 16)        # GIF IMAGE NLOOP
    inv = np.argsort(_csm)
    d[PAL:PAL + 0x400] = pal.astype(np.uint8)[inv].tobytes()
    d += swz.swizzle8(px.astype(np.uint8))
    d += tpl[-0x20:]
    assert len(d) == size
    return bytes(d)
