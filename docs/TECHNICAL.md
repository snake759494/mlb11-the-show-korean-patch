# 기술 메모

## 디스크
- ISO9660 + UDF 브리지. 실행파일 `SCUS_976.57` + 모듈 `FE/GAME/HRDERBY/INITDLL.REL`(SNR1 재배치 형식), 데이터 `MLBPS2.WAD`(1.49 GB).
- WAD: `[u32 개수][u32][개수 × (해시, 크기, 오프셋)]`, 해시 오름차순. 해시 = 대문자·역슬래시 경로에 `h = h*131 + c`(부호 있는 바이트).
- 빌드는 바뀐 파일을 WAD 끝에 덧붙이고, WAD 바로 뒤 파일들(SYSTEM.CNF, MODULES, CHANTS.SKX 등)을 ISO 끝으로 옮겨 공간을 만든 뒤 ISO9660·UDF(파일 엔트리, 파티션 길이, 앵커)를 갱신합니다.

## REL(SNR1)
- 머리 12워드: [1]=재배치표 위치, [2]=개수, [3]=심볼표, [4]=심볼 수. 재배치 `(위치, (심볼<<8)|형식, addend)`, 형식 2=R32 4=R26 5=HI16 6=LO16.
- HRDERBY.REL 에만 심볼 이름이 있어, 같은 코드를 FE/GAME 에서 재배치 칸을 가린 바이트 패턴으로 찾았습니다(`tools/fmatch.py`).
- 내장 문자열 번역은 문자열 칸들을 모은 풀에 다시 배치하고 재배치 addend 를 바꿉니다(파일 크기 불변, `tools/relinject.py`).
  한 단어 문자열 일부(팀 별칭, Grass, 눈/머리 색, Left/Right, 목표 조건 등)는 텍스처·판정 키로도 쓰여 번역하면 그래픽이 깨지므로, 옵션 표 영역·팝업 제목·검증한 목록만 번역합니다.

## 글꼴·한글 출력
- 글꼴 = `frontend\art\fonts\english.bin/tx2`(3페이지), `symbols.bin/tx2`. 글리프 28바이트(UV 4float, 폭·높이·y보정·앞뒤 여백). 텍스처는 8bpp PSMT8 을 CT32 로 스위즐 업로드하는 TX00(IFF0) 형식.
- 글자 그리기 명령에 문자 1바이트 + 페이지 4비트가 들어가므로, 리드 0x80~0x8B / 트레일 0x80~0xFF 2바이트 코드를 페이지 3~9(english) · 11~15(symbols) 로 보냅니다. 심볼 페이지는 3→10 으로 이동(SetSymbolPage 인자 수정).
- 텍스처는 512×512 로 확장(1024 폭은 GS 제약으로 표시 실패).

## UI·텍스트 데이터
- 화면: `IFF0ASSH` 묶음 안 `VOIDASS0` 청크, 문자열은 청크 상대 u32 참조. 표시용 참조만 바꾸고, 길어지면 청크 끝에 붙이고 머리 오프셋을 갱신(`tools/inject.py`).
- 도움말 바 `FE.txt`(CSV), `goals.txt`/`eggs.txt`(TSV), RTTS 목표 레코드 스트림, `notable.bin`(200바이트 레코드).
- 선수 DB(TGDF): 이름 16 + 성 16 고정 칸, 구단 표 `D_TEAM_PROF`(52바이트)·`ROSTERS`.

## 선수 머리
`MlbPlayerInfo::GeneratePlayerInfo` 가 `data/heads/%s_%s/` + `PackFile.PS2` 를 DB 이름(공백·'.,`- 제거)으로 만듭니다. 한글 이름 경로의 해시를 원래 머리 파일을 가리키는 WAD 항목으로 추가했습니다(목록이 커져 겹치는 앞쪽 파일은 끝으로 이동).
