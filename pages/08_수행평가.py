
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="전국 대학교 검색",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 전국 대학교 검색 사이트")
st.write("원하는 지역을 검색하고 해당 지역의 대학교 정보를 확인해 보세요.")

st.divider()

# -----------------------------
# 데이터 불러오기
# -----------------------------
@st.cache_data
def load_data():
    file_path = Path(__file__).parent / "universities.csv"

    if not file_path.exists():
        raise FileNotFoundError("universities.csv 파일을 찾을 수 없습니다.")

    df = pd.read_csv(file_path, encoding="utf-8-sig")

    required_columns = [
        "학교명",
        "대학구분명",
        "설립형태구분명",
        "시도명",
        "소재지도로명주소",
        "홈페이지주소",
        "대표전화번호"
    ]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"필수 컬럼이 없습니다: {col}")

    return df


try:
    df = load_data()
    st.success("대학교 데이터를 성공적으로 불러왔습니다!")

except Exception as e:
    st.error(f"데이터를 불러오지 못했습니다: {e}")
    st.stop()


# -----------------------------
# 데이터 전처리
# -----------------------------
df["시도명"] = df["시도명"].fillna("").astype(str).str.strip()
df["학교명"] = df["학교명"].fillna("").astype(str).str.strip()

# 일반 대학 및 전문대학만 추출
university_df = df[
    df["대학구분명"].isin(["대학", "전문대학"])
].copy()

# 대학을 전문대학보다 먼저 표시
university_df["정렬순서"] = university_df["대학구분명"].map({
    "대학": 0,
    "전문대학": 1
})

# 동일 학교명 중복 제거
university_df = university_df.sort_values("정렬순서")
university_df = university_df.drop_duplicates(
    subset=["학교명"],
    keep="first"
)


# -----------------------------
# 데이터 현황
# -----------------------------
st.subheader("📊 전국 대학 데이터 현황")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("전체 데이터", f"{len(df):,}개")

with col2:
    st.metric("대학 및 전문대학", f"{len(university_df):,}개")

with col3:
    st.metric("지역 수", f"{university_df['시도명'].nunique()}개")

st.divider()


# -----------------------------
# 지역 검색 기능
# -----------------------------
st.subheader("🔍 지역별 대학교 검색")

st.write("검색하고 싶은 지역명을 입력해 주세요.")

search_region = st.text_input(
    "지역 검색",
    placeholder="예: 서울, 부산, 경기도, 대전"
).strip()

if search_region:

    # 지역명 검색
    result = university_df[
        university_df["시도명"].str.contains(
            search_region,
            case=False,
            na=False
        )
    ].copy()

    if len(result) > 0:

        regions = result["시도명"].unique()

        if len(regions) > 1:
            st.info(
                "검색어와 일치하는 지역이 여러 곳입니다: "
                + ", ".join(regions)
            )

        st.success(
            f"'{search_region}' 검색 결과: "
            f"{len(result)}개의 대학 데이터"
        )

        # 동일 학교 중복 제거 후 상위 2개 표시
        result = result.drop_duplicates(subset=["학교명"])
        top_two = result.head(2)

        st.subheader("🏫 추천 대학교")

        columns = st.columns(2)

        for i, (_, row) in enumerate(top_two.iterrows()):

            with columns[i]:

                with st.container(border=True):

                    st.markdown(f"### 🎓 {row['학교명']}")

                    st.write(
                        f"**지역:** {row['시도명']}"
                    )

                    st.write(
                        f"**대학 구분:** {row['대학구분명']}"
                    )

                    st.write(
                        f"**설립 형태:** {row['설립형태구분명']}"
                    )

                    address = row["소재지도로명주소"]

                    if pd.notna(address) and str(address).strip():
                        st.write(f"**주소:** {address}")
                    else:
                        st.write("**주소:** 정보 없음")

                    phone = row["대표전화번호"]

                    if pd.notna(phone) and str(phone).strip():
                        st.write(f"**대표 전화:** {phone}")

                    website = row["홈페이지주소"]

                    if pd.notna(website) and str(website).strip():

                        website = str(website).strip()

                        if not website.startswith(("http://", "https://")):
                            website = "https://" + website

                        st.link_button(
                            "🌐 학교 홈페이지 방문",
                            website,
                            use_container_width=True
                        )

        if len(top_two) < 2:
            st.warning("검색된 학교가 2곳보다 적습니다.")

        # 추가 검색 결과
        with st.expander("전체 검색 결과 확인하기"):
            st.dataframe(
                result.drop(columns=["정렬순서"], errors="ignore"),
                use_container_width=True,
                hide_index=True
            )

    else:
        st.warning(
            f"'{search_region}'에 해당하는 대학을 찾을 수 없습니다."
        )
        st.info("서울, 경기, 부산, 대전 등의 지역명을 검색해 보세요.")

else:
    st.info("지역을 입력하면 해당 지역의 대학교 2곳을 보여줍니다.")


st.divider()


# -----------------------------
# 지역별 대학 통계
# -----------------------------
st.subheader("📈 지역별 대학교 분포")

region_count = (
    university_df["시도명"]
    .value_counts()
    .sort_values(ascending=False)
)

if len(region_count) > 0:

    chart_df = region_count.reset_index()
    chart_df.columns = ["지역", "대학교 수"]

    st.bar_chart(
        chart_df.set_index("지역"),
        height=400
    )

    st.write("지역별 대학 데이터 순위")

    st.dataframe(
        chart_df,
        use_container_width=True,
        hide_index=True
    )


# -----------------------------
# 설립 형태 분석
# -----------------------------
st.divider()

st.subheader("🏛️ 설립 형태별 대학교 분석")

establishment_count = (
    university_df["설립형태구분명"]
    .value_counts()
)

st.bar_chart(establishment_count)


# -----------------------------
# 전체 데이터 확인
# -----------------------------
st.divider()

with st.expander("📚 전체 대학교 데이터 확인"):

    st.dataframe(
        university_df.drop(
            columns=["정렬순서"],
            errors="ignore"
        ),
        use_container_width=True,
        hide_index=True
    )

st.caption("대학교 데이터 출처: 업로드된 universities.csv")
st.caption("데이터를 기반으로 제작한 지역별 대학 검색 서비스")


