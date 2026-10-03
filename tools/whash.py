def h131(s):
    h = 0
    for c in s.encode('latin1') if isinstance(s, str) else s:
        c = c - 256 if c > 127 else c
        h = (h * 131 + c) & 0xffffffff
    return h
