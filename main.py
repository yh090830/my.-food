import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import quote

# ---------------------------------------
# 기본 설정
# ---------------------------------------

st.set_page_config(
    page_title="학교 급식 찾아보기",
    page_icon="🍚",
    layout="wide"
)

st.title("🍚 학교 급식 찾아보기")
st.write("학교 이름과 날짜를 선택하면 해당 학교의 중식 메뉴를 확인할 수 있습니다.")

API_KEY = "sample key"

SCHOOL_API = "https://open.neis.go.kr/hub/schoolInfo"
MEAL_API = "https://open.neis.go.kr/hub/mealServiceDietInfo"


# ---------------------------------------
# 학교 이름 변환
# ---------------------------------------

def expand_school_name(name):
    """
    줄임말을 정식 학교명 검색어로 바꿉니다.

    예:
    수도여고 → 수도여자고등학교
    서울고 → 서울고등학교
    """

    name = name.strip()

    # 여고 → 여자고등학교
    if name.endswith("여고"):
        name = name[:-2] + "여자고등학교"

    # 남고 → 남자고등학교
    elif name.endswith("남고"):
        name = name[:-2] + "남자고등학교"

    # 일반적인 '고' → '고등학교'
    elif name.endswith("고"):
        name = name[:-1] + "고등학교"

    return name


# ---------------------------------------
# 학교 검색
# ---------------------------------------

def search_schools(school_name):
    params = {
        "KEY": API_KEY,
        "Type": "json",
        "SCHUL_NM": school_name
    }

    try:
        response = requests.get(
            SCHOOL_API,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

    except Exception:
        return None, "API_ERROR"

    # 데이터 없음
    if "RESULT" in data:
        result = data["RESULT"]

        if isinstance(result, dict):
            code = result.get("CODE", "")

            if code == "INFO-200":
                return [], "NO_DATA"

    try:
        rows = data["schoolInfo"][1]["row"]
    except (KeyError, IndexError, TypeError):
        return [], "NO_DATA"

    return rows, "OK"


# ---------------------------------------
# 급식 조회
# ---------------------------------------

def get_meal(school, selected_date):

    date_string = selected_date.strftime("%Y%m%d")

    params = {
        "KEY": API_KEY,
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": school["ATPT_OFCDC_SC_CODE"],
        "SD_SCHUL_CODE": school["SD_SCHUL_CODE"],
        "MMEAL_SC_CODE": "2",
        "MLSV_FROM_YMD": date_string,
        "MLSV_TO_YMD": date_string,
        "pSize": "1000",
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

    except Exception:
        return None, "API_ERROR"

    # 데이터 없음
    if "RESULT" in data:
        result = data["RESULT"]

        if isinstance(result, dict):
            code = result.get("CODE", "")

            if code == "INFO-200":
                return [], "NO_DATA"

    try:
        rows = data["mealServiceDietInfo"][1]["row"]
    except (KeyError, IndexError, TypeError):
        return [], "NO_DATA"

    return rows, "OK"


# ---------------------------------------
# 학교 검색 UI
# ---------------------------------------

school_name = st.text_input(
    "학교 이름을 입력하세요",
    placeholder="예: 송탄고, 수도여고"
)

schools = []
search_message = ""

if school_name:

    # 1차 검색
    schools, status = search_schools(school_name)

    # 1차 검색 결과가 없으면 줄임말 변환 후 재검색
    if status == "NO_DATA" or not schools:

        expanded_name = expand_school_name(school_name)

        # 실제로 검색어가 바뀐 경우에만 재검색
        if expanded_name != school_name:

            schools, status = search_schools(
                expanded_name
            )

            if status == "OK" and schools:
                search_message = (
                    f"'{school_name}'을(를) "
                    f"'{expanded_name}'로 바꾸어 검색했습니다."
                )

    # 검색 결과
    if schools:

        if search_message:
            st.info(search_message)

        st.success(
            f"검색 결과 {len(schools)}개의 학교를 찾았습니다."
        )

        # 학교 선택용 목록
        school_options = []

        for school in schools:

            school_text = (
                f"{school['SCHUL_NM']} "
                f"({school['LCTN_SC_NM']})"
            )

            school_options.append(school_text)

        selected_index = st.selectbox(
            "학교를 선택하세요",
            range(len(school_options)),
            format_func=lambda x: school_options[x]
        )

        selected_school = schools[selected_index]

        # 선택한 학교 정보
        st.info(
            f"선택한 학교: **{selected_school['SCHUL_NM']}**  \n"
            f"지역: **{selected_school['LCTN_SC_NM']}**"
        )

        # ---------------------------------------
        # 날짜 선택
        # ---------------------------------------

        today_korea = datetime.now(
            ZoneInfo("Asia/Seoul")
        ).date()

        selected_date = st.date_input(
            "급식 날짜를 선택하세요",
            value=today_korea
        )

        # ---------------------------------------
        # 급식 조회
        # ---------------------------------------

        meal_rows, meal_status = get_meal(
            selected_school,
            selected_date
        )

        if meal_status == "API_ERROR":

            st.error(
                "급식 정보를 불러오는 중 문제가 발생했습니다. "
                "잠시 후 다시 시도해주세요."
            )

        elif meal_status == "NO_DATA" or not meal_rows:

            formatted_date = selected_date.strftime(
                "%Y년 %m월 %d일"
            )

            st.warning(
                f"**{formatted_date}**에는 "
                f"이 학교의 중식 급식 정보가 없습니다."
            )

        else:

            # 보통 해당 날짜에는 한 행이지만
            # 여러 행이 있을 경우 모두 처리
            for meal in meal_rows:

                st.subheader(
                    f"🍽️ {selected_date.strftime('%Y년 %m월 %d일')} 중식"
                )

                # 메뉴 원문
                menu = meal.get(
                    "DDISH_NM",
                    ""
                )

                # <br/>을 줄바꿈으로 변경
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

                # 메뉴 표시
                st.markdown("### 🍚 오늘의 메뉴")

                st.text(
                    menu
                )

                # 칼로리 표시
                st.markdown("### 🔥 칼로리")

                st.write(
                    calories
                )

                st.caption(
                    "※ 메뉴에 표시된 괄호 안 숫자는 "
                    "알레르기 유발 식재료 번호입니다."
                )


    elif status == "API_ERROR":

        st.error(
            "학교 정보를 불러오는 중 문제가 발생했습니다. "
            "잠시 후 다시 시도해주세요."
        )

    else:

        st.warning(
            f"'{school_name}'에 해당하는 학교를 찾지 못했습니다. "
            "학교 이름을 다시 확인해주세요."
        )

else:

    st.info(
        "학교 이름을 입력하면 검색 결과에서 학교를 선택할 수 있습니다."
    )
