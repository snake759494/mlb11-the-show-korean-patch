"""시범 경기 → 첫 타자 → 팁 닫기 → 2번 타자 등장 클로즈업 캡처. python tools/face2.py <iso> <prefix>"""
import sys, time, os
sys.path.insert(0, os.path.dirname(__file__)); import emu
from PIL import Image
iso, pre = sys.argv[1], sys.argv[2]
emu.start(iso); time.sleep(35)
emu.keys('start w3 start w3 x w5'); time.sleep(6)
emu.keys('x w3 x w6 left w1 x w6 x w3'); time.sleep(25)
emu.keys('x w3'); time.sleep(30); emu.keys('x w3'); time.sleep(30)
emu.keys('x w3'); time.sleep(5); emu.keys('x w3'); time.sleep(5); emu.keys('x w3')
time.sleep(130)
for k in range(6): emu.keys('x w1'); time.sleep(3)
for i in range(120):
    emu.shot(f'work/{pre}_{i:03d}.png'); time.sleep(0.4)
ims = [Image.open(f'work/{pre}_{i:03d}.png').resize((160, 120)) for i in range(120)]
b = Image.new('RGB', (1600, 1440)); [b.paste(im, ((i % 10) * 160, (i // 10) * 120)) for i, im in enumerate(ims)]; b.save(f'work/{pre}_grid.png')
