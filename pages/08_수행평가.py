
import streamlit as st
import pandas as pd
from pathlib import Path

# =========================
# 1. 페이지 설정
# =========================
st.set_page_config(
    page_title="전국 대학교 검색",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 전국 대학교 검색 사이트")
st.write("지역을 검색하면 해당 지역의 대학교 2곳을 보여줍니다.")

# =========================
# 2. CSV 데이터 불러오기
# =========================
@st.cache_data
def load_data():

    file_path = Path(__file__).parent / "universities.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            "universities.csv 파일이 없습니다. "
            "app.py와 같은 폴더에 업로드해 주세요."
        )

    # 여러 인코딩 자동 시도
    encodings = ["utf-8-sig", "utf-8", "cp949"]

    df = None
    last_error = None

    for encoding in encodings:
        try:
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                sep=None,
                engine="python"
            )
            break
        except Exception as e:
            last_error = e

    if df is None:
        raise ValueError(f"CSV 읽기 실패: {last_error}")

    # 컬럼명 자동 정리
    df.columns = (
        df.columns
        .astype(str)
        .str.replace("\ufeff", "", regex=False)
        .str.strip()
    )

    # 컬럼명 공백 제거
    df.columns = df.columns.str.replace(
        " ", "", regex=False
    )

    # 필수 컬럼 확인
    required = [
        "학교명",
        "대학구분명",
        "설립형태구분명",
        "시도명"
    ]

    missing = [
        col for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"필수 컬럼이 없습니다: {missing}\n"
            f"현재 CSV 컬럼: {list(df.columns)}"
        )

    return df


try:
    df = load_data()

    st.success(
        f"데이터 불러오기 성공! 총 {len(df):,}개 데이터"
    )

except Exception as e:
    st.error(f"데이터를 불러오지 못했습니다: {e}")
    st.stop()


# =========================
# 3. 데이터 전처리
# =========================
df["학교명"] = df["학교명"].fillna("").astype(str).str.strip()
df["시도명"] = df["시도명"].fillna("").astype(str).str.strip()

# 대학 및 전문대학만 추출
university_df = df[
    df["대학구분명"].isin(["대학", "전문대학"])
].copy()

# 학교명 없는 데이터 제거
university_df = university_df[
    university_df["학교명"] != ""
]

# 같은 학교 중복 제거
university_df = university_df.drop_duplicates(
    subset=["학교명"],
    keep="first"
).reset_index(drop=True)


# =========================
# 4. 데이터 현황
# =========================
st.divider()
st.subheader("📊 대학 데이터 현황")

col1, col2, col3 = st.columns(3)

col1.metric("전체 데이터", f"{len(df):,}개")
col2.metric("대학 데이터", f"{len(university_df):,}개")
col3.metric("지역 수", f"{university_df['시도명'].nunique()}개")


# =========================
# 5. 지역별 대학 검색
# =========================
st.divider()
st.subheader("🔍 지역별 대학교 검색")

search_region = st.text_input(
    "검색할 지역을 입력하세요",
    placeholder="예: 서울, 경기, 부산, 대전"
).strip()

if search_region:

    # 지역명 검색
    result = university_df[
        university_df["시도명"].str.contains(
            search_region,
            na=False,
            case=False,
            regex=False
        )
    ].copy()

    if not result.empty:

        st.success(
            f"{search_region} 검색 결과: "
            f"{len(result)}개 대학"
        )

        # 지역 검색 결과 중 상위 2개
        top_two = result.head(2)

        st.subheader("🏫 해당 지역 대학교 TOP 2")

        cols = st.columns(2)

        for i, (_, row) in enumerate(top_two.iterrows()):

            with cols[i]:

                with st.container(border=True):

                    st.markdown(
                        f"### 🎓 {row['학교명']}"
                    )

                    st.write(
                        f"**지역:** {row['시도명']}"
                    )

                    st.write(
                        f"**대학 구분:** {row['대학구분명']}"
                    )

                    st.write(
                        f"**설립 형태:** "
                        f"{row['설립형태구분명']}"
                    )

                    # 주소
                    address = row.get(
                        "소재지도로명주소", ""
                    )

                    if pd.notna(address) and str(address).strip():
                        st.write(f"**주소:** {address}")

                    # 전화번호
                    phone = row.get(
                        "대표전화번호", ""
                    )

                    if pd.notna(phone) and str(phone).strip():
                        st.write(f"**전화번호:** {phone}")

                    # 홈페이지
                    website = row.get(
                        "홈페이지주소", ""
                    )

                    if pd.notna(website) and str(website).strip():

                        website = str(website).strip()

                        if not website.startswith(
                            ("http://", "https://")
                        ):
                            website = "https://" + website

                        st.link_button(
                            "🌐 홈페이지 방문",
                            website,
                            use_container_width=True
                        )

        if len(top_two) < 2:
            st.warning("검색된 대학교가 2곳보다 적습니다.")

        # 전체 검색 결과
        with st.expander("📚 전체 검색 결과 보기"):

            st.dataframe(
                result,
                use_container_width=True,
                hide_index=True
            )

    else:
        st.warning(
            f"'{search_region}'에 해당하는 대학교가 없습니다."
        )

else:
    st.info("지역을 입력하면 해당 지역 대학교 2곳이 표시됩니다.")


# =========================
# 6. 지역별 대학 분포
# =========================
st.divider()
st.subheader("📈 지역별 대학교 분포")

region_count = university_df["시도명"].value_counts()

st.bar_chart(region_count)

# =========================
# 7. 설립 형태별 분석
# =========================
st.divider()
st.subheader("🏛️ 설립 형태별 대학 분석")

establishment_count = (
    university_df["설립형태구분명"].value_counts()
)

st.bar_chart(establishment_count)

# =========================
# 8. 전체 데이터
# =========================
st.divider()

with st.expander("전체 대학 데이터 확인"):

    st.dataframe(
        university_df,
        use_container_width=True,
        hide_index=True
    )

st.caption("데이터 출처: universities.csv")



            
                            
