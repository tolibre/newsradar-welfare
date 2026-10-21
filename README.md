# 뉴스레이다 · 복지·보건판

CBS노컷뉴스 정다운 기자용 보고 준비 페이지.
원본 [tolibre/news-monitor](https://github.com/tolibre/news-monitor)(김광일 기자 출입처판)에서 설정만 바꿔 만든 판이다.
같은 방식: 재경부판 [tolibre/newsradar-moef](https://github.com/tolibre/newsradar-moef) · 국회판 [tolibre/newsradar-assembly](https://github.com/tolibre/newsradar-assembly) · 산업부판 [tolibre/newsradar-industry](https://github.com/tolibre/newsradar-industry) · 기후·문체판 [tolibre/newsradar-climate-culture](https://github.com/tolibre/newsradar-climate-culture).

- 페이지: https://tolibre.github.io/newsradar-welfare/ (→ `/live/`)
- 섹션: 복지부 · 질병청 · 식약처 · 성평등부 · 국민연금 · 건보공단 (+ 맨 끝 정다운 기자 본인 기사, 보고 양식에서 `<기처리>`)
- 보고: 업무일 09:00 · 14:00 (원본과 같은 구간·화면 전환 시각)

## 코드를 직접 고치지 말 것

`news_monitor.py`·`render_page.py`·`merge_db.py`·`retitle.py`는 **`tools/make_variant.py`가 원본에서 생성**한다.

```
git clone --depth 1 https://github.com/tolibre/news-monitor /tmp/nm
python tools/make_variant.py /tmp/nm .
```

생성기는 치환마다 원본 등장 횟수를 검사하고, 생성본을 import해 검색어·그룹·보관 기간 값을 확인한 뒤에만 파일을 쓴다. 함수는 바꾸지 않는다.

## 원본과 다른 점

| | 원본 | 이 판 |
|---|---|---|
| 검색어 | 공정위·방미통위·과기정통부·우주항공청·CBS 등 | 보건복지부·복지부 · 질병관리청·질병청 · 식품의약품안전처·식약처 · 성평등가족부·성평등부 · 국민연금 · 건강보험공단·건보공단 |
| 그룹 | — | 복지부 · 질병청 · 식약처 · 성평등부 · 국민연금 · 건보공단. 검색어 11개 모두 `KEYWORD_GROUPS`에 매핑(클러스터링 출입처명 토큰·주체 판정 단서) |
| 오탐 예방 | — | '복지부문·복지부담·복지부족·복지부정·복지부채·복지부서', '성평등부문' 제외. 옛 이름(질병관리본부·여성가족부)은 검색어에 넣지 않음 |
| 섹션 색 | — | 부처 4곳은 원본 네 출입처 색, 공단 2곳은 기본 회색 |
| DB 보관 | 90일 | 45일(첫 실행 실측 하루 1,200~1,800건 — 기후·문체판과 비슷) |
| '관련 약함' 접기(원본 0-58) | 과기정통부·우주항공청 | **국민연금·건보공단** — 소관 어휘(`GROUP_SCOPE`)를 이 판에서 정의. 첫날 실측 국민연금 53묶음 중 36~39·건보공단 21묶음 중 11 접힘 |
| 기관장 이름 씨앗 | — | 정은경·현수엽·이형훈(복지부), 임승관(질병청), 오유경(식약처), 원민경(성평등부), 강청희(건보공단) — 국민연금 이사장은 동명이인이 있어 DB 학습에 맡김 |
| 당직(휴일 특근) | 있음 | 없음(경제정책팀 아님) |
| 본인 기사 섹션 | 김광일 기자 | 정다운 기자 |
| 브라우저 저장키 | `nm-live-*` | `nm-wel-*` |
| 기기 연동·텔레그램·digest 페이지·수확 | 있음 | 없음(다른 변형판과 같음) |

주체 출입처 배정·'전체' 탭 주체 가점·주요 매체 가점·사진 설명형 제목 거르기·노컷 기출고 표시는 원본(김광일판)과 같다.

## 운영 (cron-job.org → workflow_dispatch)

URL `https://api.github.com/repos/tolibre/newsradar-welfare/actions/workflows/newsradar-welfare.yml/dispatches`, POST,
헤더는 원본 잡과 같음(PAT `news-monitor-cron`에 이 저장소 추가 필요), 시간대 Asia/Seoul.

| 잡 | 스케줄 | body |
|---|---|---|
| wel-check | `0 * * * *` | `{"ref":"main","inputs":{"mode":"check"}}` |
| wel-precut | `25 8,13 * * 1-5` | 위와 같음 |
| wel-digest | `0 6 * * *` | `{"ref":"main","inputs":{"mode":"digest"}}` |
| wel-retitle | `15 */2 * * *` | `{"ref":"main","inputs":{"mode":"retitle","apply":"1","limit":"100"}}` |

Secrets: `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`(원본과 같은 값). Pages: main / docs.
