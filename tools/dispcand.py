"""표시 시점 번역(Parse 훅) 후보 전수 집계.
각 모듈의 REL 문자열 + 모든 화면(ASSH) 문자열 중, 빌드에서 데이터로 번역되지 않는 것."""
import sys, os, json, re, glob
sys.path.insert(0, os.path.dirname(__file__))
import relstr, assh, inject, ktext
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MARK = re.compile(r'\^[a-z]\d*\^')
def plain(s): return MARK.sub('', s).strip()
def person_names(tr):
    S = set()
    for (f, l) in tr.names: S |= {f, l, f'{f} {l}'}
    for fp in ('rel_staff.json',):
        S |= set(json.load(open(os.path.join(ROOT, 'translation', 'fix', fp), encoding='utf-8')))
    return S
ABBR = re.compile(r'^[A-Z0-9/%.&+\-# ]{1,5}$')      # 짧은 대문자 약어·숫자는 영어 유지
def wanted(s):
    p = plain(s)
    if sum(c.isalpha() for c in p) < 2: return False
    if ABBR.match(p) and not (len(p) >= 3 and re.search(r'[AEIOUY]', p) and re.fullmatch(r'[A-Z]+', p)): return False
    if any(ord(c) > 126 or (ord(c) < 32 and c not in '\n') for c in s): return False
    if '%' in s or chr(92) in s or '_' in p or len(s) > 120: return False
    if re.search(r'[a-z][A-Z]', p) and ' ' not in p: return False     # CamelCase 내부 키
    return True
def collect():
    tr = ktext.Translator(); PN = person_names(tr)
    out = {}
    for m in ('FE', 'GAME', 'HRDERBY', 'INITDLL'):
        for a, s, r in relstr.strings(os.path.join(ROOT, 'extract', m + '.REL'))[4]:
            if wanted(s) and s not in PN: out.setdefault(s, set()).add('rel:' + m)
    for fn in glob.glob(os.path.join(ROOT, 'extract', 'wad', '*.bin')):
        d = open(fn, 'rb').read()
        if d[:8] != b'IFF0ASSH': continue
        for (i, h, sz) in assh.chunks(d):
            if sz >= 0x80000000 or sz == 0: continue
            c = d[i + 16:i + 16 + sz]
            for o, s, refs in assh.strings(d, i + 16, sz):
                t = s.decode('latin1')
                if wanted(t) and t not in PN: out.setdefault(t, set()).add('assh')
    return tr, out
if __name__ == '__main__':
    tr, out = collect()
    have = {k: v for k, v in out.items() if k in tr.map}
    need = {k: v for k, v in out.items() if k not in tr.map}
    print('candidates', len(out), 'with translation', len(have), 'without', len(need))
    json.dump({k: sorted(v) for k, v in need.items()}, open(os.path.join(ROOT, 'work', 'disp_need.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    import collections
    print(collections.Counter(tuple(sorted(v)) for v in need.values()).most_common(12))

def remaining(isop=None):
    """빌드된 ISO 기준으로 아직 영어인 후보 문자열 → {문자열: 출처 집합}"""
    import iso, wad, tempfile
    isop = isop or os.path.join(ROOT, 'MLB 11 - The Show (USA) (Korean).iso')
    tr = ktext.Translator(); PN = person_names(tr)
    ents = {p: (l, s) for p, l, s, r in iso.walk(isop)}
    out = {}
    for m in ('FE', 'GAME', 'HRDERBY', 'INITDLL'):
        l, s = ents[m + '.REL']; tmp = os.path.join(ROOT, 'work', f'_built_{m}.REL')
        open(tmp, 'wb').write(iso.read(l, s, isop))
        for a, t, r in relstr.strings(tmp)[4]:
            if wanted(t) and t not in PN: out.setdefault(t, set()).add('rel:' + m)
    for h, sz, o in wad.table(isop):
        if sz < 16: continue
        hd = iso.read(wad.WAD_LBA + o // 2048, 16, isop) if o % 2048 == 0 else None
        d = None
        with open(isop, 'rb') as f:
            f.seek(wad.WAD_LBA * 2048 + o); head = f.read(8)
            if head != b'IFF0ASSH': continue
            f.seek(wad.WAD_LBA * 2048 + o); d = f.read(sz)
        for (i, hh, csz) in assh.chunks(d):
            if csz >= 0x80000000 or csz == 0: continue
            for oo, s2, refs in assh.strings(d, i + 16, csz):
                t = s2.decode('latin1')
                if wanted(t) and t not in PN: out.setdefault(t, set()).add('assh')
    return tr, out

def all_strings_rel(path):
    """REL 데이터 영역(코드 뒤 ~ 재배치표 앞)의 모든 NUL 종료 문자열."""
    import struct
    d = open(path, 'rb').read(); h = struct.unpack_from('<12I', d, 0)
    out = set()
    for m in re.finditer(rb'(?<=\x00)[\x20-\x7e]{2,120}(?=\x00)', d[:h[1]]):
        out.add(m.group().decode('latin1'))
    # 숫자 표(float 등) 바로 뒤에 0 없이 붙은 문자열: 4바이트 정렬 + 앞 바이트가 글자가 아닐 때만 (예: 일시정지 도움말)
    for m in re.finditer(rb'(?<=[^\x00\x20-\x7e])[\x20-\x7e]{2,120}(?=\x00)', d[:h[1]]):
        if m.start() % 4 == 0: out.add(m.group().decode('latin1'))
    return out
def remaining_full(isop=None):
    """빌드된 ISO 기준: 모듈별 남은 영어 (재배치 대상 + 고정 칸 문자열 + 화면 파일)."""
    import iso, wad
    isop = isop or os.path.join(ROOT, 'MLB 11 - The Show (USA) (Korean).iso')
    tr = ktext.Translator(); PN = person_names(tr)
    ents = {p: (l, s) for p, l, s, r in iso.walk(isop)}
    per = {}
    for m in ('FE', 'GAME', 'HRDERBY'):
        l, s = ents[m + '.REL']; tmp = os.path.join(ROOT, 'work', f'_built_{m}.REL')
        open(tmp, 'wb').write(iso.read(l, s, isop))
        per[m] = {t for t in all_strings_rel(tmp) if wanted(t) and t not in PN}
    ash = set()
    with open(isop, 'rb') as f:
        for h, sz, o in wad.table(isop):
            if sz < 16: continue
            f.seek(wad.WAD_LBA * 2048 + o)
            if f.read(8) != b'IFF0ASSH': continue
            f.seek(wad.WAD_LBA * 2048 + o); d = f.read(sz)
            for (i, hh, csz) in assh.chunks(d):
                if csz >= 0x80000000 or csz == 0: continue
                for oo, s2, refs in assh.strings(d, i + 16, csz):
                    t = s2.decode('latin1')
                    if wanted(t) and t not in PN: ash.add(t)
    return tr, per, ash
