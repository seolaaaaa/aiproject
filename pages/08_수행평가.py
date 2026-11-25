
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="Animal Data",
    page_icon="🐾",
    layout="wide"
)

# 제목
st.title("🐾 Animal Data Explorer")
st.write("동물 데이터를 검색하고 분석하는 사이트입니다.")

# CSV 데이터 불러오기
@st.cache_data
def load_data():
    file_path = Path(__file__).parent / "Animals.csv"
    df = pd.read_csv(file_path)

    required_columns = ["id", "name", "animal"]

    if not all(col in df.columns for col in required_columns):
        raise ValueError("CSV에 id, name, animal 열이 필요합니다.")

    return df

try:
    df = load_data()

    # 데이터 개요
    st.subheader("📊 데이터 개요")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("전체 데이터", len(df))

    with col2:
        st.metric("동물 종류", df["animal"].nunique())

    with col3:
        st.metric("이름 종류", df["name"].nunique())

    st.divider()

    # 검색 기능
    st.subheader("🔍 동물 검색")

    search_col, filter_col = st.columns(2)

    with search_col:
        keyword = st.text_input(
            "이름 검색",
            placeholder="검색할 이름을 입력하세요."
        )

    with filter_col:
        animals = ["전체"] + sorted(df["animal"].dropna().unique().tolist())

        selected_animal = st.selectbox(
            "동물 종류 선택",
            animals
        )

    # 데이터 필터링
    filtered_df = df.copy()

    if keyword:
        filtered_df = filtered_df[
            filtered_df["name"].astype(str).str.contains(
                keyword, case=False, na=False
            )
        ]

    if selected_animal != "전체":
        filtered_df = filtered_df[
            filtered_df["animal"] == selected_animal
        ]

    # 검색 결과
    st.subheader("📋 검색 결과")

    st.write(f"검색된 데이터: {len(filtered_df)}개")

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # 동물 종류별 분석
    st.subheader("📈 동물 종류별 데이터 분석")

    animal_counts = df["animal"].value_counts()

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.write("동물 종류별 개수")

        st.bar_chart(animal_counts)

    with chart_col2:
        st.write("동물 종류별 비율")

        st.dataframe(
            animal_counts.rename("개수"),
            use_container_width=True
        )

    # 원본 데이터
    with st.expander("전체 원본 데이터 확인"):
        st.dataframe(df, use_container_width=True)

    # 다운로드
    csv_data = filtered_df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="📥 검색 결과 CSV 다운로드",
        data=csv_data,
        file_name="animal_search_result.csv",
        mime="text/csv"
    )

except FileNotFoundError:
    st.error("Animals.csv 파일을 찾을 수 없습니다.")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")





    
       
                   
