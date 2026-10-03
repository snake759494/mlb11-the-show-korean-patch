"""시범 경기 시작 → 첫 타자 등장 장면을 1초 간격으로 캡처. python tools/faceshot.py <iso> <prefix>"""
import sys, time, os
sys.path.insert(0, os.path.dirname(__file__)); import emu
iso, pre = sys.argv[1], sys.argv[2]
emu.start(iso); time.sleep(35)
emu.keys('start w3 start w3 x w5'); time.sleep(6)
emu.keys('x w3 x w6 left w1 x w6 x w3'); time.sleep(25)
emu.keys('x w3'); time.sleep(30)
emu.keys('x w3'); time.sleep(30)
emu.keys('x w3'); time.sleep(5)
emu.keys('x w3'); time.sleep(5)
emu.keys("x w3"); time.sleep(float(os.environ.get("FS_WAIT", 60)))
for i in range(70):
    emu.shot(f'work/{pre}_{i:02d}.png'); time.sleep(float(os.environ.get("FS_STEP", 0.8)))
from PIL import Image
ims = [Image.open(f'work/{pre}_{i:02d}.png').resize((160, 120)) for i in range(70)]
b = Image.new('RGB', (1600, 840)); [b.paste(im, ((i % 10) * 160, (i // 10) * 120)) for i, im in enumerate(ims)]; b.save(f'work/{pre}_grid.png')
