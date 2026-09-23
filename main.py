import streamlit as st
import requests
import pandas as pd
import re
from datetime import date, timedelta
from collections import Counter

st.set_page_config(
    page_title="학교 급식 찾아보기",
    page_icon="🍲",
    layout="wide"
)

st.title("🍲 학교 급식 찾아보기")
st.subheader("송탄고등학교에서 자주 나오는 국 종류는 무엇일까?")

st.write(
    "송탄고등학교의 중식 급식 데이터를 분석하여 "
    "자주 나오는 국, 찌개, 탕 종류를 알아봅니다."
)

# ==================================================
# 송탄고등학교 정보
# ==================================================

SCHOOL_NAME = "송탄고등학교"
ATPT_OFCDC_SC_CODE = "J10"
SD_SCHUL_CODE = "7530480"

MEAL_API = "https://open.neis.go.kr/hub/mealServiceDietInfo"

# ==================================================
# 분석 기간
# ==================================================

st.markdown("### 📅 분석 기간")

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "시작 날짜",
        value=date(2026, 1, 1)
    )

with col2:
    end_date = st.date_input(
        "끝 날짜",
        value=date.today()
    )

if start_date > end_date:
    st.error("시작 날짜가 끝 날짜보다 늦습니다.")
    st.stop()

# ==================================================
# 하루 단위로 급식 데이터 가져오기
# ==================================================

@st.cache_data
def get_meal_data(start_date, end_date):

    current_date = start_date
    all_rows = []

    total_days = (end_date - start_date).days + 1

    while current_date <= end_date:

        date_string = current_date.strftime("%Y%m%d")

        params = {
            "KEY": "sample key",
            "Type": "json",
            "ATPT_OFCDC_SC_CODE": ATPT_OFCDC_SC_CODE,
            "SD_SCHUL_CODE": SD_SCHUL_CODE,
            "MMEAL_SC_CODE": "2",
            "MLSV_FROM_YMD": date_string,
            "MLSV_TO_YMD": date_string,
            "pSize": "5",
            "pIndex": "1"
        }

        try:
            response = requests.get(
                MEAL_API,
                params=params,
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            # 급식이 없는 날
            if "RESULT" in data:

                result = data["RESULT"]

                if isinstance(result, dict):
                    code = result.get("CODE", "")

                    if code == "INFO-200":
                        current_date += timedelta(days=1)
                        continue

            # 급식 데이터가 있는 날
            if "mealServiceDietInfo" in data:

                rows = data["mealServiceDietInfo"][1]["row"]

                if rows:
                    all_rows.extend(rows)

        except Exception:
            pass

        current_date += timedelta(days=1)

    return all_rows


# ==================================================
# 데이터 불러오기
# ==================================================

with st.spinner(
    "송탄고등학교 급식 데이터를 불러오는 중입니다..."
):

    meal_rows = get_meal_data(
        start_date,
        end_date
    )

if not meal_rows:

    st.warning(
        "선택한 기간에 송탄고등학교의 "
        "중식 데이터를 찾지 못했습니다."
    )

    st.stop()

st.success(
    f"총 {len(meal_rows)}일의 중식 데이터를 확인했습니다."
)

# ==================================================
# 국 종류 추출
# ==================================================

soup_counter = Counter()

# 국으로 판단할 끝부분
soup_endings = [
    "국",
    "찌개",
    "탕",
    "전골"
]

# 잘못 잡힐 수 있는 메뉴
exclude_words = [
    "국수",
    "국밥",
    "국물"
]

for row in meal_rows:

    menu = row.get("DDISH_NM", "")

    if not menu:
        continue

    # <br/> 기준으로 메뉴 분리
    menu_items = re.split(
        r"<br\s*/?>",
        menu
    )

    for item in menu_items:

        # 알레르기 번호 제거
        item = re.sub(
            r"\([^)]*\)",
            "",
            item
        )

        # 앞뒤 공백 제거
        item = item.strip()

        if not item:
            continue

        # 특수문자 제거
        cleaned = re.sub(
            r"[^가-힣]",
            "",
            item
        )

        if not cleaned:
            continue

        # 제외 메뉴
        if any(
            word in cleaned
            for word in exclude_words
        ):
            continue

        # 국 / 찌개 / 탕 / 전골 판별
        if any(
            cleaned.endswith(ending)
            for ending in soup_endings
        ):

            soup_counter[cleaned] += 1


# ==================================================
# 결과가 없는 경우
# ==================================================

if not soup_counter:

    st.warning(
        "선택한 기간에서 국 종류를 찾지 못했습니다."
    )

    st.stop()

# ==================================================
# 데이터프레임
# ==================================================

result = pd.DataFrame(
    soup_counter.most_common(),
    columns=[
        "국 종류",
        "등장 횟수"
    ]
)

# ==================================================
# TOP 10
# ==================================================

st.markdown("### 🥣 자주 나오는 국 TOP 10")

top10 = result.head(10)

st.dataframe(
    top10,
    use_container_width=True,
    hide_index=True
)

# ==================================================
# 그래프
# ==================================================

st.markdown("### 📊 국 종류별 등장 횟수")

chart_data = top10.set_index(
    "국 종류"
)

st.bar_chart(
    chart_data
)

# ==================================================
# 가장 많이 나온 국
# ==================================================

top_soup = result.iloc[0]["국 종류"]
top_count = result.iloc[0]["등장 횟수"]

st.info(
    f"💡 선택한 기간 동안 송탄고등학교에서 "
    f"가장 자주 나온 국 종류는 **{top_soup}**이며 "
    f"총 **{top_count}회** 등장했습니다."
)

# ==================================================
# 전체 결과
# ==================================================

with st.expander("전체 국 종류 확인하기"):

    st.dataframe(
        result,
        use_container_width=True,
        hide_index=True
    )
