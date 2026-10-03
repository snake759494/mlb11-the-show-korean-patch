"""원문-번역 대응 이상 탐지: 숫자 누락, 길이 비율 이상."""
import json, glob, os, re, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MARK = re.compile(r'\^[a-z]\d*\^')
def run(names=None):
    bad = []
    for bp in sorted(glob.glob(os.path.join(ROOT, 'work', 'batches', '*.json'))):
        name = os.path.splitext(os.path.basename(bp))[0]
        if names and name not in names: continue
        kp = os.path.join(ROOT, 'translation', 'ko', name + '.json')
        if not os.path.exists(kp): continue
        K = json.load(open(kp, encoding='utf-8'))
        for it in json.load(open(bp, encoding='utf-8')):
            en = it['en']; ko = K.get(str(it['id']), '')
            pe = MARK.sub('', en); pk = MARK.sub('', ko)
            de = re.findall(r'\d+', pe); dk = re.findall(r'\d+', pk)
            r = len(pk) / max(1, len(pe))
            why = []
            if sorted(de) != sorted(dk) and not ('%' in en): why.append(f'숫자 {de}->{dk}')
            if len(pe) > 40 and (r < 0.18 or r > 1.3): why.append(f'길이비 {r:.2f}')
            if why: bad.append((name, it['id'], why, en[:80], ko[:80]))
    return bad
if __name__ == '__main__':
    b = run(sys.argv[1:] or None)
    for x in b: print(x)
    print(len(b))
