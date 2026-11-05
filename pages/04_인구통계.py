
import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="서울시 연령별 인구 분석",
    page_icon="📊",
    layout="wide"
)

# 핫핑크 색상
PINK = "#FF1493"

# pages 폴더의 상위 폴더 경로
BASE_DIR = Path(__file__).resolve().parent.parent

# 상위 폴더에 있는 CSV 파일
CSV_PATH = BASE_DIR / "population (2).csv"


@st.cache_data
def load_population(path: str) -> pd.DataFrame:
    """CSV 파일의 한글 인코딩을 자동으로 확인합니다."""

    last_error = None

    for encoding in ("cp949", "utf-8-sig", "euc-kr", "utf-8"):
        try:
            df = pd.read_csv(
                path,
                encoding=encoding,
                thousands=",",
                dtype={"행정구역": "string"}
            )
            break

        except UnicodeDecodeError as exc:
            last_error = exc

    else:
        raise ValueError(
            "CSV 인코딩을 읽지 못했습니다. "
            "원본 파일을 CP949 또는 UTF-8로 저장해 주세요."
        ) from last_error

    # 열 이름의 공백 제거
    df.columns = [str(col).strip() for col in df.columns]

    if "행정구역" not in df.columns:
        raise ValueError(
            "CSV에서 '행정구역' 열을 찾을 수 없습니다."
        )

    # 행정구역 이름 정리
    df["행정구역"] = (
        df["행정구역"]
        .astype("string")
        .str.strip()
    )

    # 숫자 열을 계산 가능한 숫자로 변환
    for col in df.columns:
        if col != "행정구역":
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    return df


def parse_region(value: str) -> str:
    """행정구역명 뒤에 붙은 행정코드를 제거합니다."""

    return re.sub(
        r"\s*\(\d+\)\s*$",
        "",
        str(value)
    ).strip()


def get_age_columns(columns, year: int, sex: str):
    """선택한 연도와 성별의 연령대 열을 나이순으로 반환합니다."""

    prefix = f"{year}년_{sex}_"
    found = []

    for col in columns:

        if not str(col).startswith(prefix):
            continue

        # 0~9세, 10~19세 등의 연령대
        match = re.search(
            r"_(\d+)~(\d+)세$",
            str(col)
        )

        if match:
            found.append(
                (int(match.group(1)), col)
            )
            continue

        # 100세 이상
        if re.search(r"_100세\s*이상$", str(col)):
            found.append((100, col))

    return [
        col for _, col in sorted(
            found,
            key=lambda item: item[0]
        )
    ]


def age_label(column: str) -> str:
    """CSV 열 이름을 그래프에 표시할 나이로 변환합니다."""

    match = re.search(
        r"_(\d+)~(\d+)세$",
        column
    )

    if match:
        return f"{match.group(1)}~{match.group(2)}세"

    if re.search(r"_100세\s*이상$", column):
        return "100세 이상"

    return column


def main():

    st.title("서울시 연령별 인구 분석")

    st.caption(
        "행정구역, 성별, 연도를 선택하면 "
        "연령대별 인구수를 꺾은선 그래프로 확인할 수 있습니다."
    )

    # CSV 파일 존재 여부 확인
    if not CSV_PATH.exists():

        st.error(
            f"CSV 파일을 찾을 수 없습니다: {CSV_PATH}\n\n"
            "상위 폴더에 'population (2).csv' 파일이 있는지 확인해 주세요."
        )

        st.stop()

    # 데이터 읽기
    try:
        df = load_population(str(CSV_PATH))

    except Exception as exc:

        st.error(
            f"데이터를 읽는 중 오류가 발생했습니다: {exc}"
        )

        st.stop()

    # 행정구역 이름 정리
    df["행정구역명"] = (
        df["행정구역"].map(parse_region)
    )

    regions = (
        df["행정구역명"]
        .dropna()
        .drop_duplicates()
        .tolist()
    )

    # CSV 열 이름에서 연도 추출
    years = sorted({
        int(match.group(1))
        for col in df.columns
        if (
            match := re.match(
                r"(\d{4})년_",
                str(col)
            )
        )
    })

    if not years:
        st.error("CSV 파일에서 연도 정보를 찾을 수 없습니다.")
        st.stop()

    # 성별 선택
    sex_options = ["거주자", "남", "여"]

    available_sexes = [
        sex
        for sex in sex_options
        if any(
            str(col).startswith(f"{year}년_{sex}_")
            for year in years
            for col in df.columns
        )
    ]

    if not available_sexes:
        st.error("CSV 파일에서 성별 정보를 찾을 수 없습니다.")
        st.stop()

    # 사용자 선택 영역
    c1, c2, c3 = st.columns(3)

    with c1:
        region = st.selectbox(
            "행정구역",
            regions,
            index=0
        )

    with c2:
        sex = st.selectbox(
            "성별",
            available_sexes,
            index=0
        )

    with c3:
        year = st.selectbox(
            "연도",
            years,
            index=len(years) - 1
        )

    # 선택한 행정구역 데이터
    selected = df.loc[
        df["행정구역명"] == region
    ]

    if selected.empty:

        st.warning(
            "선택한 행정구역의 데이터가 없습니다."
        )

        st.stop()

    row = selected.iloc[0]

    # 선택한 연도와 성별의 연령대 열 찾기
    age_cols = get_age_columns(
        df.columns,
        year,
        sex
    )

    if not age_cols:

        st.error(
            "선택한 연도와 성별에 해당하는 "
            "연령대별 열을 찾지 못했습니다."
        )

        st.stop()

    # 연령대별 인구수
    values = [
        0 if pd.isna(row[col])
        else int(row[col])
        for col in age_cols
    ]

    labels = [
        age_label(col)
        for col in age_cols
    ]

    # 그래프 생성
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=labels,
            y=values,
            mode="lines+markers",
            name=f"{region} · {sex} · {year}년",

            # 핫핑크 선
            line=dict(
                color=PINK,
                width=3
            ),

            # 핫핑크 점
            marker=dict(
                color=PINK,
                size=8
            ),

            hovertemplate=(
                "%{x}<br>"
                "인구수: %{y:,.0f}명"
                "<extra></extra>"
            )
        )
    )

    # 세로축 최대값 계산
    max_value = max(values) if values else 0

    y_max = max(
        10_000_000,
        ((max_value // 10_000_000) + 1)
        * 10_000_000
    )

    # 그래프 제목 및 기본 설정
    fig.update_layout(
        title=f"{region} {year}년 {sex} 연령대별 인구",
        xaxis_title="나이",
        yaxis_title="인구수(명)",

        plot_bgcolor="white",
        paper_bgcolor="white",

        font=dict(
            family=(
                "Malgun Gothic, AppleGothic, "
                "NanumGothic, sans-serif"
            ),
            color="#333333"
        ),

        margin=dict(
            l=25,
            r=25,
            t=65,
            b=30
        ),

        hovermode="x unified",
        showlegend=False
    )

    # 가로축: 10살 단위
    fig.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=labels,
        tickangle=0,
        showgrid=True,
        gridcolor="#F3D5E5",
        dtick=1
    )

    # 세로축: 1천만 명 단위
    fig.update_yaxes(
        rangemode="tozero",
        range=[0, y_max],
        tickmode="linear",
        tick0=0,
        dtick=10_000_000,
        tickformat=",",
        showgrid=True,
        gridcolor="#E8E8E8",
        zeroline=True
    )

    # 그래프 표시
    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # 선택 지역 총인구수
    total_col = f"{year}년_{sex}_총인구수"

    if (
        total_col in df.columns
        and pd.notna(row[total_col])
    ):

        st.metric(
            "선택 지역 인구수",
            f"{int(row[total_col]):,}명"
        )

    # 그래프 데이터 표
    with st.expander("그래프에 사용된 데이터 보기"):

        chart_data = pd.DataFrame({
            "나이": labels,
            "인구수": values
        })

        st.dataframe(
            chart_data,
            hide_index=True,
            use_container_width=True
        )

        # 한글 호환 CSV 다운로드
        st.download_button(
            "표를 CSV로 다운로드 (한글 호환)",

            data=chart_data.to_csv(
                index=False
            ).encode("utf-8-sig"),

            file_name=f"population_{year}_{sex}.csv",
            mime="text/csv"
        )


if __name__ == "__main__":
    main()
