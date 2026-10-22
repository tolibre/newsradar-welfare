# -*- coding: utf-8 -*-
"""사회정책팀 휴일 특근(당직) 묶음 — 뉴스레이다 사회정책팀 변형판 공용 설정.

사용자 결정(2026-10-22 15:19): "김동빈, 정다운, 양형욱은 모두 사회정책팀이야. 세 명을 그룹화해서
휴일 당직 기능을 만들자. 세 사람이 쓰는 키워드를 합하면 돼. 사회정책팀은 김민재, 박종환 기자도 있는데
그들 뉴스레이다 페이지는 나중에 만들고 그때 같이 더 묶어주자."

원본(tolibre/news-monitor)의 당직 묶음은 경제정책팀 8곳이다(DUTY_KEYWORDS). 사회정책팀 판들은 생성기가
그 자리를 이 파일의 팀 묶음으로 바꾼다. 각 판은 묶음 중 **자기 섹션이 아닌 그룹만** 당직으로 모은다
(원본 규칙: DUTY_ONLY_GROUPS = 당직 그룹 - GROUP_ORDER) — 그룹 이름이 각 판의 섹션 이름과 같아야 한다.

**이 파일은 사회정책팀 판 저장소마다 똑같은 사본이 있다**(newsradar-climate-culture·newsradar-welfare·newsradar-labor).
팀원이 늘면(김민재·박종환) MEMBERS에 한 줄씩 넣고, **모든 사회정책팀 저장소의 사본을 같은 내용으로 바꾼 뒤** 각 생성기를 다시 돌릴 것.
"""

# (기자, [(검색어, 그룹), ...]) — 순서 = 당직 섹션 순서. 검색어·그룹은 각자 판의 설정과 같게.
MEMBERS = [
    ("양형욱", [("기후에너지환경부", "기후부"), ("기후부", "기후부"),
              ("문화체육관광부", "문체부"), ("문체부", "문체부")]),
    ("정다운", [("보건복지부", "복지부"), ("복지부", "복지부"),
              ("질병관리청", "질병청"), ("질병청", "질병청"),
              ("식품의약품안전처", "식약처"), ("식약처", "식약처"),
              ("성평등가족부", "성평등부"), ("성평등부", "성평등부"),
              ("국민연금", "국민연금"),
              ("건강보험공단", "건보공단"), ("건보공단", "건보공단")]),
    ("김동빈", [("고용노동부", "노동부"), ("노동부", "노동부"), ("고용부", "노동부"),
              ("노동장관", "노동부"), ("노동차관", "노동부"),
              ("노동", "노동")]),
]

# 단어 일부 오매칭 예방 — 각 판에서 쓰던 것을 합친다(당직 수집도 같은 규칙으로 제목을 판정한다).
ANTI = {
    "기후부":   [r"기후부문", r"기후부담", r"기후부채", r"기후부진", r"기후부자"],
    "복지부":   [r"복지부문", r"복지부담", r"복지부족", r"복지부정", r"복지부채", r"복지부서"],
    "성평등부": [r"성평등부문"],
    "고용부":   [r"고용부진", r"고용부담", r"고용부문", r"고용부족", r"고용부채"],
    "노동":     [r"노동신문", r"조선노동당", r"노동당(?!국)", r"매일노동뉴스"],
}

# 제목 판정 전용(네이버 검색 안 함) — 노동판 0-66
NO_SEARCH = ["노동장관", "노동차관"]

# 사안어(부처명이 아님) — 클러스터링 '출입처명 토큰'에서 뺀다(원본 0-28 누리호와 같은 이유).
# 당직 매핑(DUTY_KEYWORD_GROUPS)에 들어가면 KEYWORD_GROUPS를 거쳐 출입처명 토큰이 되기 때문.
TOPIC_WORDS = ["노동"]

DUTY_KEYWORDS = [k for _, kws in MEMBERS for k, _g in kws]
DUTY_GROUPS = {k: g for _, kws in MEMBERS for k, g in kws}
ALL_GROUPS = []
for _k in DUTY_KEYWORDS:
    if DUTY_GROUPS[_k] not in ALL_GROUPS:
        ALL_GROUPS.append(DUTY_GROUPS[_k])


def duty_only(own_groups):
    """이 판에서 당직으로만 모을 그룹(원본 DUTY_ONLY_GROUPS 계산과 같은 순서)."""
    return [g for g in ALL_GROUPS if g not in own_groups]


def duty_keywords_block():
    body = "".join(f"    # {name}\n    " + ", ".join(f'"{k}"' for k, _ in kws) + ",\n" for name, kws in MEMBERS)
    return ("DUTY_KEYWORDS = [\n"
            "    # 사회정책팀 휴일 특근 묶음(tools/social_team.py — 생성기가 원본 경제정책팀 묶음 자리에 넣는다)\n"
            + body + "]\n")


def duty_groups_block():
    body = "".join("    " + ", ".join(f'"{k}": "{g}"' for k, g in kws) + ",\n" for _, kws in MEMBERS)
    return "DUTY_KEYWORD_GROUPS = {\n" + body + "}\n"


def anti_lines():
    return "".join(f'    "{k}": ' + "[" + ", ".join(f'r"{p}"' for p in pats) + "],   # 사회정책팀(social_team.py)\n"
                   for k, pats in ANTI.items())


def max_pages_block():
    return ('KEYWORD_MAX_PAGES = {\n    "CBS": 1,\n    '
            + ", ".join(f'"{k}": 0' for k in NO_SEARCH)
            + ",   # 사회정책팀(social_team.py) — 제목 판정 전용\n}\n")


def topic_line():
    return "CLUSTER_TOPIC_KEYWORDS = {" + ", ".join(f'"{w}"' for w in ["누리호"] + TOPIC_WORDS) + "}   # 사회정책팀 사안어 추가(social_team.py)\n"


def replacements(NM):
    """세 생성기가 REPLACEMENTS 앞에 붙이는 치환(원본 기준 문자열·횟수)."""
    return [
        (NM, r"DUTY_KEYWORDS = \[\n(?:.*\n)*?\]\n", duty_keywords_block(), 1, True),
        (NM, r"DUTY_KEYWORD_GROUPS = \{\n(?:.*\n)*?\}\n", duty_groups_block(), 1, True),
        (NM, 'KEYWORD_MAX_PAGES = {\n    "CBS": 1,\n}\n', max_pages_block(), 1, False),
        (NM, 'CLUSTER_TOPIC_KEYWORDS = {"누리호"}\n', topic_line(), 1, False),
        (NM, '    "개인정보위": [],\n', '    "개인정보위": [],\n' + anti_lines(), 1, False),
    ]
