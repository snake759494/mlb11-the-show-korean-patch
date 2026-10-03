"""MLBPS2.WAD: [u32 n][u32 ?] + n x (hash, size, offset) 해시 오름차순, 데이터 연속 배치."""
import struct, os, sys
sys.path.insert(0, os.path.dirname(__file__)); import iso
WAD_LBA = 9606
def table(isop=iso.ISO):
    h = iso.read(WAD_LBA, 0x16000, isop)
    n = struct.unpack_from('<I', h, 0)[0]
    return [struct.unpack_from('<3I', h, 8 + 12 * i) for i in range(n)]
def get(hsh, isop=iso.ISO):
    for h, s, o in table(isop):
        if h == hsh:
            with open(isop, 'rb') as f:
                f.seek(WAD_LBA * 2048 + o); return f.read(s)
