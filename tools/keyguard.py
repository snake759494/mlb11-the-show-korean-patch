"""REL 한 단어 문자열 안전 판별 (번역 금지 규칙).
위험(UNSAFE) 근거:
 A. 코드 참조(HI16/LO16) 뒤 24명령 안에서 문자열 비교·파일·사운드·해시 함수를 호출
 B. 데이터 표 참조(R32)만 있고 FE 옵션 표 영역이 아님 (표의 용도를 코드로 확인할 수 없음)
 C. 같은 단어가 비텍스트 WAD 데이터(모델·텍스처·스크립트·사운드 이름표)에 이름으로 등장
안전으로 인정: A·B·C 모두 해당 없음, 또는 FE 옵션 표 영역(0x2f3000~0x2f6200), 또는 팝업 제목."""
import os, sys, re, glob, struct, collections
sys.path.insert(0, os.path.dirname(__file__)); import rel
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BAD_CALL = re.compile(r'cmp|casecmp|Open|LoadFile|Exist|GetWadPos|snd_|Hash|Crc|Find|Locate|IsName|SetSwapTexture|SetPath|Texture', re.I)
_wordcache = None
def data_words():
    """비텍스트 WAD 파일에 등장하는 영숫자 토큰(소문자) 집합."""
    global _wordcache
    if _wordcache is not None: return _wordcache
    W = collections.Counter()
    for fn in glob.glob(os.path.join(ROOT, 'extract', 'wad', '*.bin')):
        d = open(fn, 'rb').read()
        if d[:8] == b'IFF0ASSH': continue                      # 화면 파일은 표시용
        if d[:4] == b'TGDF' or b'TGDF' in d[:16]: continue      # 선수 DB(이름)는 별도 처리
        pr = sum(1 for b in d[:4000] if 32 <= b < 127 or b in (9, 10, 13)) / max(1, min(len(d), 4000))
        if pr > 0.9 and not d.startswith(b'ScriptWorld'): continue   # 순수 텍스트 파일
        for m in re.finditer(rb'[A-Za-z][A-Za-z0-9_]{2,}', d): W[m.group().decode().lower()] += 1
    _wordcache = W; return W
class Module:
    def __init__(self, name):
        self.name = name
        self.d, self.h, self.S = rel.load(os.path.join(ROOT, 'extract', name + '.REL'))
        self.R = rel.relocs(self.d, self.h, self.S)
        self.calls = {o: (sym if sym else hex(a)) for o, (t, sym, a) in self.R.items() if t == 4}
        self.by = collections.defaultdict(list)
        for o, (t, sym, a) in self.R.items():
            if sym is None and t in (2, 5, 6): self.by[a].append((o, t))
    def callees_after(self, o, n=24):
        out = []
        for k in range(1, n + 1):
            c = self.calls.get(o + 4 * k)
            if c: out.append(c)
        return out
    def judge(self, a, s):
        refs = self.by.get(a, [])
        why = []
        if self.name == 'FE' and 0x2f3000 <= a < 0x2f6200: return 'SAFE', ['option-table']
        code = [o for o, t in refs if t in (5, 6)]
        table = [o for o, t in refs if t == 2]
        for o in code:
            for c in self.callees_after(o):
                if BAD_CALL.search(c): why.append(f'A:{c}')
        if table and not code: why.append('B:table-only')
        w = re.sub(r'\^[a-z]\d*\^', '', s).strip().lower()
        if w and data_words().get(w, 0) > 0: why.append(f'C:data-name({data_words()[w]})')
        return ('UNSAFE' if why else 'SAFE'), why
if __name__ == '__main__':
    M = {m: Module(m) for m in ('FE', 'GAME', 'HRDERBY', 'INITDLL')}
    import relstr
    words = sys.argv[1:]
    for m, mod in M.items():
        for a, s, r in relstr.strings(os.path.join(ROOT, 'extract', m + '.REL'))[4]:
            if s in words: print(m, hex(a), s, *mod.judge(a, s))
