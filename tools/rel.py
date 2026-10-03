"""SNR1 REL: header 12 words; symtab at h[3], h[4] entries x (name_off, a, b)."""
import struct
def load(fn):
    d = open(fn, 'rb').read()
    h = struct.unpack_from('<12I', d, 0)
    syms = []
    for i in range(h[4]):
        no, a, b = struct.unpack_from('<3I', d, h[3] + 12 * i)
        e = d.index(b'\0', no)
        syms.append((d[no:e].decode('latin1'), a, b))
    return d, h, syms
def relocs(d, h, S):
    """offset -> (type, symbol name or None, addend). type 2=R32 4=R26 5=HI16 6=LO16"""
    out = {}
    for i in range(h[2]):
        o, info, add = struct.unpack_from('<3I', d, h[1] + 12 * i)
        si = info >> 8
        out[o] = (info & 0xff, S[si][0] if si else None, add)
    return out
def cstr(d, o):
    e = d.find(b'\0', o)
    return d[o:e].decode('latin1') if 0 <= o < len(d) and e - o < 200 else None
