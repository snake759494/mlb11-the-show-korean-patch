import capstone, sys
D = open(__import__('os').path.join(__import__('os').path.dirname(__file__), '..', 'extract', 'SCUS_976.57'), 'rb').read()
md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS64 + capstone.CS_MODE_LITTLE_ENDIAN)
def dis(va, n):
    for i in range(n):
        a = va + 4 * i; o = a - 0x100000 + 0x80
        ins = list(md.disasm(D[o:o + 4], a))
        print(hex(a), ins[0].mnemonic + ' ' + ins[0].op_str if ins else D[o:o + 4].hex())
if __name__ == '__main__': dis(int(sys.argv[1], 16), int(sys.argv[2]))
