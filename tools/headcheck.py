"""시범 경기(TEX@SF) 시작 후 메모리에 로드된 선수 머리 모델 목록을 출력. python tools/headcheck.py <iso>"""
import sys, time, os, re
sys.path.insert(0, os.path.dirname(__file__)); import emu
iso = sys.argv[1]
emu.start(iso); time.sleep(35)
emu.keys('start w3 start w3 x w5'); time.sleep(6)
emu.keys('x w3 x w6 left w1 x w6 x w3'); time.sleep(25)
emu.keys('x w3'); time.sleep(30); emu.keys('x w3'); time.sleep(30)
emu.keys('x w3'); time.sleep(5); emu.keys('x w3'); time.sleep(5); emu.keys('x w3')
time.sleep(150)
p = emu.savestate(6); m = emu.eemem(p)
heads = sorted(set(x.decode() for x in re.findall(rb'face\.([A-Za-z]+_[A-Za-z]+)\.512', m)))
print(len(heads), heads)
