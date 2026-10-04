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
    ASSH_LEFT = set()      # 화면 파일에서 표시용 참조가 아니라 데이터로 번역되지 않은 문자열
    for h in sorted(W):
        s, o = W[h]
        if s < 16: continue
        d = get(h)
        if d[:8] != b'IFF0ASSH': continue
        ctr = None
        if h == 0x3690fe30:      # 키보드 화면 청크: 글자 키에 자모 병기, CAPS LOCK → 한/영
            KL = json.load(open(os.path.join(ROOT, 'translation', 'keyboard_labels.json'), encoding='utf-8'))
            ctr = {0x1fe130: lambda b, KL=KL: tr.enc(KL[b.decode('latin1')]) if b.decode('latin1') in KL else None}
        cpost = None
        if h == 0x3690fe30:
            def _shrink(orig, nc, KL=KL):
                import assh as _a
                nc = bytearray(nc)
                for o, s_, refs in _a.strings(orig, 0, len(orig)):
                    t = s_.decode('latin1')
                    if t in KL and 'CAPS' not in t:
                        for k in refs:
                            if nc[k + 17] == 0xff and nc[k + 18] == 3:          # 요소의 글자 크기 바이트 = 참조 +16
                                nc[k + 16] = int(os.environ.get('KO_KEYSIZE', 10))
                return bytes(nc)
            cpost = {0x1fe130: _shrink}
        nd, st = inject.inject(d, tr.assh(h), force_all=tr.force_all(h), chunk_tr=ctr, chunk_post=cpost)
        ASSH_LEFT.update(x.decode('latin1') for x in st.get('left', ()))
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
        import glob as _gg, assh as _as
        ASSH_STR = set()
        # 정규화용 핵심 번역: 표식을 뗀 영어 → 한글(표식 뗀 것), 대소문자 무시판
        import re as _re0
        CORE = {}
        for _k, _v in tr.map.items():
            _ck = _re0.sub(r'^(\^[a-z]\d*\^)+|(\^[a-z]\d*\^)+$', '', _k)
            _cv = _re0.sub(r'^(\^[a-z]\d*\^)+|(\^[a-z]\d*\^)+$', '', _v)
            if _ck and '^' not in _ck and '^' not in _cv and '%' not in _ck: CORE.setdefault(_ck, tr.enc(_cv))
        CORE_L = {}
        for _k, _v in CORE.items(): CORE_L.setdefault(_k.lower(), _v)
        for _fn in _gg.glob(os.path.join(ROOT, 'extract', 'wad', '*.bin')):
            _d = open(_fn, 'rb').read()
            if _d[:8] != b'IFF0ASSH': continue
            for (_i, _h, _sz) in _as.chunks(_d):
                if 0 < _sz < 0x80000000:
                    for _o, _s, _r in _as.strings(_d, _i + 16, _sz): ASSH_STR.add(_s.decode('latin1'))
        ASSH_ALL = ASSH_STR
        _td = json.load(open(os.path.join(ROOT, 'translation', 'fix', 'team_db.json'), encoding='utf-8'))
        for _k in [k for k in _td if ' ' not in k and '^' not in k] + ['Grass', 'Bat', 'Hat', 'Vortex', 'bat', 'cap', 'Cap']:
            em_all.pop(_k, None)
        PAUSE_MENU = (0x3ad9d8, 0x3ada78)          # GAME 일시정지 메뉴 항목 문자열 묶음 (메뉴 표 0x36ff88~ 에서만 참조)
        PAUSE_WORDS = {'REPLAY', 'OPTIONS', 'CONTROLS'}
        for m in ([] if os.environ.get('KO_NOCODE') else ['FE', 'GAME', 'HRDERBY', 'INITDLL']):
            l, s = ents[m + '.REL']
            f.seek(l * SEC); d = f.read(s)
            p = codepatch.patch(d, m) if m != 'INITDLL' else d
            if not os.environ.get('KO_NOREL'):
                em = {k: v for k, v in em_all.items() if (k in relkeys or k in PAUSE_WORDS) and (m == 'FE' or ' ' in k.strip() or '%' in k or k in PAUSE_WORDS)}
                TITLES = {'Warning', 'WARNING', 'Confirm', 'CONFIRM', 'Notice', 'NOTICE', 'Error', 'ERROR', 'OK', 'YES', 'NO', 'CANCEL', 'Substitution'}
                SAFE = set(json.load(open(os.path.join(ROOT, 'translation', 'rel_safe_words.json'), encoding='utf-8')))
                def allow(a, t, m=m):
                    if t in SAFE and m == 'FE': return True
                    if ' ' in t.strip() or '%' in t: return True          # 문장형·printf
                    if t in TITLES: return True                           # 팝업 제목
                    if m == 'GAME' and PAUSE_MENU[0] <= a < PAUSE_MENU[1]: return True   # 일시정지 첫 메뉴 표(팀 관리 등과 같은 표)
                    return m == 'FE' and 0x2f3000 <= a < 0x2f6200          # FE 옵션 표(이름·값)
                import kbd, disphook, dispcand
                KBD = 6144 if m == 'FE' else 0
                # 표시 번역 표: 이 모듈에 들어 있는 문자열 + 화면 파일 문자열 중 번역이 있는 것 (데이터로 번역된 것은 아래에서 제외)
                modstr = dispcand.all_strings_rel(os.path.join(ROOT, 'extract', m + '.REL'))
                # 콘솔 전용 디버그 문구는 빈 문자열로 옮겨 연속 공간 확보 (화면에 나오지 않음)
                import re as _re, relstr as _rs
                DBG = _re.compile(r'(\n$|::|SKAT|Unable to|Early EOF|lgVid|XFade|Wrong |Bad |Number of |not set|mismatch|timeout while|liblgvid|bullpen locator|IPU \(|JPEG420|KHz\)|fps\)|overflow|not initialized)')
                # printf 형 콘솔 출력(줄바꿈으로 끝나거나 '클래스::' 포함). 파일 경로·확장자처럼 보이면 제외
                DBGF = _re.compile(r'%.*(\n$|::)|::.*%')
                FILEISH = _re.compile(r'[/\\]|\.[a-z]{2,3}\b')
                for _a, _t, _r in _rs.strings(os.path.join(ROOT, 'extract', m + '.REL'))[4]:
                    if len(_t) >= 16 and (DBG.search(_t) and '%' not in _t or DBGF.search(_t) and not FILEISH.search(_t)): em[_t] = b' '
                disp_all = {k: v for k, v in em_all.items() if len(k) <= 80 and (k in modstr or k in ASSH_LEFT)}
                # 표식·대소문자 정규화: '^j1^REPLAY', '^c4^REPLAY', 'UP/DOWN' 처럼 핵심이 번역된 문자열도 같은 번역으로
                FUNCW = {'to', 'or', 'and', 'in', 'of', 'at', 'on', 'by', 'vs', 'a', 'an', 'the', 'for', 'with', 'from', 'is'}
                for S in (modstr | ASSH_ALL):
                    if S in em_all or len(S) > 48: continue
                    mm = _re.match(r'^((?:\^[a-z]\d*\^)*)(.*?)((?:\^[a-z]\d*\^)*)$', S, _re.S)
                    pre, core, suf = mm.group(1), mm.group(2), mm.group(3)
                    if not core.strip() or sum(ch.isalpha() for ch in core) < 2: continue
                    # 서수(1ST=1루/1회 …)는 문맥마다 뜻이 달라 표식 붙은 원문의 번역을 다른 곳에 번지지 않게 한다
                    if _re.fullmatch(r'\d+(st|nd|rd|th)', core.strip(), _re.I): continue
                    ko = CORE.get(core)
                    # 대소문자 무시 매칭(글꼴이 대문자로 그림): 문맥 없는 기능어 조각(to, or, and …)은 제외
                    if ko is None and core.strip().lower() not in FUNCW: ko = CORE_L.get(core.lower())
                    if ko is not None: disp_all[S] = tr.enc(pre) + ko + tr.enc(suf)
                # 팀 DB(도시·별칭)는 내부 키라 데이터는 원문 유지 → 화면 표시 단계에서만 교체 (원문/대문자 표기 모두)
                TEAMK = set()
                for _k, _v in _td.items():
                    _k2 = _k.strip()
                    if _v and sum(ch.isalpha() for ch in _k2) >= 2:
                        for _kk in (_k2, _k2.upper()):
                            if len(_kk) <= 40: disp_all.setdefault(_kk, tr.enc(_v.strip())); TEAMK.add(_kk.encode('latin1'))
                # 팝업 버튼·제목: 실행 중 '^j1^'+단어 로 조합되어 그려짐(예: ^j1^CANCEL) → 정렬 표식 변형을 미리 넣음
                POPW = TITLES | {'Cancel', 'Ok', 'Yes', 'No', 'BACK', 'EXIT', 'DONE', 'ACCEPT', 'DECLINE', 'CONTINUE', 'SAVE', 'LOAD',
                                 'DELETE', 'ENTER', 'SELECT', 'HELP', 'ADVANCE', 'RETRY', 'QUIT', 'RESUME'}
                PRIO = set()
                # 스크린샷에서 영어로 보고된 화면 문구(번역 있는 것) — 원문·대문자·정렬 표식 변형 모두 우선 배치
                _snap = os.path.join(ROOT, 'work', 'snap', 'english.txt')
                SNAPW = set()
                if os.path.exists(_snap):
                    SNAPW = {x.strip() for x in open(_snap, encoding='utf-8').read().split('=== DISTINCT ===')[-1].splitlines() if x.strip()}
                for _w in SNAPW:
                    _ko = CORE.get(_w) or CORE_L.get(_w.lower())
                    if _ko is None or _re.fullmatch(r'\d+(st|nd|rd|th)', _w, _re.I) or _w.lower() in FUNCW: continue
                    for _pre in (('', '^j0^', '^j1^', '^j2^') if m == 'FE' else ('',)):
                        for _ww in {_w, _w.upper()}:
                            disp_all.setdefault(_pre + _ww, tr.enc(_pre) + _ko); PRIO.add((_pre + _ww).encode('latin1'))
                # 수동 지정 표시 번역(disp_manual.json)도 우선
                for _k in json.load(open(os.path.join(ROOT, 'translation', 'fix', 'disp_manual.json'), encoding='utf-8')):
                    if _k in disp_all: PRIO.add(_k.encode('latin1'))
                for _w in POPW:
                    _ko = CORE.get(_w) or CORE_L.get(_w.lower())
                    if _ko is None: continue
                    for _pre in (('^j0^', '^j1^', '^j2^') if m == 'FE' else ('^j1^',)):
                        for _ww in ({_w, _w.upper()} if m == 'FE' else {_w.upper()}):
                            disp_all.setdefault(_pre + _ww, tr.enc(_pre) + _ko); PRIO.add((_pre + _ww).encode('latin1'))
                _, st0 = relinject.inject(p, em, allow=allow, reserve=0)          # 데이터로 번역될 것 확정
                disp_all = {k: v for k, v in disp_all.items() if k not in st0['done']}
                disp = {k.encode('latin1'): v for k, v in disp_all.items()}
                RES = KBD + disphook.code_size()
                p, st = relinject.inject(p, em, allow=allow, reserve=RES)
                if not os.environ.get('KO_NOHOOK'):
                    if m in disphook.PARSE:
                        p = bytearray(p); FREE = st['free']
                        def place(b, p=p, FREE=FREE):
                            al = 4 if (len(b) % 8 == 0 and not any(b)) else 1      # 버킷 표 자리(0으로 채운 8바이트 단위)는 4바이트 정렬
                            for f in FREE:
                                s0 = (f[0] + al - 1) & ~(al - 1)
                                if f[1] - s0 >= len(b):
                                    p[s0:s0 + len(b)] = b; f[0] = s0 + len(b); return s0
                            return None
                        cap = sum(f[1] - f[0] for f in FREE) * 0.85 - 16 * 8
                        sel = {}; used = 0; kos = set()
                        MODB = {x.encode('latin1') for x in modstr}
                        for k in sorted(disp, key=lambda k: (0 if k in PRIO else 1 if (k in MODB or k in TEAMK) else 2, len(k), k)):          # 이 모듈 문자열 → 짧은 UI 문구 우선
                            c = (0 if disp[k] in kos else len(disp[k]) + 1) + 8
                            if used + c > cap: continue
                            sel[k] = disp[k]; used += c; kos.add(disp[k])
                        json.dump({k.decode('latin1'): tr.dec(v) if hasattr(tr, 'dec') else v.hex() for k, v in sel.items()},
                                  open(os.path.join(ROOT, 'work', f'disp_sel_{m}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
                        def write(a, x, p=p): p[a:a + len(x)] = x
                        hb, entry, nent = disphook.build(st['reserved'] + KBD, disphook.PARSE[m], sel, place, write)
                        assert KBD + len(hb) <= RES, (len(hb), RES)
                        p[st['reserved'] + KBD:st['reserved'] + KBD + len(hb)] = hb
                        b2 = place(bytes(disphook.query_size()))           # 동적 토큰 값 훅(첫 블롭 표 공유)
                        assert b2 is not None and b2 % 4 == 0
                        q = disphook.build_query(b2, st['reserved'] + KBD, disphook.QUERY_FN + disphook.DELTA[m])
                        p[b2:b2 + len(q)] = q
                        p = disphook.patch_calls(bytes(p), disphook.PARSE[m], entry)
                        p = disphook.patch_query_call(p, m, b2)
                        log(m, 'display hook entries', nent, 'of', len(disp), '(skipped for space', len(disp) - nent, ')')
                if m == 'FE' and not os.environ.get('KO_NOKBD'):
                    blob, ins_a, del_a = kbd.build(st['reserved'], tr.syl_sorted)
                    assert len(blob) <= RES
                    p = bytearray(p); p[st['reserved']:st['reserved'] + len(blob)] = blob
                    p = kbd.patch_relocs(bytes(p), ins_a, del_a)
                    log('keyboard blob', hex(st['reserved']), len(blob))
                log(m, 'REL strings', {k: v for k, v in st.items() if k not in ('kept_list', 'done', 'extra')})
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
