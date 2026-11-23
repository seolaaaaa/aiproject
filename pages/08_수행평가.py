
import streamlit as st
import pandas as pd
from pathlib import Path
import re

st.set_page_config(
    page_title="지역별 대학 검색",
    page_icon="🎓",
    layout="wide"
)

st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    max-width: 1100px;
}
.hero {
    background: linear-gradient(120deg, #eaf2ff, #f7f9ff);
    padding: 28px;
    border-radius: 18px;
    text-align: center;
    border: 1px solid #dce7f8;
    margin-bottom: 24px;
}
.hero h1 {
    color: #203864;
    margin: 0;
    font-size: 32px;
}
.hero p {
    color: #53657f;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)


# 지역명 정리 함수
def normalize_text(value):
    return re.sub(
        r"[^가-힣a-zA-Z0-9]",
        "",
        str(value)
    ).lower()


# CSV 파일 위치
DATA_PATH = Path(__file__).resolve().parent / "universities.csv"


# 대학 자료 불러오기
@st.cache_data
def load_universities(path):

    data = None

    for encoding in ["utf-8-sig", "cp949", "euc-kr"]:
        try:
            data = pd.read_csv(
                path,
                encoding=encoding,
                dtype=str
            )
            break
        except UnicodeDecodeError:
            continue

    if data is None:
        raise ValueError("CSV 인코딩을 확인해주세요.")

    data.columns = [
        str(col).replace("\ufeff", "").strip()
        for col in data.columns
    ]

    data = data.fillna("")

    required = ["대학명", "지역", "주소"]

    missing = [
        col for col in required
        if col not in data.columns
    ]

    if missing:
        raise ValueError(
            f"필요한 열이 없습니다: {missing}"
        )

    for col in [
        "영문명", "홈페이지", "전화",
        "팩스", "대표메일"
    ]:
        if col not in data.columns:
            data[col] = ""

    data["_지역검색"] = data["지역"].map(normalize_text)
    data["_주소검색"] = data["주소"].map(normalize_text)

    return data


# 지역명 별칭
REGION_ALIASES = {
    "서울특별시": "서울",
    "서울시": "서울",
    "부산광역시": "부산",
    "부산시": "부산",
    "대구광역시": "대구",
    "대구시": "대구",
    "인천광역시": "인천",
    "인천시": "인천",
    "광주광역시": "광주",
    "광주시": "광주",
    "대전광역시": "대전",
    "대전시": "대전",
    "울산광역시": "울산",
    "울산시": "울산",
    "세종특별자치시": "세종",
    "세종시": "세종",
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
    "제주특별자치도": "제주",
    "제주도": "제주"
}


# 제목
st.markdown("""
<div class="hero">
    <h1>🎓 지역별 대학 검색</h1>
    <p>원하는 지역을 검색하고 해당 지역의 대학 정보를 확인하세요.</p>
</div>
""", unsafe_allow_html=True)


# 데이터 확인
if not DATA_PATH.exists():
    st.error("universities.csv 파일이 없습니다.")
    st.info(
        "GitHub에서 app.py와 universities.csv를 "
        "같은 폴더에 업로드해주세요."
    )
    st.stop()

try:
    df = load_universities(DATA_PATH)

except Exception as error:
    st.error(f"데이터 오류: {error}")
    st.stop()


# 검색창
st.subheader("🔎 지역 검색")

with st.form("search_form"):

    search_region = st.text_input(
        "검색할 지역을 입력하세요.",
        placeholder="예: 서울, 경기, 부산, 경기도"
    )

    search_button = st.form_submit_button(
        "🔍 대학 검색",
        use_container_width=True
    )


# 검색 기능
if search_button:

    keyword = search_region.strip()

    if not keyword:

        st.session_state["search_done"] = False
        st.warning("지역을 입력해주세요.")

    else:

        region = REGION_ALIASES.get(
            keyword,
            keyword
        )

        normalized_region = normalize_text(region)
        normalized_keyword = normalize_text(keyword)

        # 지역 열 검색
        region_match = (
            df["_지역검색"] == normalized_region
        )

        # 주소 열 검색
        address_match = (
            df["_주소검색"].str.contains(
                normalized_region,
                regex=False,
                na=False
            )
        ) | (
            df["_주소검색"].str.contains(
                normalized_keyword,
                regex=False,
                na=False
            )
        )

        # 두 검색 결과 합치기
        results = df[
            region_match | address_match
        ].copy()

        results = results.drop_duplicates(
            subset=["대학명", "주소"]
        )

        st.session_state["search_done"] = True
        st.session_state["searched_region"] = keyword
        st.session_state["results"] = results.to_dict("records")


# 검색 결과 창
st.divider()
st.subheader("📋 검색 결과")

if not st.session_state.get("search_done", False):

    st.info("지역을 입력하면 대학 목록이 표시됩니다.")

else:

    results = pd.DataFrame(
        st.session_state.get("results", [])
    )

    searched = st.session_state["searched_region"]

    if results.empty:

        st.warning(
            f"'{searched}' 지역의 대학을 찾지 못했습니다."
        )

    else:

        st.success(
            f"'{searched}' 검색 결과: "
            f"총 {len(results)}개 대학"
        )

        # 대학별 카드 출력
        for _, row in results.iterrows():

            with st.container(border=True):

                st.markdown(
                    f"### 🎓 {row['대학명']}"
                )

                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**지역:** {row['지역']}")
                    st.write(f"**주소:** {row['주소']}")
                    st.write(f"**전화:** {row['전화']}")

                with col2:
                    st.write(f"**영문명:** {row['영문명']}")
                    st.write(f"**팩스:** {row['팩스']}")
                    st.write(f"**대표메일:** {row['대표메일']}")

                website = str(row["홈페이지"]).strip()

                if website:

                    if not website.startswith(
                        ("http://", "https://")
                    ):
                        website = "https://" + website

                    st.link_button(
                        "🌐 대학 홈페이지 바로가기",
                        website
                    )

        # CSV 다운로드
        download_data = results.drop(
            columns=[
                "_지역검색",
                "_주소검색"
            ],
            errors="ignore"
        )

        st.download_button(
            "📥 검색 결과 다운로드",
            data=download_data.to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name=f"{searched}_대학목록.csv",
            mime="text/csv",
            use_container_width=True
        )


# 자료 안내
with st.expander("📌 자료 안내"):

    st.write(
        "한국전문대학교육협의회 대학 정보 "
        "(2020년 10월 7일 기준)"
    )

    st.write(
        "이 데이터는 전문대학 자료입니다. "
        "일반 4년제 대학은 별도의 데이터가 필요합니다."
    )

st.caption(
    "자료 출처: 한국전문대학교육협의회 대학 정보 CSV"
)



                
