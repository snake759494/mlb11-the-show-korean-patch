"""한글 글꼴.  음절 순번 i → 리드 0x80 + i//128, 트레일 0x80 + i%128.
- i < 896 (리드 0x80~0x86): english.bin 의 한글 페이지 7개 + english.tx2(512x512)에 그림.
  english.bin 은 첫 글자 0x20 으로 읽히므로 페이지 표는 224칸, [트레일-0x20]에 기록.
- 나머지(리드 0x87~0x8B): symbols.bin 의 한글 페이지 5개 + symbols.tx2(512x512).
  symbols.bin 은 첫 글자 -1 → 페이지 표 257칸, [트레일+1]에 기록.
텍스처는 원래 글리프 영역(왼쪽 위 64폭)을 그대로 두고 나머지를 16x16 칸으로 쓴다."""
import struct, os, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__)); import tx2
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FONT = os.path.join(ROOT, os.environ.get('KO_FONT', 'NanumSquareNeo-dEb.ttf'))
PX = int(os.environ.get('KO_PX', 15))
CELL = 16
TW = TH = 512
KE, KS = 7, 5
CAP = (KE + KS) * 128
LEVELS = 16
GLYPH = dict(w=CELL - 1, h=CELL - 1, yoff=int(os.environ.get('KO_YOFF', -2)), pre=0, post=int(os.environ.get('KO_POST', 0)))
def encode_map(sylls):
    assert len(sylls) <= CAP, len(sylls)
    return {s: bytes([0x80 + i // 128, 0x80 + i % 128]) for i, s in enumerate(sylls)}
def _reduce_palette(px, pal, n):
    px = px.copy(); pal = pal.astype(int)
    used = list(np.unique(px))
    cnt = {c: int((px == c).sum()) for c in used}
    while len(used) > n:
        c = min(used, key=lambda k: cnt[k])
        rest = [k for k in used if k != c]
        t = rest[int(np.argmin([((pal[k] - pal[c]) ** 2).sum() for k in rest]))]
        px[px == c] = t; cnt[t] += cnt[c]; used.remove(c)
    remap = np.zeros(256, np.uint8); newpal = np.zeros((256, 4), np.uint8)
    for i, c in enumerate(sorted(used)): remap[c] = i; newpal[i] = pal[c]
    return remap[px], newpal, len(used)
def render(ch, font):
    im = Image.new('L', (CELL, CELL), 0)
    ImageDraw.Draw(im).text((0, -1), ch, font=font, fill=255)
    return np.array(im)
def _rec(x, y):
    g = GLYPH
    # UV 를 반 텍셀 안쪽으로: 쌍선형 보간이 이웃 칸을 읽지 않게
    r = struct.pack('<4f5h', x + 0.5, y + 0.5, x + CELL - 0.5, y + CELL - 0.5, g['w'], g['h'], g['yoff'], g['pre'], g['post'])
    return r + bytes(28 - len(r))
def _one(fbin, ftx, sylls, npage, first, tabn, font):
    px0, pal0 = tx2.read(ftx)
    h0, w0 = px0.shape
    px0, pal, n = _reduce_palette(px0, pal0, 256 - LEVELS)
    transp = [i for i in range(n) if pal[i][3] == 0]
    for k in range(LEVELS):
        pal[256 - LEVELS + k] = (240, 240, 240, round(0x80 * k / (LEVELS - 1)))
    lev0 = transp[0]
    img = np.full((TH, TW), lev0, np.uint8); img[:h0, :w0] = px0
    cells = [(x, y) for y in range(0, TH, CELL) for x in range(0, TW, CELL) if not (x < w0 and y < h0)]
    assert len(cells) >= len(sylls), (len(cells), len(sylls))
    n0, = struct.unpack_from('<I', fbin, 0)
    cnt = list(struct.unpack_from(f'<{n0}I', fbin, 4))
    glyphs = fbin[4 + 4 * n0:]
    pages = [[bytes(28)] * tabn for _ in range(npage)]
    for i, s in enumerate(sylls):
        x, y = cells[i]
        q = np.round(render(s, font).astype(int) * (LEVELS - 1) / 255).astype(int)
        img[y:y + CELL, x:x + CELL] = np.where(q == 0, lev0, 256 - LEVELS + q).astype(np.uint8)
        pages[i // 128][0x80 + i % 128 - first] = _rec(x, y)
    out = struct.pack('<I', n0 + npage) + struct.pack(f'<{n0 + npage}I', *cnt, *([tabn] * npage)) + glyphs
    for p in pages: out += b''.join(p)
    return out, tx2.write(ftx, img, pal), img, pal
def build(eng_bin, eng_tx2, sym_bin, sym_tx2, sylls):
    font = ImageFont.truetype(FONT, PX)
    a = sylls[:KE * 128]; b = sylls[KE * 128:]
    eb, et, ei, ep = _one(eng_bin, eng_tx2, a, KE, 0x20, 0xE0, font)
    sb, st, si, sp = _one(sym_bin, sym_tx2, b, KS, -1, 257, font)
    return {'eng_bin': eb, 'eng_tx2': et, 'sym_bin': sb, 'sym_tx2': st, 'imgs': ((ei, ep), (si, sp))}
