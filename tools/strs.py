import re,sys
def strings(d, n=4):
    for m in re.finditer(rb'[\x20-\x7e]{%d,}' % n, d): yield m.start(), m.group().decode()
if __name__=='__main__':
    for fn in sys.argv[1:]:
        for o,s in strings(open(fn,'rb').read()): print(f'{fn}:{o:x}:{s}')
