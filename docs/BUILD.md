# 빌드
준비물: Python 3.11+ (numpy, Pillow, capstone, pyelftools), 원본 ISO, `NanumSquareNeo-dEb.ttf`, xdelta3

1. 저장소 루트에 원본 `MLB 11 - The Show (USA).iso` 와 `NanumSquareNeo-dEb.ttf` 를 둡니다.
2. `python tools/prepare.py` — 원본에서 파일 추출(extract/)과 원문 번역 묶음(work/batches 등)을 다시 만듭니다.
3. `python tools/build.py` — `MLB 11 - The Show (USA) (Korean).iso` 생성.
4. `xdelta3 -e -9 -S none -A -s "MLB 11 - The Show (USA).iso" "MLB 11 - The Show (USA) (Korean).iso" MLB11_PS2_KO_v1.0.xdelta`

검사: `python tools/checktr.py <묶음>`(번역 형식), `python tools/checknames.py NN`(이름), `python tools/audit.py`(미번역 집계).
검증용 에뮬레이터 조작: `tools/emu.py`, `tools/headcheck.py`(로드된 머리 모델 목록), `tools/franchise.py`.
