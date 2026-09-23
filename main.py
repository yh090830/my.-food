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
    "국·찌개·탕·전골 종류가 얼마나 자주 나오는지 알아봅니다."
)

# -----------------------------------
# 송탄고등학교 급식 월별 데이터 가져오기
# -----------------------------------

BASE_URL = "https://school.koreacharts.com/school/meals/B000012576"

all_meals = []

progress = st.progress(0)
status = st.empty()

for month in range(1, 13):

    url = f"{BASE_URL}/2026{month:02d}.html"

    try:
        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        if response.status_code != 200:
            continue

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        text = soup.get_text("\n")

        # 중식 부분의 메뉴를 가져오기 위해
        # 페이지 전체에서 급식 메뉴가 있는 부분을 분석
        lines = [
            line.strip()
            for line in text.split("\n")
            if line.strip()
        ]

        for line in lines:

            # 급식 메뉴에서 자주 사용되는 국 종류만 추출
            if any(
                keyword in line
                for keyword in [
                    "국",
                    "찌개",
                    "탕",
                    "전골"
                ]
            ):
                all_meals.append(line)

        status.text(
            f"2026년 {month}월 데이터 확인 중..."
        )

    except Exception:
        continue

    progress.progress(month / 12)

progress.empty()
status.empty()

# -----------------------------------
# 국 종류 추출
# -----------------------------------

soup_counter = Counter()

# 국으로 분류할 단어
soup_keywords = [
    "국",
    "찌개",
    "탕",
    "전골"
]

# 국으로 잘못 인식될 수 있는 단어
exclude_words = [
    "국수",
    "국밥",
    "전골볶음"
]

for text in all_meals:

    # 괄호 안 알레르기 번호 제거
    text = re.sub(
        r"\([^)]*\)",
        "",
        text
    )

    # 여러 기호 제거
    text = text.replace(
        "ㆍ",
        " "
    )

    text = text.replace(
        ",",
        " "
    )

    # 공백 기준으로 메뉴 분리
    foods = text.split()

    for food in foods:

        food = food.strip()

        if not food:
            continue

        # 잘못 분류될 수 있는 메뉴 제외
        if any(
            word in food
            for word in exclude_words
        ):
            continue

        # 국/찌개/탕/전골 포함 여부
        if any(
            keyword in food
            for keyword in soup_keywords
        ):

            # 숫자 제거
            food = re.sub(
                r"\d+",
                "",
                food
            )

            # 특수문자 제거
            food = re.sub(
                r"[^가-힣]",
                "",
                food
            )

            if food:
                soup_counter[food] += 1

# -----------------------------------
# 결과
# -----------------------------------

if not soup_counter:

    st.error(
        "급식 데이터를 가져오지 못했습니다."
    )

else:

    result = pd.DataFrame(
        soup_counter.most_common(10),
        columns=[
            "국 종류",
            "등장 횟수"
        ]
    )

    st.success(
        f"총 {sum(soup_counter.values())}개의 "
        "국·찌개·탕·전골 메뉴를 찾았습니다."
    )

    # -----------------------------------
    # TOP 10 표
    # -----------------------------------

    st.subheader("🥣 자주 나오는 국 TOP 10")

    st.dataframe(
        result,
        use_container_width=True,
        hide_index=True
    )

    # -----------------------------------
    # 막대그래프
    # -----------------------------------

    st.subheader("📊 국 종류별 등장 횟수")

    chart_data = result.set_index(
        "국 종류"
    )

    st.bar_chart(
        chart_data
    )

    # -----------------------------------
    # 가장 많이 나온 국
    # -----------------------------------

    top_soup = result.iloc[0]["국 종류"]
    top_count = result.iloc[0]["등장 횟수"]

    st.info(
        f"💡 2026년 송탄고등학교 급식에서 "
        f"가장 자주 나온 국 종류는 **{top_soup}**이며, "
        f"총 **{top_count}회** 등장했습니다."
    )

    st.caption(
        "※ 급식 메뉴의 이름에 '국', '찌개', '탕', '전골'이 "
        "포함된 메뉴를 기준으로 집계합니다."
    )
