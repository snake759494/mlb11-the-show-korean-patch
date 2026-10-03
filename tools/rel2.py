"""REL 2차 대상: 단어형 표 문자열(R32 전용 참조) + printf 형식 메시지."""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(__file__)); import relstr
B = chr(92)
KEYLIKE = re.compile(r'[a-z][A-Z]|_|^[A-Z0-9/]{1,4}$|^\W+$|^\d')
CODEWORDS = {'Warning', 'WARNING', 'CONFIRM', 'Confirm', 'OK', 'YES', 'NO', 'Yes', 'No', 'CANCEL', 'Cancel', 'Continue', 'CONTINUE',
             'Error', 'ERROR', 'Notice', 'NOTICE', 'Done', 'DONE', 'Save', 'Load', 'SAVE', 'LOAD', 'Accept', 'Back', 'Help', 'Exit', 'Quit', 'Retry', 'RETRY'}
def candidates(fn):
    d, h, S, R, out = relstr.strings(fn)
    res = []
    for a, s, r in out:
        if relstr.display_like(s): continue
        p = re.sub(r'\^[a-z]\d*\^', '', s)
        if sum(c.isalpha() for c in p) < 2: continue
        if B in s or '.cpp' in s or '::' in s or '->' in s or '==' in s: continue
        fmt = bool(re.search(r'%[-0-9.]*[sdfiux]', s))
        types = {t for o, t in r}
        if fmt:
            if ' ' in p and sum(c.isalpha() for c in p) >= 8 and not re.search(r'[a-z][A-Z]|_|\[|\]', p): res.append((a, s, 'printf'))
            continue
        if '%' in s: continue
        if types == {2} and not KEYLIKE.search(p.strip()) and not '/' in p:
            res.append((a, s, 'table'))
        elif s in CODEWORDS:
            res.append((a, s, 'code'))
    return res
if __name__ == '__main__':
    allc = {}
    for m in ('FE', 'GAME', 'HRDERBY', 'INITDLL'):
        c = candidates(os.path.join(os.path.dirname(__file__), '..', 'extract', m + '.REL'))
        import collections
        print(m, collections.Counter(k for a, s, k in c))
        for a, s, k in c: allc.setdefault(s, set()).add(k)
    print(len(allc))
    json.dump({s: sorted(k) for s, k in allc.items()}, open(os.path.join(os.path.dirname(__file__), '..', 'work', 'rel2_cand.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
