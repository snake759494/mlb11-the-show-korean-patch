import sys, os, capstone
sys.path.insert(0, os.path.dirname(__file__)); import rel
md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS64 + capstone.CS_MODE_LITTLE_ENDIAN)
_cache = {}
def ld(fn):
    if fn not in _cache:
        d, h, S = rel.load(fn); _cache[fn] = (d, h, S, rel.relocs(d, h, S), {a: s for s, a, b in S if a})
    return _cache[fn]
def dis(fn, addr, n=40):
    d, h, S, R, names = ld(fn); out = []
    for i in range(n):
        a = addr + 4 * i; w = d[a:a + 4]
        ins = list(md.disasm(w, a))
        t = f'{ins[0].mnemonic} {ins[0].op_str}' if ins else f'.word {w.hex()}'
        if a in R:
            ty, sym, add = R[a]
            if sym: t += f'   ; ->{sym}+{add:x}'
            else:
                s = rel.cstr(d, add)
                t += f'   ; ->{add:x}' + (f' "{s}"' if s and len(s) > 2 and s.isprintable() else '') + (f' <{names[add]}>' if add in names else '')
        out.append(f'{a:08x}: {t}' + (f'   <<{names[a]}>>' if a in names else ''))
    return '\n'.join(out)
if __name__ == '__main__':
    print(dis(sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3]) if len(sys.argv) > 3 else 40))
