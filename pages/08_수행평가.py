
import streamlit as st
import pandas as pd
from pathlib import Path

# =====================================
# 1. 기본 페이지 설정
# =====================================
st.set_page_config(
    page_title="지역별 전문대학 검색",
    page_icon="🎓",
    layout="wide"
)

# =====================================
# 2. 디자인 CSS
# =====================================
st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-size: 38px;
        font-weight: bold;
        color: #243B64;
        margin-bottom: 10px;
    }

    .sub-title {
        text-align: center;
        color: #777777;
        font-size: 16px;
        margin-bottom: 35px;
    }

    .result-title {
        font-size: 25px;
        font-weight: bold;
        color: #243B64;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    .university-card {
        background-color: #F5F7FB;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #E1E6EF;
        margin-bottom: 15px;
    }

    .university-name {
        font-size: 21px;
        font-weight: bold;
        color: #243B64;
        margin-bottom: 12px;
    }

    .info {
        font-size: 15px;
        color: #444444;
        line-height: 1.9;
    }
</style>
""", unsafe_allow_html=True)


# =====================================
# 3. 대학 데이터 불러오기
# =====================================
@st.cache_data
def load_data():

    file_path = Path(__file__).parent / "universities.csv"

    data = pd.read_csv(
        file_path,
        encoding="utf-8-sig",
        dtype=str
    )

    data = data.fillna("")

    return data


try:
    df = load_data()

except FileNotFoundError:
    st.error("universities.csv 파일을 찾을 수 없습니다.")
    st.stop()


# =====================================
# 4. 지역명 변환
# =====================================
region_alias = {
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


# =====================================
# 5. 사이트 제목
# =====================================
st.markdown(
    '<div class="main-title">🎓 지역별 전문대학 검색</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    '원하는 지역을 검색하고 해당 지역의 전문대학 정보를 확인하세요.'
    '</div>',
    unsafe_allow_html=True
)


# =====================================
# 6. 검색창
# =====================================
st.markdown("### 🔎 지역 검색")

with st.form("search_form"):

    search_region = st.text_input(
        "검색할 지역을 입력하세요.",
        placeholder="예: 서울, 경기, 부산, 경기도"
    )

    search_button = st.form_submit_button(
        "🔍 대학 검색",
        use_container_width=True
    )


# =====================================
# 7. 검색 기능
# =====================================
if search_button:

    keyword = search_region.strip().replace(" ", "")

    if keyword == "":
        st.session_state["results"] = None
        st.warning("검색할 지역을 입력해주세요.")

    else:

        # 정식 지역명을 데이터의 지역명으로 변환
        region = region_alias.get(keyword, keyword)

        # 대학 데이터에서 해당 지역 검색
        results = df[
            df["지역"].str.strip() == region
        ]

        if len(results) > 0:

            st.session_state["results"] = results.to_dict("records")
            st.session_state["searched_region"] = region

        else:

            st.session_state["results"] = []
            st.session_state["searched_region"] = keyword


# =====================================
# 8. 검색 결과 출력 창
# =====================================
st.markdown(
    '<div class="result-title">📋 검색 결과</div>',
    unsafe_allow_html=True
)

if "results" not in st.session_state:

    st.info("지역을 검색하면 해당 지역의 전문대학이 표시됩니다.")

elif st.session_state["results"] is None:

    st.info("지역명을 입력한 뒤 다시 검색해주세요.")

elif len(st.session_state["results"]) == 0:

    st.warning(
        f"'{st.session_state['searched_region']}' 지역의 대학을 찾지 못했습니다."
    )

    st.write("검색 가능한 지역")

    st.write(
        ", ".join(sorted(df["지역"].unique()))
    )

else:

    results = pd.DataFrame(st.session_state["results"])

    region = st.session_state["searched_region"]

    st.success(
        f"'{region}' 지역 검색 완료! "
        f"총 {len(results)}개의 전문대학을 찾았습니다."
    )

    # 대학별 정보 카드
    for index, row in results.iterrows():

        with st.container(border=True):

            st.markdown(
                f'<div class="university-name">'
                f'🎓 {row["대학명"]}'
                f'</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                <div class="info">
                📍 <b>지역:</b> {row['지역']}<br>
                🏫 <b>주소:</b> {row['주소']}<br>
                ☎️ <b>전화번호:</b> {row['전화']}<br>
                📠 <b>팩스:</b> {row['팩스']}<br>
                ✉️ <b>대표메일:</b> {row['대표메일']}<br>
                </div>
                """,
                unsafe_allow_html=True
            )

            website = row["홈페이지"].strip()

            if website:

                if not website.startswith(("http://", "https://")):
                    website = "https://" + website

                st.link_button(
                    "🌐 대학 홈페이지 바로가기",
                    website
                )

    # 검색 결과 다운로드
    st.divider()

    csv_data = results.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="📥 검색 결과 다운로드",
        data=csv_data,
        file_name=f"{region}_전문대학_목록.csv",
        mime="text/csv",
        use_container_width=True
    )


# =====================================
# 9. 하단 안내
# =====================================
st.divider()

st.caption(
    "자료 출처: 한국전문대학교육협의회 대학 정보 (2020.10.07)"
)

st.caption(
    "※ 대학 정보는 자료 작성일 기준이며, "
    "최신 정보는 각 대학 공식 홈페이지에서 확인하세요."
)

