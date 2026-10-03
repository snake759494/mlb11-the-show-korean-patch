"""검증용 PCSX2(스크래치패드 휴대용 사본) 조작: 실행, 키 입력, 화면 캡처, 세이브스테이트 메모리 읽기.
사용자 PCSX2 설정은 건드리지 않는다.  키: ○=L ✕=K △=I □=J START=Return, 방향키."""
import ctypes, ctypes.wintypes as W, os, subprocess, time, glob, zipfile, sys
EMU = os.environ.get('MLB_EMU', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pcsx2'))
EXE = os.path.join(EMU, 'pcsx2-mlb.exe')   # 다른 세션의 pcsx2-qt 와 구분
u32 = ctypes.windll.user32; g32 = ctypes.windll.gdi32
VK = {'L': 0x4C, 'K': 0x4B, 'I': 0x49, 'J': 0x4A, 'Q': 0x51, 'E': 0x45, '1': 0x31, '3': 0x33,
      'Return': 0x0D, 'Backspace': 0x08, 'Up': 0x26, 'Down': 0x28, 'Left': 0x25, 'Right': 0x27,
      'Tab': 0x09, 'F1': 0x70, 'F3': 0x73, 'F12': 0x7B, 'Escape': 0x1B, 'Space': 0x20}
ALIAS = {'o': 'L', 'x': 'K', 'tri': 'I', 'sq': 'J', 'start': 'Return', 'sel': 'Backspace',
         'up': 'Up', 'down': 'Down', 'left': 'Left', 'right': 'Right', 'l1': 'Q', 'r1': 'E'}

def start(iso, extra=()):
    stop()
    return subprocess.Popen([EXE, '-fastboot', *extra, '--', iso], cwd=EMU)

def stop():
    subprocess.run(['taskkill', '/f', '/im', 'pcsx2-mlb.exe'], capture_output=True)
    time.sleep(1)

def _mypids():
    r = subprocess.run(['tasklist', '/fi', 'imagename eq pcsx2-mlb.exe', '/fo', 'csv', '/nh'], capture_output=True, text=True)
    return {int(l.split('","')[1]) for l in r.stdout.splitlines() if l.startswith('"')}

def _windows():
    res = []
    @ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    def cb(h, l):
        n = u32.GetWindowTextLengthW(h)
        b = ctypes.create_unicode_buffer(n + 1); u32.GetWindowTextW(h, b, n + 1)
        pid = W.DWORD(); u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        res.append((h, b.value, pid.value, u32.IsWindowVisible(h)))
        return True
    u32.EnumWindows(cb, 0)
    return res

def game_hwnd():
    """게임 화면 창(제목에 FPS/게임명이 붙는 PCSX2 메인창)."""
    mine = _mypids()
    best = None
    for h, t, pid, vis in _windows():
        if vis and pid in mine and t:
            r = W.RECT(); u32.GetClientRect(h, ctypes.byref(r))
            if best is None or r.right * r.bottom > best[1]: best = (h, r.right * r.bottom)
    return best and best[0]
    return None

def _targets(h):
    out = [h]
    @ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    def cb(c, l):
        out.append(c); return True
    u32.EnumChildWindows(h, cb, 0)
    return out

def key(k, hold=0.08, gap=0.25):
    k = ALIAS.get(k, k); vk = VK[k]
    h = game_hwnd()
    sc = u32.MapVirtualKeyW(vk, 0)
    if vk in (0x25, 0x26, 0x27, 0x28): sc |= 0x100   # 확장키
    for t in _targets(h):
        u32.PostMessageW(t, 0x100, vk, 1 | (sc << 16))
    time.sleep(hold)
    for t in _targets(h):
        u32.PostMessageW(t, 0x101, vk, 1 | (sc << 16) | (3 << 30))
    time.sleep(gap)

def keys(seq, gap=0.4):
    for k in seq.split():
        if k.startswith('w'):
            time.sleep(float(k[1:])); continue
        key(k, gap=gap)

def shot(path):
    """창 클라이언트 영역을 PNG로 저장 (PrintWindow)."""
    from PIL import Image
    h = game_hwnd()
    r = W.RECT(); u32.GetClientRect(h, ctypes.byref(r))
    w, hh = r.right, r.bottom
    hdc = u32.GetDC(h); mdc = g32.CreateCompatibleDC(hdc)
    bmp = g32.CreateCompatibleBitmap(hdc, w, hh); g32.SelectObject(mdc, bmp)
    u32.PrintWindow(h, mdc, 3)
    class BIH(ctypes.Structure):
        _fields_ = [('biSize', W.DWORD), ('biWidth', W.LONG), ('biHeight', W.LONG), ('biPlanes', W.WORD),
                    ('biBitCount', W.WORD), ('biCompression', W.DWORD), ('biSizeImage', W.DWORD),
                    ('a', W.LONG), ('b', W.LONG), ('c', W.DWORD), ('d', W.DWORD)]
    bi = BIH(); bi.biSize = ctypes.sizeof(BIH); bi.biWidth = w; bi.biHeight = -hh; bi.biPlanes = 1; bi.biBitCount = 32
    buf = ctypes.create_string_buffer(w * hh * 4)
    g32.GetDIBits(mdc, bmp, 0, hh, buf, ctypes.byref(bi), 0)
    img = Image.frombuffer('RGBA', (w, hh), buf, 'raw', 'BGRA', 0, 1).convert('RGB')
    img.save(path)
    g32.DeleteObject(bmp); g32.DeleteDC(mdc); u32.ReleaseDC(h, hdc)
    return img

def savestate(wait=4.0):
    """F1(슬롯 저장) 후 가장 새 p2s 경로."""
    t0 = time.time(); key('F1'); time.sleep(wait)
    fs = sorted(glob.glob(os.path.join(EMU, 'sstates', '*.p2s')), key=os.path.getmtime)
    return fs[-1] if fs and os.path.getmtime(fs[-1]) >= t0 - 1 else None

def member(p2s, name='eeMemory.bin'):
    import zstandard
    z = zipfile.ZipFile(p2s); i = z.getinfo(name)
    with open(p2s, 'rb') as f:
        f.seek(i.header_offset + 26); nl, el = __import__('struct').unpack('<HH', f.read(4))
        f.seek(i.header_offset + 30 + nl + el); comp = f.read(i.compress_size)
    if i.compress_type == 93:
        return zstandard.ZstdDecompressor().decompress(comp, max_output_size=i.file_size)
    return z.read(name)

def eemem(p2s):
    return member(p2s, 'eeMemory.bin')

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'start': start(sys.argv[2])
    elif cmd == 'stop': stop()
    elif cmd == 'keys': keys(' '.join(sys.argv[2:]))
    elif cmd == 'shot': shot(sys.argv[2])
    elif cmd == 'wins':
        for w in _windows():
            if w[3] and w[1]: print(w)

def write_state(src, dst, patches):
    """src p2s 의 eeMemory.bin 에 patches[(주소, bytes)] 를 적용해 dst 로 저장(무압축 멤버)."""
    z = zipfile.ZipFile(src)
    out = zipfile.ZipFile(dst + '.tmp', 'w', zipfile.ZIP_STORED)
    for info in z.infolist():
        data = member(src, info.filename)
        if info.filename == 'eeMemory.bin':
            b = bytearray(data)
            for a, p in patches: b[a:a + len(p)] = p
            data = bytes(b)
        out.writestr(info.filename, data)
    out.close()
    os.replace(dst + '.tmp', dst)

def loadstate(wait=3.0):
    key('F3'); time.sleep(wait)
