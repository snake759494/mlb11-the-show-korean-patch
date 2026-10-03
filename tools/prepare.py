"""원본 ISO 에서 작업 자료를 다시 만든다(저장소에는 영문 원문 묶음을 넣지 않음).
1) 작은 파일·WAD 파일 추출 → extract/   2) 번역 묶음 work/batches/*.json, 이름·notable 묶음, 목록 work/inv_*.json"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(__file__))
import iso, wad, names
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
def extract():
    os.makedirs(os.path.join(ROOT, 'extract', 'wad'), exist_ok=True)
    for p, l, s, r in iso.walk():
        if s < 20_000_000 and not p.endswith('.PSS') and not p.startswith('RAW'):
            q = os.path.join(ROOT, 'extract', p); os.makedirs(os.path.dirname(q), exist_ok=True)
            open(q, 'wb').write(iso.read(l, s))
    with open(iso.ISO, 'rb') as f:
        for h, s, o in wad.table():
            if s < 12_000_000:
                f.seek(wad.WAD_LBA * 2048 + o)
                open(os.path.join(ROOT, 'extract', 'wad', f'{h:08x}.bin'), 'wb').write(f.read(s))
def name_batches():
    P = {}
    for f in names.FILES:
        d = open(os.path.join(ROOT, 'extract', 'wad', f + '.bin'), 'rb').read()
        for o, a, b in names.pairs(d):
            if a != b: P[(a, b)] = 1
    L = sorted(P)
    for k, i in enumerate(range(0, len(L), 600)):
        json.dump([{'id': 300000 + i + j, 'first': a, 'last': b} for j, (a, b) in enumerate(L[i:i + 600])],
                  open(os.path.join(ROOT, 'work', f'batches_names_{k:02d}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
def notable_batch():
    d = open(os.path.join(ROOT, 'extract', 'wad', 'e32a33cf.bin'), 'rb').read()
    n = struct.unpack_from('<I', d, 0)[0]; items = {}
    for i in range(n):
        o = 4 + 200 * i + 100; e = d.index(b'\0', o); s = d[o:e].decode('latin1')
        if s and s not in items: items[s] = {'id': 200000 + len(items), 'en': s, 'max': 87, 'src': ['notable']}
    json.dump(list(items.values()), open(os.path.join(ROOT, 'work', 'batches', 'notable_00.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
if __name__ == '__main__':
    extract()
    os.makedirs(os.path.join(ROOT, 'work', 'batches'), exist_ok=True)
    import batches, batches2
    batches.main(); batches2.main(); notable_batch(); name_batches()
    print('ok')
