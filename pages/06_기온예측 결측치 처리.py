

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
    "1907~2025년 관측자료를 바탕으로 결측치 처리 방법과 "
    "AI 알고리즘에 따른 미래 기온 예측 결과를 비교합니다."
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
    "Jan": 1, "Feb": 2, "Mar": 3,
    "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9,
    "Oct": 10, "Nov": 11, "Dec": 12
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

    # 중복되는 월 이름이 처음 나타나는 위치 확인
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

    # 기온 결측치는 여기서 제거하지 않음!
    raw = raw.dropna(subset=["연도", "월"])

    raw["연도"] = raw["연도"].astype(int)
    raw["월"] = raw["월"].astype(int)

    raw = raw[
        (raw["연도"] >= 1907)
        & (raw["연도"] <= 2025)
    ]

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
# 4. 데이터 불러오기
# ==========================================

try:

    data = load_temperature_data(DATA_FILE)

except FileNotFoundError:

    st.error(
        "temperature.csv 파일을 찾을 수 없습니다. "
        "app.py와 같은 폴더에 넣어주세요."
    )

    st.stop()

except Exception as error:

    st.error(f"데이터 오류: {error}")

    st.stop()


if data.empty:
    st.error("분석할 데이터가 없습니다.")
    st.stop()


# ==========================================
# 5. 사용자 분석 설정
# ==========================================

st.sidebar.header("⚙️ 분석 설정")

selected_month_label = st.sidebar.selectbox(
    "📅 분석할 월 선택",
    list(MONTHS.keys())
)

selected_month = MONTH_NUMBERS[
    MONTHS[selected_month_label]
]

st.sidebar.divider()

st.sidebar.subheader("1️⃣ 결측치 처리 방법")

imputation_options = {
    "결측치 제거": "remove",
    "중앙값으로 대체": "median",
    "선형보간법": "interpolate"
}

selected_imputation_label = st.sidebar.selectbox(
    "결측치 처리 방법 선택",
    list(imputation_options.keys())
)

selected_imputation = imputation_options[
    selected_imputation_label
]

st.sidebar.divider()

st.sidebar.subheader("2️⃣ AI 알고리즘 선택")

model_options = [
    "선형 회귀",
    "랜덤 포레스트",
    "그래디언트 부스팅"
]

selected_model = st.sidebar.selectbox(
    "예측 알고리즘 선택",
    model_options
)

st.sidebar.divider()

st.sidebar.subheader("3️⃣ 미래 예측 설정")

future_year = st.sidebar.number_input(
    "예측할 마지막 연도",
    min_value=2026,
    max_value=2100,
    value=2035,
    step=1
)

st.sidebar.info(
    "결측치 처리 방법과 AI 알고리즘을 변경하면 "
    "예측 결과와 그래프가 자동으로 변경됩니다."
)


# ==========================================
# 6. 선택한 월의 데이터 추출
# ==========================================

month_data = data[
    data["월"] == selected_month
][["연도", TEMP_COLUMN]].copy()

month_data = month_data.groupby("연도")[TEMP_COLUMN].mean()

# 1907~2025년 전체 연도 생성
# 관측값이 없는 연도도 결측치로 표시

all_years = pd.RangeIndex(
    start=1907,
    stop=2026,
    name="연도"
)

original_series = month_data.reindex(all_years)

original_series.index.name = "연도"

if original_series.notna().sum() < 10:

    st.error("선택한 월의 실제 관측 데이터가 너무 적습니다.")
    st.stop()

latest_year = int(original_series.dropna().index.max())

latest_temp = float(original_series.loc[latest_year])

missing_count = int(original_series.isna().sum())

missing_rate = (
    missing_count / len(original_series) * 100
)


# ==========================================
# 7. 결측치 처리 함수
# ==========================================

def process_missing_values(series, method):

    result = series.copy()

    if method == "remove":

        # 결측치가 있는 연도 제거
        result = result.dropna()

    elif method == "median":

        # 전체 관측 기온의 중앙값으로 대체
        median_value = result.median()

        result = result.fillna(median_value)

    elif method == "interpolate":

        # 연도에 따른 선형보간
        # 양 끝의 결측치는 가장 가까운 관측값으로 채움
        result = result.interpolate(
            method="linear",
            limit_direction="both"
        )

    return result


# ==========================================
# 8. AI 알고리즘 생성 함수
# ==========================================

def create_model(name):

    if name == "선형 회귀":

        return LinearRegression()

    elif name == "랜덤 포레스트":

        return RandomForestRegressor(
            n_estimators=300,
            random_state=42,
            min_samples_leaf=3
        )

    elif name == "그래디언트 부스팅":

        return GradientBoostingRegressor(
            n_estimators=150,
            learning_rate=0.03,
            max_depth=2,
            loss="squared_error",
            random_state=42
        )


# ==========================================
# 9. 예측 실행 함수
# ==========================================

def make_prediction(series, model_name, future_year):

    clean_data = process_missing_values(
        series,
        imputation_options_reverse[model_name]
    )

    if len(clean_data) < 10:
        raise ValueError("학습 데이터가 10개 미만입니다.")

    X = clean_data.index.to_numpy().reshape(-1, 1)

    y = clean_data.to_numpy()

    future_years = np.arange(
        2026,
        int(future_year) + 1
    )

    future_X = future_years.reshape(-1, 1)

    model = create_model(model_name)

    model.fit(X, y)

    predictions = model.predict(future_X)

    return future_years, predictions, clean_data


imputation_options_reverse = {
    "결측치 제거": "remove",
    "중앙값으로 대체": "median",
    "선형보간법": "interpolate"
}


# ==========================================
# 10. 전체 9가지 조합 예측
# ==========================================

all_predictions = {}

error_messages = []

for imputation_name in imputation_options_reverse:

    for model_name in model_options:

        try:

            future_years, values, clean_data = make_prediction(
                original_series,
                model_name,
                future_year
            )

            key = (imputation_name, model_name)

            all_predictions[key] = values

        except Exception as error:

            error_messages.append(
                f"{imputation_name} / {model_name}: {error}"
            )


if not all_predictions:

    st.error("예측할 수 있는 데이터가 없습니다.")
    st.stop()


if error_messages:

    for message in error_messages:
        st.warning(message)


# ==========================================
# 11. 선택한 설정으로 예측
# ==========================================

selected_key = (
    selected_imputation_label,
    selected_model
)

if selected_key not in all_predictions:

    st.error("선택한 설정으로 예측할 수 없습니다.")
    st.stop()

selected_predictions = all_predictions[selected_key]

selected_clean_data = process_missing_values(
    original_series,
    selected_imputation
)


# ==========================================
# 12. 주요 데이터 정보
# ==========================================

st.subheader("📊 기온 데이터 현황")

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric(
    "선택한 월",
    selected_month_label
)

metric2.metric(
    "최근 관측 연도",
    f"{latest_year}년"
)

metric3.metric(
    "최근 평균기온",
    f"{latest_temp:.1f}℃"
)

metric4.metric(
    "결측치 개수",
    f"{missing_count}개",
    f"{missing_rate:.1f}%"
)

st.divider()


# ==========================================
# 13. 결측치 현황 시각화
# ==========================================

st.subheader("🔍 결측치 현황 확인")

st.write(
    "선택한 월의 1907~2025년 데이터 중 "
    "기온이 기록되지 않은 연도를 확인합니다."
)

missing_fig = go.Figure()

missing_fig.add_trace(
    go.Scatter(
        x=original_series.index,
        y=original_series.values,
        mode="lines+markers",
        name="실제 관측 기온",
        connectgaps=False,
        line=dict(width=2),
        marker=dict(size=4),
        hovertemplate=(
            "%{x}년<br>"
            "평균기온: %{y:.1f}℃"
            "<extra></extra>"
        )
    )
)

missing_fig.update_layout(
    xaxis_title="연도",
    yaxis_title="평균기온 (℃)",
    template="plotly_white",
    height=400,
    hovermode="x unified"
)

st.plotly_chart(
    missing_fig,
    use_container_width=True
)

st.caption(
    "그래프에서 선이 끊어진 부분은 관측값이 없는 연도입니다."
)

st.divider()


# ==========================================
# 14. 선택한 결측치 처리 방법 결과
# ==========================================

st.subheader(
    f"🧹 결측치 처리 결과: {selected_imputation_label}"
)

imputation_fig = go.Figure()

imputation_fig.add_trace(
    go.Scatter(
        x=original_series.index,
        y=original_series.values,
        mode="lines+markers",
        name="원본 데이터",
        connectgaps=False,
        line=dict(width=2, color="#333333"),
        marker=dict(size=4)
    )
)

if selected_imputation == "remove":

    st.info(
        f"결측치 {missing_count}개를 제거했습니다. "
        f"학습에 사용한 데이터는 {len(selected_clean_data)}개입니다."
    )

elif selected_imputation == "median":

    st.info(
        f"결측치 {missing_count}개를 "
        f"중앙값 {original_series.median():.2f}℃로 대체했습니다."
    )

elif selected_imputation == "interpolate":

    st.info(
        f"선형보간법으로 결측치를 처리했습니다. "
        f"양 끝의 결측치는 가장 가까운 관측값으로 채웠습니다."
    )

imputation_fig.add_trace(
    go.Scatter(
        x=selected_clean_data.index,
        y=selected_clean_data.values,
        mode="lines",
        name="결측치 처리 후",
        line=dict(
            width=3,
            color="#10A37F"
        )
    )
)

imputation_fig.update_layout(
    xaxis_title="연도",
    yaxis_title="평균기온 (℃)",
    template="plotly_white",
    height=430,
    hovermode="x unified",
    legend=dict(orientation="h", y=1.12)
)

st.plotly_chart(
    imputation_fig,
    use_container_width=True
)


st.divider()


# ==========================================
# 15. 선택한 알고리즘의 미래 예측
# ==========================================

st.subheader("🤖 선택한 설정의 미래 기온 예측")

st.write(
    f"결측치 처리: **{selected_imputation_label}** "
    f"| AI 알고리즘: **{selected_model}**"
)

forecast_fig = go.Figure()

forecast_fig.add_trace(
    go.Scatter(
        x=original_series.index,
        y=original_series.values,
        mode="lines",
        name="실제 관측값",
        connectgaps=False,
        line=dict(
            color="#333333",
            width=2
        )
    )
)

forecast_fig.add_trace(
    go.Scatter(
        x=future_years,
        y=selected_predictions,
        mode="lines+markers",
        name="AI 예측값",
        line=dict(
            color="#E45756",
            width=3
        ),
        marker=dict(size=5),
        hovertemplate=(
            "%{x}년<br>"
            "예측 기온: %{y:.2f}℃"
            "<extra></extra>"
        )
    )
)

forecast_fig.add_vline(
    x=2025,
    line_dash="dash",
    line_width=1,
    annotation_text="예측 시작"
)

forecast_fig.update_layout(
    xaxis_title="연도",
    yaxis_title="평균기온 (℃)",
    template="plotly_white",
    height=500,
    hovermode="x unified",
    legend=dict(orientation="h", y=1.12)
)

st.plotly_chart(
    forecast_fig,
    use_container_width=True
)


# ==========================================
# 16. 결측치 처리 방법별 예측 결과 비교
# ==========================================

st.divider()

st.subheader("📊 결측치 처리 방법에 따른 예측 비교")

st.write(
    f"**{selected_model}** 알고리즘을 고정하고 "
    "결측치 처리 방법만 변경했을 때의 결과를 비교합니다."
)

imputation_colors = {
    "결측치 제거": "#3B82F6",
    "중앙값으로 대체": "#10B981",
    "선형보간법": "#F59E0B"
}

imputation_fig = go.Figure()

# 실제 관측값
imputation_fig.add_trace(
    go.Scatter(
        x=original_series.index,
        y=original_series.values,
        mode="lines",
        name="실제 관측값",
        line=dict(
            color="#333333",
            width=2
        )
    )
)

for imputation_name, color in imputation_colors.items():

    key = (imputation_name, selected_model)

    if key not in all_predictions:
        continue

    values = all_predictions[key]

    imputation_fig.add_trace(
        go.Scatter(
            x=future_years,
            y=values,
            mode="lines+markers",
            name=imputation_name,
            line=dict(
                color=color,
                width=3
            ),
            marker=dict(size=5)
        )
    )

imputation_fig.update_layout(
    xaxis_title="연도",
    yaxis_title="평균기온 (℃)",
    template="plotly_white",
    height=500,
    hovermode="x unified",
    legend=dict(orientation="h", y=1.12)
)

st.plotly_chart(
    imputation_fig,
    use_container_width=True
)


# ==========================================
# 17. 알고리즘별 예측 결과 비교
# ==========================================

st.divider()

st.subheader("🧠 AI 알고리즘에 따른 예측 비교")

st.write(
    f"**{selected_imputation_label}** 방법을 고정하고 "
    "AI 알고리즘만 변경했을 때의 결과를 비교합니다."
)

model_colors = {
    "선형 회귀": "#3B82F6",
    "랜덤 포레스트": "#10B981",
    "그래디언트 부스팅": "#F59E0B"
}

model_fig = go.Figure()

model_fig.add_trace(
    go.Scatter(
        x=original_series.index,
        y=original_series.values,
        mode="lines",
        name="실제 관측값",
        line=dict(
            color="#333333",
            width=2
        )
    )
)

for model_name, color in model_colors.items():

    key = (selected_imputation_label, model_name)

    if key not in all_predictions:
        continue

    values = all_predictions[key]

    model_fig.add_trace(
        go.Scatter(
            x=future_years,
            y=values,
            mode="lines+markers",
            name=model_name,
            line=dict(
                color=color,
                width=3
            ),
            marker=dict(size=5)
        )
    )

model_fig.update_layout(
    xaxis_title="연도",
    yaxis_title="평균기온 (℃)",
    template="plotly_white",
    height=500,
    hovermode="x unified",
    legend=dict(orientation="h", y=1.12)
)

st.plotly_chart(
    model_fig,
    use_container_width=True
)


# ==========================================
# 18. 9가지 조합의 최종 예측값 비교
# ==========================================

st.divider()

st.subheader("📋 전체 9가지 예측 결과 비교")

st.write(
    f"{int(future_year)}년의 예측 기온을 기준으로 "
    "결측치 처리 방법과 알고리즘의 차이를 비교합니다."
)

comparison_rows = []

for imputation_name in imputation_options_reverse:

    for model_name in model_options:

        key = (imputation_name, model_name)

        if key not in all_predictions:
            continue

        comparison_rows.append({
            "결측치 처리 방법": imputation_name,
            "AI 알고리즘": model_name,
            "예측 기온(℃)": round(
                float(all_predictions[key][-1]), 2
            )
        })

comparison_df = pd.DataFrame(comparison_rows)

st.dataframe(
    comparison_df,
    use_container_width=True,
    hide_index=True
)


# ==========================================
# 19. 최종 예측값 차이 분석
# ==========================================

st.subheader("🔎 예측 결과 차이 분석")

if len(comparison_df) > 0:

    max_temp = comparison_df["예측 기온(℃)"].max()
    min_temp = comparison_df["예측 기온(℃)"].min()

    difference = max_temp - min_temp

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "가장 높은 예측값",
        f"{max_temp:.2f}℃"
    )

    c2.metric(
        "가장 낮은 예측값",
        f"{min_temp:.2f}℃"
    )

    c3.metric(
        "전체 예측값 차이",
        f"{difference:.2f}℃"
    )

    st.caption(
        "전체 예측값 차이는 9가지 조합 중 가장 높은 값과 "
        "가장 낮은 값의 차이입니다."
    )


# ==========================================
# 20. 예측 결과 다운로드
# ==========================================

st.divider()

st.subheader("📥 분석 결과 다운로드")

selected_result_table = pd.DataFrame({
    "연도": future_years,
    "예측 기온(℃)": np.round(
        selected_predictions, 2
    )
})

st.download_button(
    label="선택한 설정의 예측 결과 CSV 다운로드",
    data=selected_result_table.to_csv(
        index=False,
        encoding="utf-8-sig"
    ),
    file_name=(
        f"{selected_month_label}_"
        f"{selected_imputation_label}_"
        f"{selected_model}_예측.csv"
    ),
    mime="text/csv"
)

st.download_button(
    label="전체 9가지 조합 비교 결과 CSV 다운로드",
    data=comparison_df.to_csv(
        index=False,
        encoding="utf-8-sig"
    ),
    file_name="기온예측_전체조합비교.csv",
    mime="text/csv"
)


# ==========================================
# 21. 알고리즘 작동 원리
# ==========================================

st.divider()

st.subheader("📚 분석 방법 알아보기")

with st.expander("1. 결측치 제거"):

    st.markdown("""
    - 기온이 기록되지 않은 연도의 데이터를 학습에서 제외합니다.
    - 실제 관측값만 사용한다는 장점이 있습니다.
    - 데이터가 줄어들어 학습 결과가 달라질 수 있습니다.
    """)

with st.expander("2. 중앙값 대체"):

    st.markdown("""
    - 해당 월의 실제 관측 기온 중앙값으로 결측치를 채웁니다.
    - 모든 연도의 데이터를 학습에 사용할 수 있습니다.
    - 실제 기온의 상승과 하락 패턴이 약해질 수 있습니다.
    """)

with st.expander("3. 선형보간법"):

    st.markdown("""
    - 앞뒤 연도의 실제 기온을 연결해 중간의 결측값을 추정합니다.
    - 연속적인 기온 변화의 흐름을 반영할 수 있습니다.
    - 양 끝의 결측값은 가장 가까운 실제 관측값으로 채웁니다.
    """)

with st.expander("4. 선형 회귀"):

    st.markdown("""
    - 연도와 평균기온의 관계를 직선으로 학습합니다.
    - 장기적인 상승 또는 하락 추세를 파악하기 좋습니다.
    """)

with st.expander("5. 랜덤 포레스트"):

    st.markdown("""
    - 여러 결정 트리를 학습시킨 후 결과의 평균을 계산합니다.
    - 복잡한 데이터 관계를 학습할 수 있습니다.
    - 학습 범위 밖의 미래에서는 예측값이 일정해지는 경향이 있습니다.
    """)

with st.expander("6. 그래디언트 부스팅"):

    st.markdown("""
    - 이전 모델의 예측 오차를 다음 모델이 보완합니다.
    - 여러 모델의 결과를 순차적으로 결합합니다.
    - 비선형적인 데이터 패턴을 학습할 수 있습니다.
    """)


# ==========================================
# 22. 분석 시 주의사항
# ==========================================

st.info(
    "📌 분석 시 주의사항: 결측치 처리 방법에 따라 "
    "학습 데이터가 달라지므로 예측값도 달라질 수 있습니다. "
    "또한 AI 알고리즘마다 학습 방식이 다르기 때문에 "
    "동일한 데이터를 사용해도 서로 다른 결과가 나옵니다. "
    "이 앱은 교육용 추세 비교이며 공식 기후 전망은 아닙니다. "
    "기온에 영향을 주는 온실가스, 해류, 도시화 등의 "
    "변수는 모델 입력에 포함하지 않았습니다."
)


# ==========================================
# 23. 데이터 출처
# ==========================================

st.caption(
    "데이터 출처: 사용자가 제공한 temperature.csv "
    "| 분석 범위: 1907~2025년 "
    "| 예측 방법: Scikit-learn 머신러닝"
)







        

    
      
