# 빌드
준비물: Python 3.11+ (numpy, Pillow, capstone, pyelftools), 원본 ISO, `NanumSquareNeo-dEb.ttf`, xdelta3

1. 저장소 루트에 원본 `MLB 11 - The Show (USA).iso` 와 `NanumSquareNeo-dEb.ttf` 를 둡니다.
2. `python tools/prepare.py` — 원본에서 파일 추출(extract/)과 원문 번역 묶음(work/batches 등)을 다시 만듭니다.
2-1. `translation/disp_src/disp_*.json` 을 `work/batches/` 에, `snap_english.txt` 를 `work/snap/english.txt` 로 복사합니다(표시 번역 원문 묶음).
3. `python tools/build.py` — `MLB 11 - The Show (USA) (Korean).iso` 생성.
4. `xdelta3 -e -9 -S none -A -s "MLB 11 - The Show (USA).iso" "MLB 11 - The Show (USA) (Korean).iso" MLB11_PS2_KO_v1.2.xdelta`

검사: `python tools/checktr.py <묶음>`(번역 형식), `python tools/checknames.py NN`(이름), `python tools/audit.py`(미번역 집계).
검증용 에뮬레이터 조작: `tools/emu.py`, `tools/headcheck.py`(로드된 머리 모델 목록), `tools/franchise.py`.
표시 훅 단위 검사: `python tools/hooktest.py`(unicorn 으로 Parse/GetQueryValue 훅 실행).

## 릴리즈 규칙
- 매 릴리즈에 `MLB11_PS2_KO_vX.Y.xdelta` 와 `widescreen/SCUS-97657_7892EFCF.pnach` 를 함께 첨부합니다.
- 릴리즈 노트 끝에 `docs/RELEASE_WIDESCREEN.md` 의 와이드 패치 적용 방법을 붙입니다.
