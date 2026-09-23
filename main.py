import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="학교 급식 찾아보기",
    page_icon="🍚",
    layout="wide"
)

st.title("🍚 학교 급식 찾아보기")
st.write("송탄고등학교의 날짜별 중식 메뉴를 확인해 보세요.")

# 송탄고등학교 정보
SCHOOL_NAME = "송탄고등학교"
ATPT_OFCDC_SC_CODE = "J10"
SD_SCHUL_CODE = "7530480"

MEAL_API = "https://open.neis.go.kr/hub/mealServiceDietInfo"


def get_meal(selected_date):
    date_string = selected_date.strftime("%Y%m%d")

    params = {
        "KEY": "sample key",
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": ATPT_OFCDC_SC_CODE,
        "SD_SCHUL_CODE": SD_SCHUL_CODE,
        "MMEAL_SC_CODE": "2",
        "MLSV_FROM_YMD": date_string,
        "MLSV_TO_YMD": date_string
    }

    try:
        response = requests.get(
            MEAL_API,
            params=params,
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

    except Exception as e:
        return None, "API_ERROR"

    # 조회 결과가 없는 경우
    if "RESULT" in data:
        result = data["RESULT"]

        if isinstance(result, dict):
            code = result.get("CODE", "")

            if code == "INFO-200":
                return [], "NO_DATA"

            return None, "API_ERROR"

    # 급식 데이터 확인
    try:
        rows = data["mealServiceDietInfo"][1]["row"]
        return rows, "OK"

    except (KeyError, IndexError, TypeError):
        return [], "NO_DATA"


# 학교 정보 표시
st.info(
    f"🏫 **{SCHOOL_NAME}**\n\n"
    f"교육청 코드: `{ATPT_OFCDC_SC_CODE}`  \n"
    f"학교 코드: `{SD_SCHUL_CODE}`"
)

# 한국 시간 기준 오늘
today_korea = datetime.now(
    ZoneInfo("Asia/Seoul")
).date()

# 날짜 선택
selected_date = st.date_input(
    "📅 날짜를 선택하세요",
    value=today_korea
)

# 급식 조회
meal_rows, status = get_meal(selected_date)

date_text = selected_date.strftime(
    "%Y년 %m월 %d일"
)

if status == "API_ERROR":

    st.error(
        "급식 정보를 불러오지 못했습니다. "
        "잠시 후 다시 시도해 주세요."
    )

elif status == "NO_DATA" or not meal_rows:

    st.warning(
        f"📢 **{date_text}**에는 "
        f"{SCHOOL_NAME}의 중식 급식 정보가 없습니다."
    )

else:

    st.subheader(
        f"🍽️ {date_text} 중식"
    )

    for meal in meal_rows:

        # 메뉴 원문
        menu = meal.get(
            "DDISH_NM",
            ""
        )

        # NEIS의 <br/>을 줄바꿈으로 변경
        menu = menu.replace(
            "<br/>",
            "\n"
        )

        menu = menu.replace(
            "<br>",
            "\n"
        )

        # 칼로리
        calories = meal.get(
            "CAL_INFO",
            "-"
        )

        st.markdown("### 🍚 오늘의 메뉴")

        st.text(menu)

        st.markdown("### 🔥 칼로리")

        st.write(calories)

        st.caption(
            "※ 메뉴 뒤 괄호 안 숫자는 "
            "알레르기 유발 식재료 번호입니다."
        )
