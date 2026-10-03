"""python tools/checknames.py NN : work/batches_names_NN.json ↔ translation/names/names_NN.json
출력 형식 {"id": ["이름", "성"]}, 각 15바이트(한글 1음절=2) 이하, 한글 음절/공백/점/하이픈만."""
import sys, json, re
n = sys.argv[1]
B = json.load(open(f'work/batches_names_{n}.json', encoding='utf-8'))
T = json.load(open(f'translation/names/names_{n}.json', encoding='utf-8'))
bad = 0
def nb(s): return sum(2 if 0xAC00 <= ord(c) <= 0xD7A3 else 1 for c in s)
for it in B:
    v = T.get(str(it['id']))
    ok = isinstance(v, list) and len(v) == 2 and all(isinstance(x, str) and x and nb(x) <= 15 and re.fullmatch(r"[가-힣 .'\-A-Za-z]+", x) for x in v)
    if ok and not any(0xAC00 <= ord(c) <= 0xD7A3 for c in v[0] + v[1]): ok = False
    if not ok: print(it['id'], it['first'], it['last'], v); bad += 1
print(f'names_{n}: {len(B)} items, problems {bad}')
sys.exit(1 if bad else 0)
