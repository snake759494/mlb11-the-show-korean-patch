"""ISO 부팅 → 시범 경기 → 타석 화면 캡처.  python tools/togame.py <iso> <prefix>"""
import sys, time, os
sys.path.insert(0, os.path.dirname(__file__)); import emu
iso, pre = sys.argv[1], sys.argv[2]
emu.start(iso); time.sleep(35)
emu.keys('start w3 start w3 x w5'); time.sleep(6)
emu.keys('x w3 x w6 left w1 x w6 x w3'); time.sleep(25)
emu.keys('x w3'); time.sleep(30)
emu.keys('x w3'); time.sleep(30)
emu.keys('x w3'); time.sleep(5)
emu.keys('x w3'); time.sleep(50)
for i in range(6):
    emu.keys('x w2 start w2'); time.sleep(6)
emu.keys('start w3'); time.sleep(3)
for i in range(4):
    emu.shot(f'work/{pre}{i}.png'); emu.keys('x w2'); time.sleep(8)
