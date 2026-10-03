# 권리 및 외부 자료

이 저장소는 비공식 한국어 패치의 제작 소스·번역·검증 자료 공개용입니다. 원작 게임 「MLB 11 The Show」(PS2, Sony Computer Entertainment America / San Diego Studio)와 그 텍스트·이미지·음성·영상·실행 코드, MLB 및 구단·선수 관련 상표·초상의 권리는 각 권리자에게 있습니다. 원본 게임, 패치 적용 게임, 게임에서 추출한 실행파일·텍스처·음성·데이터는 배포하지 않으며, 릴리즈에는 원본 디스크 이미지가 있어야만 쓸 수 있는 차분 파일(xdelta)만 첨부합니다.

번역 자료(`translation/ko`, `translation/names`)에는 **영어 원문을 넣지 않았습니다**. 문장은 번호로만 연결되며, 빌드할 때 `tools/prepare.py` 가 사용자의 원본 이미지에서 원문 묶음을 다시 만듭니다. 수동 보정 파일(`translation/fix`, `translation/rel_safe_words.json`)에는 보정 대상을 가리키기 위한 짧은 단어·고유명사만 들어 있습니다.

저장소 공개 자체가 모든 파일에 동일한 오픈소스 라이선스를 부여한다는 뜻은 아닙니다. 자체 제작 코드·번역 전체에 대한 별도 포괄 라이선스는 현재 지정하지 않았습니다.

NanumSquare Neo 는 SIL Open Font License 1.1 을 따르며 전문을 `LICENSES/NanumSquareNeo-OFL-1.1.txt` 에 보존했습니다(`docs/FONT_CREDITS.md`). xdelta, PCSX2, Python 라이브러리(numpy, Pillow, capstone, pyelftools, fontTools) 등 외부 도구는 각 프로젝트의 라이선스를 따르며 바이너리를 재배포하지 않습니다. 게임 코드의 디스어셈블 결과물은 넣지 않았고, 해석한 내용만 `docs/TECHNICAL.md` 에 정리했습니다.
