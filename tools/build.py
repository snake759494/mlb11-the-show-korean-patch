"""전체 빌드: 원본 ISO → 한글 ISO.
1) FE/GAME/HRDERBY.REL 코드 패치(제자리)  2) WAD 파일 교체분을 WAD 끝에 덧붙이고 표 갱신
3) WAD 뒤 파일들(SYSTEM.CNF, MODULES, DBDEFN, CHANTS.SKX)을 ISO 끝으로 옮겨 자리 확보  4) ISO9660·UDF 갱신"""
import os, sys, struct, shutil, json, time
sys.path.insert(0, os.path.dirname(__file__))
import iso, wad, isoedit, codepatch, kfont, inject, ktext, relinject, textfiles
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = os.path.join(ROOT, 'MLB 11 - The Show (USA).iso')
DST = os.path.join(ROOT, 'MLB 11 - The Show (USA) (Korean).iso')
SEC = 2048
H_SYM_BIN, H_SYM_TX2 = 0x9d2b0d71, 0x9d2fcba4
H_ENG_BIN, H_ENG_TX2 = 0xda3b612e, 0xda401f61
MOVE = ['SYSTEM.CNF'] + [p for p in []]    # 아래에서 채움
def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)
def main():
    T = wad.table(SRC)
    W = {h: (s, o) for h, s, o in T}
    def get(h):
        s, o = W[h]
        with open(SRC, 'rb') as f: f.seek(wad.WAD_LBA * SEC + o); return f.read(s)
    new = {}
    # --- 텍스트 ---
    tr = ktext.Translator()
    for h in sorted(W):
        s, o = W[h]
        if s < 16: continue
        d = get(h)
        if d[:8] != b'IFF0ASSH': continue
        nd, st = inject.inject(d, tr.assh(h), force_all=tr.force_all(h))
        if st['n']:
            new[h] = nd
    log('ASSH files changed', len(new), 'strings', tr.count)
    sf = tr.strfn()
    new[0xbd3c4959] = textfiles.helpbar(get(0xbd3c4959), sf)          # FE.txt 도움말 바
    new[0x64e8260a] = textfiles.tsv(get(0x64e8260a), sf, [1, 2, 3, 4, 5])   # goals.txt
    new[0xf659e994] = textfiles.tsv(get(0xf659e994), sf, [2, 3])            # eggs.txt
    new[0x7a917520] = textfiles.recstream(get(0x7a917520), sf)             # RTTS 목표 문구
    new[0xe32a33cf] = textfiles.notable(get(0xe32a33cf), sf)               # notable.bin
    import names as _nm
    nreplaced = 0
    for fh in _nm.FILES:
        h = int(fh, 16); d = bytearray(new.get(h) or get(h))
        for o, a, b in _nm.pairs(bytes(d)):
            v = tr.names.get((a, b))
            if not v: continue
            parts = ((o, v[0]), (o + 16, v[1]))
            if os.environ.get('KO_NAMEPART') == 'first': parts = parts[:1]
            if os.environ.get('KO_NAMEPART') == 'last': parts = parts[1:]
            for off, txt in parts:
                e = tr.enc(txt)
                if len(e) <= 15: d[off:off + 16] = e + bytes(16 - len(e)); nreplaced += 1
        if not os.environ.get('KO_NONAMES'): new[h] = bytes(d)
    log('player name fields', nreplaced)
    import teams as _tm
    TT = {}
    for fp in __import__('glob').glob(os.path.join(ROOT, 'translation', 'fix', 'team_db.json')): TT.update(json.load(open(fp, encoding='utf-8')))
    for fh in ('1396c408', '65023f60', 'ac08628e', '63163ce7', '8382e1b8', '3aea164e'):
        h = int(fh, 16); d2, c = _tm.apply(new.get(h) or get(h), TT, tr.enc)
        if c and not os.environ.get('KO_NOTEAM'): new[h] = d2; log('team fields', fh, c)
    # --- 글꼴 ---
    sylls = tr.syllables()
    log('syllables', len(sylls))
    F = kfont.build(get(H_ENG_BIN), get(H_ENG_TX2), get(H_SYM_BIN), get(H_SYM_TX2), sylls)
    fonts = {H_ENG_BIN: F['eng_bin'], H_ENG_TX2: F['eng_tx2'], H_SYM_BIN: F['sym_bin'], H_SYM_TX2: F['sym_tx2']}
    if os.environ.get('KO_NOTEXT'): new = {}
    if not os.environ.get('KO_NOFONT'): new.update(fonts)
    # --- ISO 복사 ---
    log('copy iso')
    shutil.copyfile(SRC, DST)
    ents = {p: (l, s) for p, l, s, r in iso.walk(SRC)}
    wad_l, wad_s = ents['MLBPS2.WAD']
    with open(DST, 'r+b') as f:
        # REL 코드 패치
        inv_all = json.load(open(os.path.join(ROOT, 'work', 'inv_all.json'), encoding='utf-8'))
        relkeys = {k for k, e in inv_all.items() if any(x.startswith('rel:') for x in e['src'])}
        if not os.environ.get('KO_NOREL2'): relkeys |= set(json.load(open(os.path.join(ROOT, 'work', 'inv_rel2.json'), encoding='utf-8')))
        import glob as _g
        for fp in ([] if os.environ.get('KO_NOREL2') else _g.glob(os.path.join(ROOT, 'translation', 'fix', 'rel_*.json'))):
            relkeys |= set(json.load(open(fp, encoding='utf-8')))
        em_all = tr.enc_map()
        _td = json.load(open(os.path.join(ROOT, 'translation', 'fix', 'team_db.json'), encoding='utf-8'))
        for _k in [k for k in _td if ' ' not in k and '^' not in k] + ['Grass', 'Bat', 'Hat', 'Vortex', 'bat', 'cap', 'Cap']:
            em_all.pop(_k, None)
        for m in ([] if os.environ.get('KO_NOCODE') else ['FE', 'GAME', 'HRDERBY', 'INITDLL']):
            l, s = ents[m + '.REL']
            f.seek(l * SEC); d = f.read(s)
            p = codepatch.patch(d, m) if m != 'INITDLL' else d
            if not os.environ.get('KO_NOREL'):
                em = {k: v for k, v in em_all.items() if k in relkeys and (m == 'FE' or ' ' in k.strip() or '%' in k)}
                TITLES = {'Warning', 'WARNING', 'Confirm', 'CONFIRM', 'Notice', 'NOTICE', 'Error', 'ERROR', 'OK', 'YES', 'NO', 'CANCEL', 'Substitution'}
                SAFE = set(json.load(open(os.path.join(ROOT, 'translation', 'rel_safe_words.json'), encoding='utf-8')))
                def allow(a, t, m=m):
                    if t in SAFE and m == 'FE': return True
                    if ' ' in t.strip() or '%' in t: return True          # 문장형·printf
                    if t in TITLES: return True                           # 팝업 제목
                    return m == 'FE' and 0x2f3000 <= a < 0x2f6200          # FE 옵션 표(이름·값)
                p, st = relinject.inject(p, em, allow=allow)
                log(m, 'REL strings', {k: v for k, v in st.items() if k != 'kept_list'})
                json.dump(st['kept_list'], open(os.path.join(ROOT, 'work', f'rel_kept_{m}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
            assert len(p) == len(d)
            f.seek(l * SEC); f.write(p)
        # WAD 뒤 파일 → ISO 끝
        movers = sorted([(l, p, s) for p, (l, s) in ents.items() if wad_l < l < ents['SNDPS2/SOUND/CHANTS.SKX'][0] + 1], key=lambda x: x[0])
        limit = ents['SNDPS2/SOUND/CROWD.SKX'][0]
        end = os.path.getsize(SRC) // SEC
        for l, p, s in movers:
            f.seek(l * SEC); data = open(SRC, 'rb')  # 원본에서 읽기
            with open(SRC, 'rb') as g:
                g.seek(l * SEC); left = s; f.seek(end * SEC)
                while left > 0:
                    b = g.read(min(left, 1 << 24)); f.write(b); left -= len(b)
            f.write(bytes((-s) % SEC))
            isoedit.relocate(f, DST, p, end, s)
            end += (s + SEC - 1) // SEC
        # WAD 덧붙이기
        pos = (wad_s + SEC - 1) // SEC * SEC
        tab = [list(e) for e in T]
        for e in tab:
            if e[0] in new:
                d = new[e[0]]
                f.seek(wad_l * SEC + pos); f.write(d)
                e[1], e[2] = len(d), pos
                pos += (len(d) + 15) // 16 * 16
        # 선수 얼굴 별칭: 한글 이름으로 만든 경로 DATA\HEADS\성_이름\PACKFILE.PS2 → 영문 이름의 얼굴 데이터
        from whash import h131
        BS = bytes([92])
        byh = {e[0]: e for e in tab}
        def up(b): return bytes(c - 32 if 0x61 <= c <= 0x7a else c for c in b)
        def orig(b): return bytes(c for c in b if c not in b" '.,`-")   # cPlayerProfile::GetOrigFirst/LastName 과 같은 규칙
        aliases = {}
        for (fn, ln), (kf, kl) in tr.names.items():
            eh = h131(up(b'DATA' + BS + b'HEADS' + BS + orig(ln.encode('latin1')) + b'_' + orig(fn.encode('latin1')) + BS + b'PACKFILE.PS2'))
            if eh not in byh: continue
            kh = h131(up(b'DATA' + BS + b'HEADS' + BS + orig(tr.enc(kl)) + b'_' + orig(tr.enc(kf)) + BS + b'PACKFILE.PS2'))
            if kh in byh or kh in aliases: continue
            aliases[kh] = eh
        n_all = len(tab) + len(aliases)
        tab_end = 8 + 12 * n_all
        # 늘어난 목록과 겹치는 앞쪽 파일은 끝으로 옮김
        with open(SRC, 'rb') as g:
            for e in tab:
                if e[2] < tab_end:
                    g.seek(wad_l * SEC + e[2]); d = g.read(e[1]) if e[0] not in new else new[e[0]]
                    f.seek(wad_l * SEC + pos); f.write(d)
                    e[2] = pos; pos += (len(d) + 15) // 16 * 16
        byh = {e[0]: e for e in tab}
        for kh, eh in aliases.items(): tab.append([kh, byh[eh][1], byh[eh][2]])
        tab.sort(key=lambda e: e[0])
        log('face aliases', len(aliases), 'table end', hex(tab_end))
        new_wad = pos
        assert wad_l + (new_wad + SEC - 1) // SEC <= limit, 'WAD too big'
        f.seek(wad_l * SEC + pos); f.write(bytes((-pos) % SEC))
        f.seek(wad_l * SEC); f.write(struct.pack('<I', len(tab)))
        f.seek(wad_l * SEC + 8)
        f.write(b''.join(struct.pack('<3I', *e) for e in tab))
        isoedit.relocate(f, DST, 'MLBPS2.WAD', wad_l, new_wad)
        # 볼륨 크기 + UDF 앵커
        f.seek(0, 2); f.write(bytes((-f.tell()) % SEC))
        with open(SRC, 'rb') as g:
            g.seek(os.path.getsize(SRC) - SEC); avdp = bytearray(g.read(SEC))
        nsec = end + 1
        struct.pack_into('<I', avdp, 12, nsec - 1)
        isoedit._fix_tag(avdp, 0, struct.unpack_from('<H', avdp, 10)[0])
        f.seek((nsec - 1) * SEC); f.write(avdp)
        isoedit.set_volume_size(f, nsec)
    log('done', DST, os.path.getsize(DST) // SEC, 'sectors; WAD', hex(new_wad))
    json.dump({'syllables': len(sylls)}, open(os.path.join(ROOT, 'work', 'build_report.json'), 'w'))
if __name__ == '__main__': main()
