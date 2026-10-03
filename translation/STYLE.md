# MLB 11 The Show (PS2) 한글화 번역 지침

## 출력 형식
- 입력 묶음 파일(JSON 배열)의 각 항목 `{"id": ..., "en": 원문, "max": 바이트 한도 또는 null, "src": 출처}` 에 대해
  출력 파일에 `{"<id>": "번역문", ...}` JSON 객체로 저장한다(UTF-8, ensure_ascii=False).
- 번역하지 않고 원문을 그대로 둘 항목은 원문을 그대로 넣는다(빈 문자열 금지).

## 반드시 지킬 것 (깨지면 게임 오류)
1. 마크업 코드는 원문 그대로, 같은 개수·순서로 유지: `^j0^ ^j1^ ^j2^`(정렬, 보통 맨 앞), `^n^`(줄바꿈), `^b숫자^`(버튼 아이콘),
   `^c숫자^`(색), `^d숫자^`(동적 값), `^t숫자^`(탭 위치), `^e^ ^r^`(®/™ 같은 기호). 코드 사이 공백도 가능한 한 유지.
2. 치환자 `%1 %2 %3 …`, `[AT_BATS]` 같은 대괄호 토큰은 그대로 둔다. 한국어 어순에 맞게 위치는 옮겨도 되지만 빠뜨리거나 늘리지 않는다.
3. 사용 가능한 문자: 한글 완성형 음절(가~힣), ASCII 출력 문자(영문·숫자·기호). 그 밖의 문자(한자, 자모 단독 ㅋ, 말줄임표 …, 가운뎃점 ·, 전각 기호, 이모지)는 쓰지 않는다. 말줄임은 `...`.
4. `"max"` 가 숫자인 항목은 번역문의 바이트 수(한글 1음절 = 2바이트, ASCII 1글자 = 1바이트)가 그 값 이하여야 한다. 넘으면 줄여 쓴다.
5. 큰따옴표 `"` 와 쉼표 `,` 를 원문에 없던 곳에 새로 넣지 않는다(일부 데이터가 CSV 형식).
6. 원문 앞뒤 공백, 맨 앞의 `^j1^` 같은 코드 위치를 유지한다.

## 번역하지 않는 것
- 선수·감독·코치·실존 인물 이름, 팀 이름(Yankees 등), 도시명, 구장명, 리그 약칭(MLB, AL, NL), 방송인 이름.
- 표 머리 등 짧은 통계 약어: AVG, HR, RBI, ERA, W, L, SV, K, BB, SO, OBP, SLG, OPS, IP, H, R, ER, WHIP, G, GS, AB, 2B, 3B, SB, CS, PCT, GB, L10, STRK, RS, RA, OVR, POT, POS, B/T, AGE 등은 그대로 둔다.
- 화면에 나오지 않는 것으로 보이는 내부 이름(밑줄이 있는 식별자, 파일 이름)과 자리 표시용 더미 문자열(xxxx, 0000, WWWW, 의미 없는 이름)은 원문 그대로.

## 문체
- 메뉴·버튼·제목: 짧은 명사형. (예: OPTIONS → 옵션, VIEW ROSTER → 로스터 보기, Accept → 확인)
- 설명문·도움말·시스템 안내: 합니다체. (예: "~을 설정합니다.", "~할 수 있습니다.")
- 등장인물 대사(감독·코치·단장·에이전트·동료가 선수에게): 자연스러운 구어체. 감독/코치 → 선수는 반말(해라/해 체), 에이전트·구단 직원 → 선수는 해요체.
- 영어 원문의 대문자 강조는 한국어에서 의미로 살린다(필요하면 따옴표 없이 그대로).
- 화면 폭이 좁으므로 원문보다 길어지지 않게 간결하게. 한글 1음절은 영문 대문자 약 1.3자 폭이다.
- 원문 문장이 중간에서 끊긴 조각(다른 문자열과 이어 붙여 쓰는 경우)이면 조각 그대로 자연스럽게 이어질 수 있게 번역한다.

## 용어집 (일관성 유지)
| 영어 | 한국어 |
|---|---|
| Exhibition | 시범 경기 |
| Season | 시즌 |
| Franchise | 프랜차이즈 |
| Road to the Show (RTTS) | 로드 투 더 쇼 |
| Home Run Derby | 홈런 더비 |
| Manager Mode | 감독 모드 |
| Rivalry | 라이벌전 |
| Quick Game / Play Now | 빠른 경기 / 바로 시작 |
| Features | 부가 기능 |
| Options / Settings | 옵션 / 설정 |
| Load / Save | 불러오기 / 저장 |
| Main Menu | 메인 메뉴 |
| Back / Accept / Advance / Select / Cancel / Help / Exit | 뒤로 / 확인 / 진행 / 선택 / 취소 / 도움말 / 나가기 |
| Roster / Lineup / Depth Chart / Bullpen | 로스터 / 라인업 / 뎁스 차트 / 불펜 |
| Player Card | 선수 카드 |
| Starting Pitcher / Relief Pitcher / Closer / Setup | 선발 투수 / 구원 투수 / 마무리 투수 / 셋업맨 |
| Catcher / First Base(man) / Second / Third / Shortstop | 포수 / 1루수 / 2루수 / 3루수 / 유격수 |
| Left/Center/Right Field(er) / Outfielder / Infielder | 좌익수 / 중견수 / 우익수 / 외야수 / 내야수 |
| Designated Hitter / Pinch Hitter / Pinch Runner | 지명타자 / 대타 / 대주자 |
| Batting / Pitching / Fielding / Baserunning | 타격 / 투구 / 수비 / 주루 |
| Batting Average / Home Run / RBI | 타율 / 홈런 / 타점 |
| Hit / Double / Triple / Single | 안타 / 2루타 / 3루타 / 단타 |
| Walk / Strikeout / Hit by Pitch | 볼넷 / 삼진 / 몸에 맞는 공 |
| Stolen Base / Caught Stealing | 도루 / 도루 실패 |
| ERA | 평균자책점 |
| Win / Loss / Save / Hold | 승 / 패 / 세이브 / 홀드 |
| Error | 실책 |
| Bunt / Sacrifice / Squeeze | 번트 / 희생 / 스퀴즈 |
| Pickoff / Pitchout / Intentional Walk | 견제 / 피치아웃 / 고의사구 |
| Fastball / 4-Seam / 2-Seam / Cutter / Sinker | 패스트볼 / 포심 / 투심 / 커터 / 싱커 |
| Curveball / Slider / Changeup / Splitter / Forkball | 커브 / 슬라이더 / 체인지업 / 스플리터 / 포크볼 |
| Knuckleball / Knuckle Curve / Slurve / Screwball / Palmball / Circle Change | 너클볼 / 너클 커브 / 슬러브 / 스크루볼 / 팜볼 / 서클 체인지업 |
| Velocity / Break / Control / Stamina | 구속 / 변화 / 제구 / 체력 |
| Contact / Power / Vision / Discipline / Clutch | 컨택트 / 파워 / 선구안 / 인내심 / 클러치 |
| Speed / Arm Strength / Arm Accuracy / Reaction / Blocking | 스피드 / 송구력 / 송구 정확도 / 반응 / 블로킹 |
| Ratings / Attributes / Potential | 능력치 / 능력 / 잠재력 |
| Training Points | 훈련 포인트 |
| Goals | 목표 |
| Trade / Free Agent / Contract / Arbitration / Waivers | 트레이드 / FA(자유계약선수) / 계약 / 연봉 조정 / 웨이버 |
| Draft / Amateur Draft | 드래프트 / 신인 드래프트 |
| Minor League / AAA / AA | 마이너리그 / 트리플A / 더블A |
| Call up / Send down / Option | 콜업 / 강등 / 마이너 이관 |
| Disabled List / Injury | 부상자 명단 / 부상 |
| Rookie / Veteran / All-Star / Hall of Fame / Legend (난이도) | 루키 / 베테랑 / 올스타 / 명예의 전당 / 레전드 |
| Hall of Fame (명예) | 명예의 전당 |
| MVP / Cy Young / Gold Glove / Silver Slugger | MVP / 사이 영 상 / 골드 글러브 / 실버 슬러거 |
| Rookie of the Year | 올해의 신인 |
| World Series / Playoffs / Postseason | 월드 시리즈 / 플레이오프 / 포스트시즌 |
| American League / National League / Division | 아메리칸 리그 / 내셔널 리그 / 지구 |
| Spring Training / Offseason / Regular Season | 스프링 캠프 / 오프시즌 / 정규 시즌 |
| Standings / Schedule / Stats / Leaders | 순위 / 일정 / 기록 / 리더 |
| Manager / General Manager / Coach / Agent / Owner | 감독 / 단장 / 코치 / 에이전트 / 구단주 |
| Memory Card (8MB)(for PlayStation^r^2) | 메모리 카드 (8MB)(PlayStation^r^2용) |
| Controller / DUALSHOCK^r^2 | 컨트롤러 / DUALSHOCK^r^2 |
| Difficulty / Sliders | 난이도 / 슬라이더 |
| Guess Pitch | 구종 예측 |
| Analog Pitching / Classic | 아날로그 투구 / 클래식 |
| Pitch Count | 투구 수 |
| Inning / Out / Count / Ball / Strike | 이닝 / 아웃 / 카운트 / 볼 / 스트라이크 |
| Home / Away / Road | 홈 / 원정 / 원정 |
| Profile | 프로필 |
| Unlock / Reward | 해제 / 보상 |
| Fans / Attendance / Revenue / Budget | 팬 / 관중 / 수익 / 예산 |
