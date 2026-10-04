"""번역 결과 검사: python tools/checktr.py <묶음이름>   (work/batches/<이름>.json ↔ translation/ko/<이름>.json)
문제가 있으면 id 와 사유를 출력하고 종료코드 1."""
import sys, os, json, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MARK = re.compile(r'\^[a-z]\d*\^')
PH = re.compile(r'%\d|\[[A-Z_]+\]')
def nbytes(s): return sum(2 if 0xAC00 <= ord(c) <= 0xD7A3 else 1 for c in s)
SUBST = '·…“”‘’–—~　'
def check(en, ko, mx):
    errs = []
    if not isinstance(ko, str) or not ko: return ['빈 번역']
    if sorted(MARK.findall(en)) != sorted(MARK.findall(ko)): errs.append(f'마크업 불일치 {MARK.findall(en)} / {MARK.findall(ko)}')
    if sorted(PH.findall(en)) != sorted(PH.findall(ko)): errs.append(f'치환자 불일치 {PH.findall(en)} / {PH.findall(ko)}')
    for c in ko:
        o = ord(c)
        if not (0xAC00 <= o <= 0xD7A3 or 32 <= o < 127 or c in '\n\r\t' or c in SUBST):
            errs.append(f'허용 안 되는 문자 {c!r}'); break
    if mx is not None and nbytes(ko) > mx: errs.append(f'바이트 초과 {nbytes(ko)} > {mx}')
    if ko.count('"') > en.count('"'): errs.append('큰따옴표 추가')
    if ko.count(',') > en.count(',') and any(s == 'help' for s in []): errs.append('쉼표 추가')
    m1 = re.match(r'^(\s*(\^[a-z]\d*\^)*)', en).group(1); m2 = re.match(r'^(\s*(\^[a-z]\d*\^)*)', ko).group(1)
    if m1.replace(' ', '') != m2.replace(' ', '') and m1: errs.append(f'앞머리 코드 위치 {m1!r} / {m2!r}')
    return errs
def main(name):
    B = json.load(open(os.path.join(ROOT, 'work', 'batches', name + '.json'), encoding='utf-8'))
    p = os.path.join(ROOT, 'translation', 'ko', name + '.json')
    if not os.path.exists(p): print('출력 파일 없음', p); return 1
    T = json.load(open(p, encoding='utf-8'))
    bad = 0
    for it in B:
        if str(it['id']) not in T: print(it['id'], '번역 누락'); bad += 1; continue
        ko = T.get(str(it['id']))
        if ko is None and name.startswith('disp_'): continue      # 표시 번역 묶음: null = 건너뜀(내부 키 등)
        e = check(it['en'], ko, it['max'])
        if 'help' in it['src'] and ko.count(',') > it['en'].count(','): e.append('쉼표 추가(CSV)')
        if it.get('printf'):
            pf = re.compile(r'%[-0-9.]*[a-zA-Z]')
            if pf.findall(it['en']) != pf.findall(ko): e.append(f'printf 형식 순서 불일치 {pf.findall(it["en"])} / {pf.findall(ko)}')
        if e: print(it['id'], ' / '.join(e)); bad += 1
    print(f'{name}: {len(B)}개 중 문제 {bad}개')
    return 1 if bad else 0
if __name__ == '__main__': sys.exit(main(sys.argv[1]))
