
from pathlib import Path
import pandas as pd
import streamlit as st

# app.py와 universities.csv는 같은 폴더에 있어야 합니다.
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "universities.csv"

st.set_page_config(
    page_title="지역별 전문대학 찾기",
    page_icon="🎓",
    layout="centered"
)

st.markdown("""
<style>
    .main {background-color: #fbfaff;}
    .block-container {max-width: 850px; padding-top: 2.5rem;}
    .hero {
        padding: 28px 24px;
        border-radius: 20px;
        background: linear-gradient(120deg, #f4eaff, #fff0f5);
        margin-bottom: 22px;
    }
    .school-card {
        border: 1px solid #eee6f5;
        border-radius: 16px;
        padding: 18px 20px;
        margin: 12px 0;
        background: white;
    }
    .school-name {
        font-size: 1.2rem;
        font-weight: 700;
        color: #38294b;
    }
    .school-info {
        color: #666;
        font-size: 0.92rem;
        line-height: 1.7;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>🎓 지역별 전문대학 찾기</h1>
    <p>궁금한 지역을 입력하면 해당 지역의 전문대학을 최대 2곳 보여드립니다.</p>
</div>
""", unsafe_allow_html=True)


@st.cache_data
def load_universities():

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            "universities.csv 파일을 찾을 수 없습니다. "
            "app.py와 같은 폴더에 올려주세요."
        )

    # GitHub HTML 페이지를 CSV로 잘못 읽는 문제 방지
    raw_start = DATA_FILE.read_bytes()[:500].lstrip().lower()

    if raw_start.startswith(b"<!doctype html") or raw_start.startswith(b"<html"):
        raise ValueError(
            "CSV가 아니라 GitHub 웹페이지 HTML이 들어 있습니다. "
            "원본 CSV 파일을 다운로드해서 다시 업로드해 주세요."
        )

    data = None
    last_error = None

    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            data = pd.read_csv(DATA_FILE, encoding=encoding)
            break
        except UnicodeDecodeError as exc:
            last_error = exc

    if data is None:
        raise ValueError(
            f"CSV 문자 인코딩을 읽지 못했습니다: {last_error}"
        )

    data.columns = [str(col).strip() for col in data.columns]

    required = ["대학명", "지역", "주소", "홈페이지"]

    missing = [
        col for col in required
        if col not in data.columns
    ]

    if missing:
        raise ValueError(
            f"필수 열을 찾을 수 없습니다: {', '.join(missing)}. "
            f"현재 열 이름: {list(data.columns)}"
        )

    for col in required:
        data[col] = (
            data[col]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    data = data[data["대학명"] != ""].copy()

    data["지역_검색용"] = (
        data["지역"].str.replace(" ", "", regex=False)
    )

    return data


def normalize_region(value: str) -> str:

    value = value.strip().replace(" ", "")

    aliases = {
        "서울특별시": "서울",
        "서울시": "서울",
        "경기도": "경기",
        "강원도": "강원",
        "강원특별자치도": "강원",
        "충청북도": "충북",
        "충청남도": "충남",
        "전라북도": "전북",
        "전북특별자치도": "전북",
        "전라남도": "전남",
        "경상북도": "경북",
        "경상남도": "경남",
        "부산광역시": "부산",
        "대구광역시": "대구",
        "인천광역시": "인천",
        "광주광역시": "광주",
        "대전광역시": "대전",
        "울산광역시": "울산",
        "세종특별자치시": "세종",
        "제주특별자치도": "제주",
        "제주도": "제주"
    }

    return aliases.get(value, value)


# 데이터 불러오기
try:
    universities = load_universities()

except Exception as error:

    st.error(f"데이터를 불러오지 못했습니다: {error}")

    st.info(
        "깃허브 저장소 최상위에 app.py, "
        "universities.csv, requirements.txt가 "
        "나란히 있는지 확인해 주세요."
    )

    st.stop()


# 지역 입력창
st.subheader("어느 지역의 대학을 찾으시나요?")

region_input = st.text_input(
    "지역 입력",
    placeholder="예: 서울, 경기, 부산, 강원",
    help="시·도 이름을 입력해 주세요."
)

search_clicked = st.button(
    "대학 찾기",
    type="primary",
    use_container_width=True
)


# 검색 기능
if search_clicked:

    if not region_input.strip():

        st.warning("지역을 먼저 입력해 주세요.")

    else:

        selected_region = normalize_region(region_input)

        results = universities[
            universities["지역_검색용"] == selected_region
        ].head(2)

        if results.empty:

            available = sorted(
                universities["지역"].dropna().unique().tolist()
            )

            st.warning(
                f"'{region_input}' 지역의 대학을 찾지 못했습니다."
            )

            st.caption(
                "검색 가능한 지역: " + " · ".join(available)
            )

        else:

            st.success(
                f"{selected_region} 지역의 전문대학 검색 결과"
            )

            st.caption(
                f"검색 결과 {len(results)}곳 (최대 2곳 표시)"
            )

            for _, school in results.iterrows():

                name = school["대학명"]
                address = school["주소"] or "주소 정보 없음"
                website = school["홈페이지"]

                st.markdown(
                    '<div class="school-card">',
                    unsafe_allow_html=True
                )

                st.markdown(
                    f'<div class="school-name">🎓 {name}</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    f'<div class="school-info">📍 {address}</div>',
                    unsafe_allow_html=True
                )

                if website:

                    safe_url = website

                    if not website.startswith(
                        ("http://", "https://")
                    ):
                        safe_url = "https://" + website

                    st.markdown(
                        f"🌐 [학교 홈페이지 바로가기]({safe_url})"
                    )

                else:

                    st.markdown("🌐 홈페이지 정보 없음")

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True
                )

else:

    st.caption(
        "지역을 입력하고 '대학 찾기'를 누르면 "
        "해당 지역의 대학 최대 2곳이 표시됩니다."
    )


st.divider()

st.caption(
    "자료 출처: 한국전문대학교육협의회 "
    "「대학 정보」 CSV (2020-10-07). "
    "자료에 수록된 지역·학교 정보 기준으로 검색합니다."
)




    
       
                   
