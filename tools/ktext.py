"""번역 데이터 → 게임 바이트.
번역 원본: work/batches/<묶음>.json (id, en) + translation/ko/<묶음>.json (id → 한국어)
수동 보정: translation/fix/*.json  {"원문": "번역"} (우선 적용)
한글 음절은 kfont.encode_map 의 2바이트 코드로, 나머지는 ASCII 로."""
import json, os, glob, sys, re
sys.path.insert(0, os.path.dirname(__file__)); import kfont
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TR = os.path.join(ROOT, 'translation')
SUBST = {'·': '.', '…': '...', '“': '"', '”': '"', '‘': "'", '’': "'", '–': '-', '—': '-', '~': '-', '　': ' '}
RTTS = 0x97c92be3
def is_syl(ch): return 0xAC00 <= ord(ch) <= 0xD7A3
def load_map():
    m = {}
    for bp in sorted(glob.glob(os.path.join(ROOT, 'work', 'batches', '*.json'))):
        name = os.path.splitext(os.path.basename(bp))[0]
        kp = os.path.join(TR, 'ko', name + '.json')
        if not os.path.exists(kp): continue
        K = json.load(open(kp, encoding='utf-8'))
        for it in json.load(open(bp, encoding='utf-8')):
            v = K.get(str(it['id']))
            if v and v != it['en']: m[it['en']] = v
    for fp in sorted(glob.glob(os.path.join(TR, 'fix', '*.json'))):
        for k, v in json.load(open(fp, encoding='utf-8')).items():
            if v is None: m.pop(k, None)
            else: m[k] = v
    return m
def load_names():
    nm = {}
    for bp in sorted(glob.glob(os.path.join(ROOT, 'work', 'batches_names_*.json'))):
        k = bp[-7:-5]
        tp = os.path.join(TR, 'names', f'names_{k}.json')
        if not os.path.exists(tp): continue
        T = json.load(open(tp, encoding='utf-8'))
        for it in json.load(open(bp, encoding='utf-8')):
            v = T.get(str(it['id']))
            if v: nm[(it['first'], it['last'])] = tuple(v)
    return nm
class Translator:
    def __init__(self):
        self.map = load_map()
        self.names = load_names()
        if os.environ.get('KO_NAMETEST'):
            self.names = {(f, l): (f[::-1].lower().capitalize(), l[::-1].lower().capitalize()) for (f, l) in self.names}
        inv = json.load(open(os.path.join(ROOT, 'work', 'inv_all.json'), encoding='utf-8'))
        for (f, l), (kf, kl) in self.names.items():
            full = f'{f} {l}'
            for k in (full, '^j1^' + full, '^j0^' + full, '^j2^' + full):
                if k in inv and k not in self.map: self.map[k] = k.replace(full, f'{kf} {kl}')
        used = {}
        for v in list(self.map.values()) + [x for p in self.names.values() for x in p]:
            for ch in v:
                if is_syl(ch): used[ch] = used.get(ch, 0) + 1
        # 유니코드 순 음절(키보드 조합용) + 끝에 호환 자모 51자
        import hangul
        assert len(used) <= kfont.CAP - 51, f'too many syllables {len(used)}'
        self.syl_sorted = hangul.build_set(used, kfont.CAP - 51)
        self.sylls = self.syl_sorted + hangul.COMPAT
        self.code = kfont.encode_map(self.sylls)
        self.count = 0
    def syllables(self): return self.sylls
    def enc(self, s):
        out = bytearray()
        for ch in s:
            ch = SUBST.get(ch, ch)
            if len(ch) > 1: out += ch.encode('ascii'); continue
            if is_syl(ch) or ch in self.code: out += self.code[ch]
            elif ord(ch) < 0x7f: out.append(ord(ch))
            else: raise ValueError(f'unencodable {ch!r} in {s!r}')
        return bytes(out)
    def get(self, k):
        v = self.map.get(k)
        return None if v is None else self.enc(v)
    def assh(self, h):
        def tr(b):
            v = self.get(b.decode('latin1'))
            if v is None: return None
            if h == RTTS and b' ' not in b and b'^' not in b: return None
            self.count += 1
            return v
        return tr
    def force_all(self, h): return h == RTTS
    def strfn(self):
        """latin1 str → latin1 str (텍스트 파일용)"""
        def tr(s):
            v = self.get(s)
            return s if v is None else v.decode('latin1')
        return tr
    def enc_map(self):
        return {k: self.enc(v) for k, v in self.map.items()}
