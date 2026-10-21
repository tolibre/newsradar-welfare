#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""뉴스레이다 복지·보건판(정다운 기자용) 생성기.

원본(tolibre/news-monitor — 김광일 기자 출입처판)의 파일을 그대로 가져와
'출입처·바이라인·브라우저 저장키·보관 기간' 같은 설정만 바꿔 이 저장소에 쓴다.
(기후·문체판 tolibre/newsradar-climate-culture 생성기와 같은 구조 — 설정 블록만 다르다.)

  python tools/make_variant.py <원본 저장소 경로> [<출력 경로, 기본=이 저장소>]

- 치환마다 '원본에서 정확히 몇 번 나와야 하는지'를 적어 두고, 다르면 아무 파일도
  쓰지 않고 멈춘다.
- 원본 쪽 파일은 읽기만 한다. 함수는 바꾸지 않는다(설정·문구만).
- 원본의 주체 출입처 배정·'전체' 탭 주체 가점(+2)·주요 매체 가점(+1)·사진 설명형 제목 거르기는
  원본 값 그대로 쓴다(김광일판과 같음).
"""
import hashlib, os, re, shutil, sys

# ---------------------------------------------------------------- 설정값 ---
REPORTER = "정다운"                       # 노컷 원문 author 메타 'CBS노컷뉴스 정다운 기자'로 가정 — 첫 실행 로그로 확인할 것
BEATS_TITLE = "보건복지부·질병관리청·식약처·성평등가족부"
STORE_PREFIX = "nm-wel-"                  # 브라우저 저장키 — 원본('nm-live-')·재경부판('nm-moef-')·국회판('nm-asm-')·
                                          # 산업부판('nm-ind-')·기후문체판('nm-cc-')과 같은 출처(tolibre.github.io)라 반드시 달라야 한다
# 섹션 순서 = 사용자가 말한 순서(부처 4곳) + 복지부 산하 공단 2곳(10/21 추가 요청). 그룹명은 제목에서 흔히 쓰는 약칭.
# 공단 둘은 따로 섹션을 둔다 — 국민연금은 기금 운용·지분 공시 기사가 많아 복지부 섹션에 섞으면 복지부 기사가 묻힌다.
GROUPS = ["복지부", "질병청", "식약처", "성평등부", "국민연금", "건보공단"]
REPORT_ORDER_JS = "[" + ",".join(f"'{g}'" for g in GROUPS) + "]"

NEW_BASE_KEYWORDS = '''BASE_KEYWORDS = [
    # 뉴스레이다 복지·보건판(tools/make_variant.py가 생성 — 직접 고치지 말 것).
    # '질병관리본부'는 2020년 청 승격 전 이름이라 넣지 않는다. '여성가족부·여가부'도 2025년 10월 개편 전 이름이라 뺐다.
    "보건복지부", "복지부",
    "질병관리청", "질병청",
    "식품의약품안전처", "식약처",
    "성평등가족부", "성평등부",
    # 복지부 산하 공단(사용자 10/21 추가). '국민연금'은 국민연금공단·국민연금기금·국민연금법을 모두 덮는다.
    # '건강보험공단'은 '국민건강보험공단'의 일부라 제목 판정에서 둘 다 걸린다('건강보험' 단독은 정책 기사 전반이라 넣지 않음).
    "국민연금",
    "건강보험공단", "건보공단",
]
'''
# 새 출입처를 KEYWORD_GROUPS에 넣는다 — 그래야 클러스터링의 '출입처명 토큰'(CLUSTER_AGENCY_TOKENS)과
# 주체 출입처 판정 단서에 들어간다(원본 0-31: 매핑이 없으면 그 이름 하나로 다른 사안이 묶인다).
NEW_GROUPS_LINE = ("KEYWORD_GROUPS.update(DUTY_KEYWORD_GROUPS)\n"
                   "KEYWORD_GROUPS.update({'보건복지부': '복지부', '복지부': '복지부',\n"
                   "                       '질병관리청': '질병청', '질병청': '질병청',\n"
                   "                       '식품의약품안전처': '식약처', '식약처': '식약처',\n"
                   "                       '성평등가족부': '성평등부', '성평등부': '성평등부',\n"
                   "                       '국민연금': '국민연금',\n"
                   "                       '건강보험공단': '건보공단', '건보공단': '건보공단'})   # 복지·보건판(생성기)\n")
# 짧은 약칭이 다른 단어의 일부로 걸리는 것 예방(원본 '산업부'·'중기부'와 같은 꼴):
# '복지부문·복지부담·복지부족·복지부정(수급)·복지부채·복지부서(지자체 복지 담당 부서)', '성평등부문'.
NEW_ANTI = ('    "개인정보위": [],\n'
            '    "복지부":   [r"복지부문", r"복지부담", r"복지부족", r"복지부정", r"복지부채", r"복지부서"],   # 복지·보건판(생성기)\n'
            '    "성평등부": [r"성평등부문"],   # 복지·보건판(생성기)\n')

# 기관장 이름 씨앗 — 이 저장소 DB는 시작 직후라 학습분이 없다. 기사로 확인(2026-10-21):
# 정은경 장관·현수엽 1차관·이형훈 2차관(복지부, 5/15 차관 인사), 임승관 청장(질병청), 오유경 처장(식약처, 10/13 국감),
# 원민경 장관(성평등부), 강청희 이사장(건보공단, 7/20 취임).
# 국민연금 이사장 '김성주'는 동명 방송인이 있어 넣지 않음 — DB 학습에 맡김. 인사가 바뀌면 고칠 것.
SEED = {"정은경": "복지부", "현수엽": "복지부", "이형훈": "복지부",
        "임승관": "질병청", "오유경": "식약처", "원민경": "성평등부",
        "강청희": "건보공단"}

# 뉴스레이다 '관련 약함' 접기(원본 0-58) — 원본은 과기정통부·우주항공청, 이 판은 국민연금·건보공단(사용자 10/22).
# 첫날 실측: 국민연금 섹션 83건 중 비정규직 통계·지자체 채용행사·코스피 칼럼처럼 본문에 '국민연금'이 스친 기사가 대부분,
# 건보공단은 공단 자료를 인용한 비만·검진 건강 기사가 많다. 판정은 원본 그대로(소관 관문 normal + check 노이즈 + 잡문,
# [단독]·제목에 이 판 기관명이 있는 기사는 접지 않음) — 그러려면 두 그룹의 소관 어휘(GROUP_SCOPE)가 있어야 한다.
WEAK_GROUPS = ("국민연금", "건보공단")
NEW_SCOPE = """GROUP_SCOPE = {
    # 복지·보건판(생성기) — '관련 약함' 접기용 소관 어휘. strong 하나면 관련, weak는 정책 신호어(POLICY_SIGNALS)와 함께일 때만.
    "국민연금": {
        "strong": [
            "연금개혁", "연금 개혁", "연금특위", "모수개혁", "구조개혁", "보험료율", "소득대체율",
            "수급개시", "수급연령", "수급 연령", "수급자", "수급권", "가입기간", "납부예외", "추납", "반환일시금",
            "노령연금", "유족연금", "장애연금", "연금액", "연금 수령", "연금수령", "조기연금", "연기연금", "크레딧",
            "기금운용", "기금 운용", "기금운용위원회", "기금위", "기금운용본부", "기금본부", "기금고갈", "기금 고갈", "고갈",
            "적립금", "운용수익", "운용 수익", "리밸런싱", "자산배분", "스튜어드십", "수탁자 책임", "수탁자책임",
            "의결권", "주주제안", "대표소송", "국민연금공단", "연금공단", "실버론", "기초연금", "퇴직연금", "노후소득",
            "미래세대",   # 연금 논쟁의 표지어('결국 미래세대 부담') — 본문에 국민연금이 걸린 기사 안에서만 쓰이므로 다른 분야 오탐 위험 낮음
            "김성주",   # 국민연금공단 이사장 — 동명 방송인이 있어 기관장 씨앗엔 안 넣었지만, 본문에 국민연금이 걸린 기사 안에선 안전
        ],
        "weak": ["연금", "노후", "기금", "수익률", "투자", "지분", "주주", "은퇴", "가입자"],
    },
    "건보공단": {
        "strong": [
            "건강보험", "건보", "보험료", "지역가입자", "직장가입자", "피부양자", "소득정산", "부과체계",
            "사무장병원", "불법개설", "면허대여", "특사경", "특별사법경찰", "부당청구", "환수",
            "요양급여", "장기요양", "요양보호사", "수가", "본인부담", "산정특례", "급여화", "비급여",
            "국고지원", "건강검진", "국가검진", "의료급여", "보장성",
            "강청희",   # 건보공단 이사장
        ],
        "weak": ["검진", "건강", "의료", "병원", "진료", "돌봄", "환자", "재정", "적자", "가입자", "비만", "질환"],
    },
"""

# (파일, 찾을 문자열 또는 정규식, 바꿀 문자열, 원본에서 나와야 하는 횟수, 정규식 여부)
NM = "news_monitor.py"
RP = "render_page.py"

REPLACEMENTS = [
    # ---- news_monitor.py: 출입처 ----
    # 0-44: 원본은 당직 출입처 8곳을 날마다 따로 수집한다(알림 없음, 뉴스레이다 '당직' 스위치로만 봄).
    # 복지·보건판은 쓰지 않는다 — 정다운 기자는 경제정책팀이 아니라 당직 대상이 아니다(사용자 10/21, 기후·문체판 0-47과 같음).
    (NM, "DUTY_COLLECT = True\n",
         "DUTY_COLLECT = False   # 복지·보건판은 당직 수집을 하지 않는다(생성기, 경제정책팀 아님)\n", 1, False),
    # 0-46: 원본의 EXCLUDE_TERMS(대한체육회·스포츠공정위·모의공정위)는 '공정위' 검색어 오탐용이다. 이 판은 '공정위'를
    # 검색하지 않으니 끈다(기후·문체판 0-46과 같음).
    (NM, r"EXCLUDE_TERMS = \[\n(?:.*\n)*?\]\n",
         "EXCLUDE_TERMS = []   # 이 판은 '공정위'를 검색하지 않아 공정위 오탐용 제외어가 필요 없다(생성기, 0-46)\n", 1, True),
    (NM, r"BASE_KEYWORDS = \[\n(?:.*\n)*?\]\n", NEW_BASE_KEYWORDS, 1, True),
    (NM, 'TEMP_KEYWORDS = {\n    "대미투자": "2026-09-23",\n}\n', "TEMP_KEYWORDS = {}\n", 1, False),
    (NM, "KEYWORD_GROUPS.update(DUTY_KEYWORD_GROUPS)\n", NEW_GROUPS_LINE, 1, False),
    (NM, '    "개인정보위": [],\n', NEW_ANTI, 1, False),
    # ---- news_monitor.py: '관련 약함' 접기 그룹·소관 어휘(원본 0-58 자리) ----
    (NM, 'LIVE_WEAK_FOLD_GROUPS = ("과기정통부", "우주항공청")\n',
         f'LIVE_WEAK_FOLD_GROUPS = {WEAK_GROUPS!r}   # 복지·보건판(생성기, 10/22)\n', 1, False),
    (NM, "GROUP_SCOPE = {\n", NEW_SCOPE, 1, False),
    # ---- news_monitor.py: 보관 기간 ----
    # 첫 실행 실측(10/21 17:52, 5,312건): 발행일 기준 10/20 1,178건·10/21 17시까지 1,542건 → 하루 1,200~1,800건,
    # 기후·문체판(1,500~2,000)과 비슷 → 같은 45일(약 6~8만 건). 처음엔 '국민연금' 양을 걱정해 30일로 시작했다.
    (NM, "RETENTION_DAYS = 90 ", "RETENTION_DAYS = 45 ", 1, False),
    # ---- news_monitor.py: 기관장 이름 씨앗(원본 0-38 자리) ----
    (NM, "ACTOR_PEOPLE_SEED = {}\n", f"ACTOR_PEOPLE_SEED = {SEED!r}   # 복지·보건판(생성기)\n", 1, False),
    # ---- news_monitor.py: 바이라인(본인 기사 섹션) ----
    (NM, 'BYLINE_NAME = "김광일"', f'BYLINE_NAME = "{REPORTER}"', 1, False),
    (NM, 'BYLINE_SECTION = "김광일 기자"', f'BYLINE_SECTION = "{REPORTER} 기자"', 1, False),

    # ---- render_page.py: 보고 양식 순서 ----
    (RP, "var REPORT_ORDER = ['방미통위','공정위','과기정통부','우주항공청'];",
         f"var REPORT_ORDER = {REPORT_ORDER_JS};", 2, False),
    (RP, "출입처 순서(방미통위 → 공정위 → 과기정통부 → 우주청 → 2진)",
         "출입처 순서(" + " → ".join(GROUPS) + ")", 2, False),
    # ---- render_page.py: 브라우저 저장키(같은 출처의 다른 페이지와 섞이지 않게) ----
    (RP, "'nm-live-", f"'{STORE_PREFIX}", 6, False),
    # ---- render_page.py: 출입처 식별색 ----
    # 부처 4곳이 원본의 네 출입처 색을 물려받는다. 공단 둘(국민연금·건보공단)은 기본 회색(--o-etc) — 산하기관이라 한 단 낮게.
    (RP, '[data-g="공정위"], [data-b="공정위"]', '[data-g="복지부"], [data-b="복지부"]', 1, False),
    (RP, '[data-g="과기정통부"], [data-b="과기정통부"]', '[data-g="질병청"], [data-b="질병청"]', 1, False),
    (RP, '[data-g="방미통위"], [data-b="방미통위"]', '[data-g="식약처"], [data-b="식약처"]', 1, False),
    (RP, '[data-g="우주항공청"], [data-b="우주항공청"]', '[data-g="성평등부"], [data-b="성평등부"]', 1, False),
    (RP, '[data-g="김광일 기자"], [data-b="김광일 기자"]',
         f'[data-g="{REPORTER} 기자"], [data-b="{REPORTER} 기자"]', 1, False),
    # ---- render_page.py: 기기 연동 숨김(GitHub 계정이 없는 기자는 못 쓴다 — 버튼만 숨김) ----
    (RP, '<button type="button" id="sync" class="sync off"',
         '<button type="button" id="sync" class="sync off" style="display:none"', 1, False),
    # ---- render_page.py: 화면 문구 ----
    (RP, "<title>뉴스레이다</title>", f"<title>뉴스레이다 · {BEATS_TITLE}</title>", 1, False),
    (RP, "document.title = '뉴스레이다 · ' + r.title;",
         "document.title = '뉴스레이다(복지) · ' + r.title;", 1, False),
    (RP, "맨 끝 ‘김광일 기자’는", f"맨 끝 ‘{REPORTER} 기자’는", 1, False),
    (RP, "과기정통부·우주항공청 묶음 중 소관 어휘가 없거나", "·".join(WEAK_GROUPS) + " 묶음 중 소관 어휘가 없거나", 1, False),
    (RP, "체크한 기사와 ‘여기까지 확인’은 이 기기에 저장되고, 머리줄 <b>기기 연동</b>을 켜면 다른 기기와 맞춰집니다(내 GitHub 비공개 gist). · <a href=\"../\">최신 다이제스트</a> · <a href=\"../archive/\">지난 다이제스트</a></p>",
         "체크한 기사와 ‘여기까지 확인’은 이 기기(브라우저)에만 저장됩니다 — PC와 폰은 따로 기억합니다.</p>", 1, False),
]

# 원본에서 그대로 가져오는 파일(치환 없음)
COPY_AS_IS = ["merge_db.py", "retitle.py"]

# 페이지에 남아 있으면 안 되는 문자열 — 주석(# / //)이 아닌 줄에서만 검사한다.
# (news_monitor.py는 문자열 대신 아래 EXPECT로 '실제로 import했을 때의 값'을 검사한다.
#  원본의 우주항공청·CBS 매핑·소관 어휘는 남아 있어도 검색어가 아니면 무해하다.)
FORBIDDEN = {
    RP: ["nm-live-", "김광일 기자\"", "기기 연동</b>", "방미통위 → 공정위"],
}
# 생성한 news_monitor.py를 별도 프로세스로 import해 확인할 값(당직·임시 키워드가 꺼진 날짜 기준).
EXPECT = {
    "DUTY_ONLY_GROUPS": [],   # 0-44 — 당직 수집 꺼짐(경제정책팀 아님)
    "EXCLUDE_TERMS": [],      # 0-46 — 공정위 오탐용 제외어 꺼짐
    "KEYWORDS": ["보건복지부", "복지부", "질병관리청", "질병청", "식품의약품안전처", "식약처",
                 "성평등가족부", "성평등부", "국민연금", "건강보험공단", "건보공단"],
    "GROUP_ORDER": GROUPS,
    "LIVE_WEAK_FOLD_GROUPS": list(WEAK_GROUPS),
    "RETENTION_DAYS": 45,
    "BYLINE_NAME": REPORTER,
    "BYLINE_SECTION": f"{REPORTER} 기자",
    "ACTOR_ASSIGN": True,
    "LIVE_ACTOR_BONUS": 2.0,
    "ACTOR_PEOPLE_SEED": SEED,
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(src_dir):
    out = {}
    for fname in {r[0] for r in REPLACEMENTS}:
        with open(os.path.join(src_dir, fname), encoding="utf-8") as f:
            out[fname] = f.read()
    errors = []
    for fname, old, new, count, is_re in REPLACEMENTS:
        text = out[fname]
        found = len(re.findall(old, text)) if is_re else text.count(old)
        if found != count:
            errors.append(f"{fname}: {old[:60]!r} — {count}번이어야 하는데 {found}번")
            continue
        out[fname] = re.sub(old, lambda m: new, text) if is_re else text.replace(old, new)
    if errors:
        raise SystemExit("원본이 예상과 달라 생성을 멈춥니다(아무 파일도 쓰지 않음):\n  "
                         + "\n  ".join(errors))
    leftovers = []
    for fname, pats in FORBIDDEN.items():
        for i, line in enumerate(out[fname].splitlines(), 1):
            s = line.strip()
            if s.startswith("#") or s.startswith("//"):
                continue
            for p in pats:
                if p in line:
                    leftovers.append(f"{fname}:{i}: {p!r} — {s[:80]}")
    if leftovers:
        raise SystemExit("원본 고유 문자열이 남았습니다:\n  " + "\n  ".join(leftovers))
    return out


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    src = os.path.abspath(sys.argv[1])
    dst = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else
                          os.path.join(os.path.dirname(__file__), ".."))
    out = apply(src)
    # 먼저 임시 폴더에 써서 import 검사를 통과한 뒤에만 실제 위치로 옮긴다.
    import json, subprocess, tempfile
    with tempfile.TemporaryDirectory() as tmp:
        for fname, text in out.items():
            with open(os.path.join(tmp, fname), "w", encoding="utf-8") as f:
                f.write(text)
        probe = ("import json, news_monitor as m; print(json.dumps({k: getattr(m, k) for k in %r}, "
                 "ensure_ascii=False))" % list(EXPECT))
        env = dict(os.environ, DUTY_MODE="")
        r = subprocess.run([sys.executable, "-c", probe], cwd=tmp, env=env,
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("생성본 import 실패:\n" + r.stderr[-2000:])
        got = json.loads(r.stdout.strip().splitlines()[-1])
        bad = {k: (got.get(k), v) for k, v in EXPECT.items() if got.get(k) != v}
        if bad:
            raise SystemExit(f"생성본 설정값이 예상과 다릅니다: {bad}")
    for fname, text in sorted(out.items()):
        with open(os.path.join(dst, fname), "w", encoding="utf-8") as f:
            f.write(text)
    for fname in COPY_AS_IS:
        shutil.copyfile(os.path.join(src, fname), os.path.join(dst, fname))
    for fname in sorted(list(out) + COPY_AS_IS):
        with open(os.path.join(src, fname), "rb") as a, open(os.path.join(dst, fname), "rb") as b:
            print(f"{fname:18s} 원본 {md5(a.read())} → 생성 {md5(b.read())}")


if __name__ == "__main__":
    main()
