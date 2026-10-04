"""프랜차이즈 새 게임 → 첫 경기 시작까지 진행하며 단계마다 캡처. python tools/franchise.py <iso> <prefix>"""
import sys, time, os, subprocess
sys.path.insert(0, os.path.dirname(__file__)); import emu
iso, pre = sys.argv[1], sys.argv[2]
def alive(): return bool(emu._mypids())
def snap(n):
    if not alive(): print('DEAD at', n); sys.exit(2)
    try: emu.shot(f'work/{pre}_{n}.png')
    except Exception as e: print('shot fail', n, e)
emu.start(iso); time.sleep(35)
emu.keys('start w3 start w3 x w5'); time.sleep(6)
emu.keys('x w2 down w1 down w1 down w1 down w1 w1 x w8 x w8 x w8'); snap('a')
for i in range(6): emu.keys('x'); time.sleep(12)
snap('b')
emu.keys('x'); time.sleep(12); snap('c')
emu.keys('x'); time.sleep(12); snap('d')
emu.keys('x w3 x w3 down w1 x'); time.sleep(5); snap('e')
for i in range(6):
    time.sleep(15); snap(f'f{i}'); emu.keys('x')
time.sleep(30); snap('g')
p = emu.savestate(6); print(p)
open('work/ee_popup.bin','wb').write(emu.eemem(p))
