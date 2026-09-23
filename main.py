import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from collections import Counter

st.set_page_config(
    page_title="송탄고 급식 데이터 분석",
    page_icon="🍲",
    layout="wide"
)

st.title("🍲 송탄고등학교 급식 데이터 분석")
st.subheader("자주 나오는 국 종류는 무엇일까?")

st.write(
    "2026년 송탄고등학교 급식 메뉴를 분석하여 "
    "가장 자주 등장하는 국 종류를 알아봅니다."
)

# ---------------------------------------
# 송탄고등학교 월별 급식 페이지
# ---------------------------------------

BASE_URL = "https://school.koreacharts.com/school/meals/B000012576"

# 현재 시점인 2026년 9월까지 분석
months = range(1, 10)

all_menu_text = []

progress = st.progress(0)
status = st.empty()

for i, month in enumerate(months):

    url = f"{BASE_URL}/2026{month:02d}.html"

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=15
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # 페이지의 모든 텍스트 가져오기
        text = soup.get_text("\n")

        lines = [
            line.strip()
            for line in text.split("\n")
            if line.strip()
        ]

        for line in lines:
            all_menu_text.append(line)

    except Exception:
        pass

    progress.progress((i + 1) / len(months))

progress.empty()
status.empty()

# ---------------------------------------
# 국 종류 추출
# ---------------------------------------

soup_counter = Counter()

# 국으로 분류할 끝말
patterns = [
    r"[가-힣]+국",
    r"[가-힣]+찌개",
    r"[가-힣]+탕",
    r"[가-힣]+전골"
]

# 잘못 국으로 잡힐 수 있는 단어
exclude_words = [
    "국수",
    "국밥",
    "국물",
    "전골볶음"
]

for text in all_menu_text:

    # 알레르기 번호 제거
    text = re.sub(
        r"\([^)]*\)",
        "",
        text
    )

    # 숫자 제거
    text = re.sub(
        r"\d+",
        "",
        text
    )

    # 특수문자 제거
    text = text.replace(
        "ㆍ",
        " "
    )

    # 문장 안에서 국/찌개/탕/전골 찾기
    for pattern in patterns:

        matches = re.findall(
            pattern,
            text
        )

        for food in matches:

            food = food.strip()

            if not food:
                continue

            if any(
                word in food
                for word in exclude_words
            ):
                continue

            soup_counter[food] += 1

# ---------------------------------------
# 결과
# ---------------------------------------

if len(soup_counter) == 0:

    st.error(
        "급식 데이터를 가져오지 못했습니다."
    )

    st.write(
        "인터넷 연결 또는 급식 사이트의 페이지 구조를 확인해주세요."
    )

    st.stop()

# 데이터프레임 생성
result = pd.DataFrame(
    soup_counter.most_common(10),
    columns=[
        "국 종류",
        "등장 횟수"
    ]
)

# ---------------------------------------
# 분석 결과
# ---------------------------------------

st.success(
    f"총 {sum(soup_counter.values())}개의 "
    "국·찌개·탕·전골 메뉴를 찾았습니다."
)

st.subheader("🥣 송탄고에서 자주 나오는 국 TOP 10")

st.dataframe(
    result,
    use_container_width=True,
    hide_index=True
)

# ---------------------------------------
# 그래프
# ---------------------------------------

st.subheader("📊 국 종류별 등장 횟수")

chart_data = result.set_index(
    "국 종류"
)

st.bar_chart(
    chart_data
)

# ---------------------------------------
# 가장 많이 나온 국
# ---------------------------------------

top_soup = result.iloc[0]["국 종류"]
top_count = result.iloc[0]["등장 횟수"]

st.info(
    f"💡 분석 결과, 송탄고등학교 급식에서 "
    f"가장 자주 등장한 국 종류는 **{top_soup}**이며 "
    f"총 **{top_count}회** 등장했습니다."
)

st.caption(
    "※ 2026년 1월부터 9월까지 확인 가능한 송탄고등학교 "
    "급식 메뉴를 대상으로 분석했습니다."
)
