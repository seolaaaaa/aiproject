
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor


# ==========================================
# 1. 기본 페이지 설정
# ==========================================

st.set_page_config(
    page_title="월별 평균기온 분석 & AI 예측",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌍 월별 평균기온 분석 & AI 예측")
st.caption(
    "1907~2025년 관측자료를 바탕으로 월별 기온을 분석하고 "
    "세 가지 알고리즘으로 미래 기온을 예측합니다."
)

DATA_FILE = "temperature.csv"
TEMP_COLUMN = "평균기온(℃)"


# ==========================================
# 2. 월 데이터 설정
# ==========================================

MONTHS = {
    "1월": "Jan",
    "2월": "Feb",
    "3월": "Mar",
    "4월": "Apr",
    "5월": "May",
    "6월": "Jun",
    "7월": "Jul",
    "8월": "Aug",
    "9월": "Sep",
    "10월": "Oct",
    "11월": "Nov",
    "12월": "Dec"
}

MONTH_NUMBERS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12
}


# ==========================================
# 3. CSV 데이터 불러오기
# ==========================================

@st.cache_data
def load_temperature_data(file_path):

    try:
        raw = pd.read_csv(file_path, encoding="cp949")

    except UnicodeDecodeError:
        try:
            raw = pd.read_csv(file_path, encoding="euc-kr")

        except UnicodeDecodeError:
            raw = pd.read_csv(file_path, encoding="utf-8-sig")

    required = {"일시", TEMP_COLUMN}

    missing = required - set(raw.columns)

    if missing:
        raise ValueError(
            f"CSV에 필요한 열이 없습니다: {', '.join(sorted(missing))}"
        )

    raw = raw.copy()

    raw["일시"] = raw["일시"].astype(str).str.strip()

    # 날짜가 처음 반복되는 위치 확인
    duplicate_positions = np.flatnonzero(
        raw["일시"].duplicated(keep="first").to_numpy()
    )

    split_at = (
        int(duplicate_positions[0])
        if len(duplicate_positions)
        else len(raw)
    )

    month_values = []
    year_values = []

    for idx, label in enumerate(raw["일시"]):

        try:
            month_text, year_text = label.split("-")

            month_text = month_text[:3].title()

            short_year = int(year_text)

            month_number = MONTH_NUMBERS[month_text]

            # 첫 번째 구간은 1900년대
            # 반복 날짜 이후 구간은 2000년대

            full_year = (
                1900 + short_year
                if idx < split_at
                else 2000 + short_year
            )

            month_values.append(month_number)
            year_values.append(full_year)

        except (ValueError, KeyError, TypeError):

            month_values.append(np.nan)
            year_values.append(np.nan)

    raw["연도"] = year_values
    raw["월"] = month_values

    raw[TEMP_COLUMN] = pd.to_numeric(
        raw[TEMP_COLUMN],
        errors="coerce"
    )

    raw = raw.dropna(
        subset=["연도", "월", TEMP_COLUMN]
    )

    raw["연도"] = raw["연도"].astype(int)
    raw["월"] = raw["월"].astype(int)

    # 1907~2025년 데이터만 사용

    raw = raw[
        (raw["연도"] >= 1907)
        & (raw["연도"] <= 2025)
    ]

    # 동일 연도와 월의 데이터 평균 계산

    monthly = (
        raw.groupby(
            ["연도", "월"],
            as_index=False
        )[TEMP_COLUMN]
        .mean()
        .sort_values(["연도", "월"])
    )

    return monthly


# ==========================================
# 4. 데이터 불러오기 및 오류 처리
# ==========================================

try:

    data = load_temperature_data(DATA_FILE)

except FileNotFoundError:

    st.error(
        "temperature.csv 파일을 찾을 수 없습니다. "
        "app.py와 같은 폴더에 파일을 넣어주세요."
    )

    st.stop()

except Exception as error:

    st.error(f"데이터를 읽는 중 문제가 발생했습니다: {error}")

    st.stop()


if data.empty:

    st.error("분석할 데이터가 없습니다.")

    st.stop()


# ==========================================
# 5. 사용자 분석 설정
# ==========================================

st.sidebar.header("⚙️ 분석 설정")

selected_month_label = st.sidebar.selectbox(
    "분석할 월 선택",
    list(MONTHS.keys())
)

selected_month = MONTH_NUMBERS[
    MONTHS[selected_month_label]
]

min_future_year = int(data["연도"].max()) + 1

max_future_year = 2100

future_year = st.sidebar.number_input(
    "예측할 마지막 연도",
    min_value=min_future_year,
    max_value=max_future_year,
    value=min(min_future_year + 10, max_future_year),
    step=1
)

st.sidebar.info(
    "선택한 월의 연도별 평균기온을 학습합니다. "
    "예측값은 실제 관측값이 아닌 모델의 추정치입니다."
)


# ==========================================
# 6. 선택한 월의 데이터 추출
# ==========================================

month_data = data[
    data["월"] == selected_month
][["연도", TEMP_COLUMN]].dropna()

month_data = month_data.sort_values("연도")


if len(month_data) < 10:

    st.error(
        "선택한 월의 데이터가 너무 적어 예측하기 어렵습니다."
    )

    st.stop()


X = month_data[["연도"]].to_numpy()

y = month_data[TEMP_COLUMN].to_numpy()


# 미래 연도 생성

future_years = np.arange(
    int(month_data["연도"].max()) + 1,
    int(future_year) + 1
)

future_X = future_years.reshape(-1, 1)


# ==========================================
# 7. AI 예측 알고리즘 3개 설정
# ==========================================

models = {

    "선형 회귀": LinearRegression(),

    "랜덤 포레스트": RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        min_samples_leaf=3
    ),

    "그래디언트 부스팅": GradientBoostingRegressor(
        n_estimators=150,
        learning_rate=0.03,
        max_depth=2,
        loss="squared_error",
        random_state=42
    )

}


# ==========================================
# 8. 알고리즘 학습 및 예측
# ==========================================

predictions = {}

for name, model in models.items():

    model.fit(X, y)

    predictions[name] = model.predict(future_X)


# ==========================================
# 9. 주요 기온 정보
# ==========================================

latest_year = int(month_data["연도"].max())

latest_temp = float(
    month_data.iloc[-1][TEMP_COLUMN]
)

metric1, metric2, metric3 = st.columns(3)

metric1.metric(
    "선택한 월",
    selected_month_label
)

metric2.metric(
    "가장 최근 관측 연도",
    f"{latest_year}년"
)

metric3.metric(
    "최근 평균기온",
    f"{latest_temp:.1f} °C"
)


st.divider()


# ==========================================
# 10. 1907~2025년 실제 기온 그래프
# ==========================================

st.subheader(
    f"📈 {selected_month_label}의 장기 평균기온 변화 (1907~2025)"
)

st.write(
    "가로축은 연도, 세로축은 해당 월의 평균기온입니다. "
    "점 하나가 해당 연도의 선택한 월 평균기온을 나타냅니다."
)

history_fig = go.Figure()

history_fig.add_trace(
    go.Scatter(

        x=month_data["연도"],

        y=month_data[TEMP_COLUMN],

        mode="lines+markers",

        name="실제 평균기온",

        line=dict(width=2),

        marker=dict(size=5),

        hovertemplate=(
            "%{x}년<br>"
            "평균기온: %{y:.1f}℃"
            "<extra></extra>"
        )
    )
)

history_fig.update_layout(

    xaxis_title="연도",

    yaxis_title="평균기온 (℃)",

    hovermode="x unified",

    template="plotly_white",

    height=470,

    legend=dict(
        orientation="h",
        y=1.1
    )

)

st.plotly_chart(
    history_fig,
    use_container_width=True
)


st.divider()


# ==========================================
# 11. 미래 평균기온 예측 그래프
# ==========================================

st.subheader(
    "🤖 세 가지 AI 알고리즘의 미래 예측 비교"
)

st.write(
    f"{latest_year}년까지의 관측자료를 학습한 뒤 "
    f"{int(future_year)}년까지 매년 "
    f"{selected_month_label} 평균기온을 예측합니다."
)


forecast_fig = go.Figure()


# 실제 관측값

forecast_fig.add_trace(
    go.Scatter(

        x=month_data["연도"],

        y=month_data[TEMP_COLUMN],

        mode="lines",

        name="실제 관측값",

        line=dict(
            color="#333333",
            width=2
        )

    )
)


# 알고리즘별 선 스타일

line_styles = {

    "선형 회귀": dict(
        width=3,
        dash="solid"
    ),

    "랜덤 포레스트": dict(
        width=3,
        dash="dash"
    ),

    "그래디언트 부스팅": dict(
        width=3,
        dash="dot"
    )

}


# 세 알고리즘의 예측선을 하나의 그래프에 표시

for name, values in predictions.items():

    forecast_fig.add_trace(
        go.Scatter(

            x=future_years,

            y=values,

            mode="lines+markers",

            name=name,

            line=line_styles[name],

            marker=dict(size=5),

            hovertemplate=(
                "%{x}년<br>"
                "예측 평균기온: %{y:.2f}℃"
                "<extra></extra>"
            )

        )
    )


# 예측 시작 지점 표시

forecast_fig.add_vline(

    x=latest_year,

    line_width=1,

    line_dash="dash",

    annotation_text="예측 시작",

    annotation_position="top"

)


forecast_fig.update_layout(

    xaxis_title="연도",

    yaxis_title="평균기온 (℃)",

    hovermode="x unified",

    template="plotly_white",

    height=540,

    legend=dict(
        orientation="h",
        y=1.12
    )

)


st.plotly_chart(
    forecast_fig,
    use_container_width=True
)


# ==========================================
# 12. 마지막 예측 연도 결과 비교
# ==========================================

st.markdown(
    f"#### 🔎 {int(future_year)}년 예측 결과"
)

result_cols = st.columns(3)

for col, (name, values) in zip(
    result_cols,
    predictions.items()
):

    col.metric(
        name,
        f"{float(values[-1]):.2f} °C"
    )


# 예측 결과 표

result_table = pd.DataFrame({

    "연도": future_years,

    **{
        name: np.round(values, 2)
        for name, values in predictions.items()
    }

})


st.dataframe(
    result_table,
    use_container_width=True,
    hide_index=True
)


# 예측 결과 다운로드

st.download_button(

    label="📥 예측 결과 CSV 다운로드",

    data=result_table.to_csv(
        index=False,
        encoding="utf-8-sig"
    ),

    file_name=f"{selected_month_label}_기온예측결과.csv",

    mime="text/csv"

)


st.divider()


# ==========================================
# 13. 알고리즘 작동 원리 설명
# ==========================================

st.subheader(
    "🧠 알고리즘은 어떻게 작동할까?"
)

st.caption(
    "아래 설명과 예측선의 모양을 함께 보면 "
    "세 알고리즘의 차이를 이해할 수 있습니다."
)


# ------------------------------------------
# 알고리즘 1. 선형 회귀
# ------------------------------------------

with st.expander(
    "1. 선형 회귀 (Linear Regression)",
    expanded=True
):

    st.markdown("""
    **작동 원리**

    - 과거 연도와 평균기온 사이의 관계를 하나의 직선으로 표현합니다.
    - 데이터와 직선 사이의 오차 제곱합이 작아지도록 기울기와 절편을 학습합니다.
    - 학습한 직선을 미래 연도까지 연장해 예측합니다.

    **그래프에서 읽는 방법**

    - 예측선이 직선 형태로 나타납니다.
    - 기울기가 양수이면 장기적으로 상승하는 추세,
      음수이면 하락하는 추세를 뜻합니다.

    **장점과 한계**

    - 장기적인 전체 추세를 간단하게 파악하기 좋습니다.
    - 기온 변화가 직선 형태가 아닐 경우
      복잡한 변화를 충분히 반영하지 못할 수 있습니다.
    """)


# ------------------------------------------
# 알고리즘 2. 랜덤 포레스트
# ------------------------------------------

with st.expander(
    "2. 랜덤 포레스트 (Random Forest)"
):

    st.markdown("""
    **작동 원리**

    - 학습 데이터를 여러 부분으로 무작위 추출해 여러 결정 트리를 만듭니다.
    - 각 트리가 예측한 값을 모아 평균을 계산합니다.
    - 여러 트리의 결과를 결합해 예측의 변동성을 줄입니다.

    **그래프에서 읽는 방법**

    - 구간별로 값이 계단처럼 바뀌거나 평평하게 이어질 수 있습니다.
    - 여러 트리의 평균을 사용하기 때문에
      하나의 트리보다 결과가 안정적입니다.

    **장점과 한계**

    - 데이터 안에 있는 복잡한 관계를 학습할 수 있습니다.
    - 학습한 연도 범위를 벗어난 미래에서는
      새로운 상승·하락 추세를 스스로 길게 이어가기 어렵습니다.
    """)


# ------------------------------------------
# 알고리즘 3. 그래디언트 부스팅
# ------------------------------------------

with st.expander(
    "3. 그래디언트 부스팅 (Gradient Boosting)"
):

    st.markdown("""
    **작동 원리**

    - 첫 번째 모델을 만든 뒤 예측에서 발생한 오차를 확인합니다.
    - 다음 모델이 이전 모델의 오차를 보완하도록 순서대로 학습합니다.
    - 여러 약한 학습기의 결과를 더해 최종 예측을 만듭니다.

    **그래프에서 읽는 방법**

    - 데이터의 구간별 패턴을 반영해
      선형 회귀와 다른 형태의 예측선이 나타날 수 있습니다.
    - 트리 기반 모델이므로 학습 범위 밖에서는
      예측값이 일정한 수준에 가까워질 수 있습니다.

    **장점과 한계**

    - 데이터에 포함된 비선형 패턴을 학습하는 데 유용합니다.
    - 설정값과 데이터에 따라 결과가 달라지며,
      미래의 장기 추세를 정확히 보장하지는 않습니다.
    """)


# ==========================================
# 14. 분석 시 주의사항
# ==========================================

st.info(
    "📌 해석할 때 주의하세요: 이 앱은 선택한 월의 연도별 "
    "평균기온만 사용해 예측합니다. 계절 내 다른 월, "
    "온실가스 배출량, 해류, 도시화 등 기후에 영향을 주는 "
    "요인은 모델 입력에 포함하지 않았습니다. "
    "따라서 교육용 추세 비교이며 공식 기후 전망은 아닙니다."
)


# ==========================================
# 15. 데이터 출처
# ==========================================

st.caption(
    "데이터 출처: 사용자가 제공한 temperature.csv "
    "| 분석 범위: 1907~2025년"
)
