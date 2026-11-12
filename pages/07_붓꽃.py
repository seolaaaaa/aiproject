
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from pathlib import Path
from io import BytesIO

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler


# ---------------------------------
# 1. 페이지 설정
# ---------------------------------

st.set_page_config(
    page_title="Iris AI 품종 예측",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 붓꽃 품종 예측 AI")
st.write(
    "꽃잎의 길이와 너비를 입력하면 "
    "인공지능이 붓꽃의 품종을 예측해 줍니다."
)

st.divider()


# ---------------------------------
# 2. CSV 파일 불러오기
# ---------------------------------

def read_iris_data(source):

    encodings = ["cp949", "utf-8-sig", "euc-kr"]

    for encoding in encodings:
        try:
            if isinstance(source, bytes):
                df = pd.read_csv(
                    BytesIO(source),
                    encoding=encoding
                )
            else:
                df = pd.read_csv(
                    source,
                    encoding=encoding
                )

            return df

        except UnicodeDecodeError:
            continue

    raise ValueError("CSV 파일 인코딩을 확인해 주세요.")


file_path = Path(__file__).parent / "Iris.csv"

if file_path.exists():
    df = read_iris_data(file_path)
else:
    uploaded_file = st.file_uploader(
        "Iris.csv 파일을 업로드해 주세요.",
        type=["csv"]
    )

    if uploaded_file is None:
        st.info("Iris.csv 파일이 필요합니다.")
        st.stop()

    df = read_iris_data(uploaded_file.getvalue())


# ---------------------------------
# 3. 데이터 전처리
# ---------------------------------

df.columns = df.columns.str.strip()

required_columns = [
    "꽃잎길이",
    "꽃잎너비",
    "품종"
]

if not all(col in df.columns for col in required_columns):
    st.error("CSV 파일의 열 이름을 확인해 주세요.")
    st.stop()

df = df[required_columns].copy()

df["꽃잎길이"] = pd.to_numeric(
    df["꽃잎길이"], errors="coerce"
)

df["꽃잎너비"] = pd.to_numeric(
    df["꽃잎너비"], errors="coerce"
)

df = df.dropna()

if df.empty:
    st.error("분석할 데이터가 없습니다.")
    st.stop()

X = df[["꽃잎길이", "꽃잎너비"]]
y = df["품종"]


# ---------------------------------
# 4. 학습 및 정확도 평가
# ---------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

evaluation_model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)

evaluation_model.fit(X_train, y_train)

y_pred = evaluation_model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

# 전체 데이터를 이용한 최종 예측 모델
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)

model.fit(X, y)


# ---------------------------------
# 5. 사용자 입력
# ---------------------------------

st.subheader("🌱 꽃잎 크기 입력")

col1, col2 = st.columns(2)

with col1:
    petal_length = st.number_input(
        "꽃잎 길이 (cm)",
        min_value=0.0,
        max_value=10.0,
        value=4.5,
        step=0.1
    )

with col2:
    petal_width = st.number_input(
        "꽃잎 너비 (cm)",
        min_value=0.0,
        max_value=5.0,
        value=1.5,
        step=0.1
    )

predict_button = st.button(
    "🌸 품종 예측하기",
    use_container_width=True
)


# ---------------------------------
# 6. 예측 및 결과 출력
# ---------------------------------

if predict_button:

    user_data = pd.DataFrame(
        [[petal_length, petal_width]],
        columns=["꽃잎길이", "꽃잎너비"]
    )

    prediction = model.predict(user_data)[0]

    probabilities = model.predict_proba(user_data)[0]

    class_names = model.classes_

    korean_names = {
        "Iris-setosa": "세토사",
        "Iris-versicolor": "버시컬러",
        "Iris-virginica": "버지니카"
    }

    result_name = korean_names.get(
        prediction, prediction
    )

    st.divider()

    st.subheader("🎯 AI 예측 결과")

    st.success(
        f"예측된 붓꽃 품종은 **{result_name}** 입니다!"
    )

    st.metric(
        "모델의 예측 확률",
        f"{probabilities[np.where(class_names == prediction)[0][0]] * 100:.1f}%"
    )

    # 품종별 예측 확률
    probability_df = pd.DataFrame({
        "품종": [
            korean_names.get(name, name)
            for name in class_names
        ],
        "예측 확률(%)": probabilities * 100
    })

    st.write("### 품종별 예측 확률")

    st.bar_chart(
        probability_df.set_index("품종")
    )


    # ---------------------------------
    # 7. 분류 영역 시각화
    # ---------------------------------

    st.divider()
    st.subheader("📊 AI 품종 분류 지도")

    x_min = min(X["꽃잎길이"].min(), petal_length) - 0.5
    x_max = max(X["꽃잎길이"].max(), petal_length) + 0.5

    y_min = min(X["꽃잎너비"].min(), petal_width) - 0.3
    y_max = max(X["꽃잎너비"].max(), petal_width) + 0.3

    xx, yy = np.meshgrid(
        np.linspace(x_min, x_max, 250),
        np.linspace(y_min, y_max, 250)
    )

    grid = pd.DataFrame({
        "꽃잎길이": xx.ravel(),
        "꽃잎너비": yy.ravel()
    })

    Z = model.predict(grid)

    class_to_num = {
        name: i for i, name in enumerate(class_names)
    }

    Z_num = np.array([
        class_to_num[name] for name in Z
    ]).reshape(xx.shape)

    fig, ax = plt.subplots(figsize=(10, 6))

    cmap = plt.get_cmap("Set2", len(class_names))

    # AI가 분류한 영역
    ax.contourf(
        xx,
        yy,
        Z_num,
        levels=np.arange(len(class_names) + 1) - 0.5,
        cmap=cmap,
        alpha=0.22
    )

    # 실제 붓꽃 데이터
    for i, name in enumerate(class_names):

        subset = df[df["품종"] == name]

        ax.scatter(
            subset["꽃잎길이"],
            subset["꽃잎너비"],
            color=cmap(i),
            label=korean_names.get(name, name),
            s=45,
            edgecolors="white",
            linewidths=0.5
        )

    # 사용자 입력값: 회색 별
    ax.scatter(
        petal_length,
        petal_width,
        color="gray",
        marker="*",
        s=350,
        edgecolors="black",
        linewidths=1.2,
        label="사용자 입력값",
        zorder=10
    )

    ax.set_xlabel("꽃잎 길이 (cm)", fontsize=12)
    ax.set_ylabel("꽃잎 너비 (cm)", fontsize=12)

    ax.set_title(
        "Random Forest 품종 분류 영역",
        fontsize=15
    )

    ax.legend()
    ax.grid(alpha=0.2)

    st.pyplot(fig)
    plt.close(fig)

    st.caption(
        "배경 색상은 AI가 해당 꽃잎 크기를 "
        "어떤 품종으로 분류하는지 나타냅니다. "
        "회색 별은 사용자가 입력한 값입니다."
    )


    # ---------------------------------
    # 8. 왜 해당 품종으로 예측했을까?
    # ---------------------------------

    st.divider()
    st.subheader("🔍 AI가 이렇게 판단한 이유")

    st.write(
        f"입력한 꽃잎 길이는 **{petal_length}cm**, "
        f"꽃잎 너비는 **{petal_width}cm**입니다."
    )

    st.write(
        f"AI는 이 위치가 **{result_name}**의 "
        "분류 영역에 해당한다고 판단했습니다."
    )

    # 특성 중요도
    importance_df = pd.DataFrame({
        "특성": ["꽃잎 길이", "꽃잎 너비"],
        "중요도": model.feature_importances_
    }).sort_values(
        "중요도", ascending=False
    )

    st.write("### 품종 예측에 사용된 특성 중요도")

    st.bar_chart(
        importance_df.set_index("특성")
    )

    st.caption(
        "특성 중요도는 모델 전체에서 각 특성이 "
        "분류에 기여한 상대적 비중입니다. "
        "개별 예측의 직접적인 원인이나 인과관계를 뜻하지는 않습니다."
    )

    # ---------------------------------
    # 9. 가까운 실제 데이터 비교
    # ---------------------------------

    scaler = StandardScaler()

    scaled_X = scaler.fit_transform(X)

    scaled_user = scaler.transform(user_data)

    distances = np.sqrt(
        ((scaled_X - scaled_user) ** 2).sum(axis=1)
    )

    nearest_indices = np.argsort(distances)[:5]

    nearest_df = df.iloc[nearest_indices].copy()

    nearest_df["거리"] = distances[nearest_indices]

    nearest_df["품종"] = nearest_df["품종"].map(
        lambda x: korean_names.get(x, x)
    )

    st.write("### 입력값과 가까운 실제 붓꽃 5개")

    st.dataframe(
        nearest_df.reset_index(drop=True),
        use_container_width=True
    )

    st.caption(
        "거리는 두 입력 특성을 표준화한 뒤 계산했습니다. "
        "가까운 실제 데이터는 참고 자료이며, "
        "최종 예측은 랜덤 포레스트 모델이 결정합니다."
    )


# ---------------------------------
# 10. 모델 평가
# ---------------------------------

st.divider()

st.subheader("📈 AI 모델 성능")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "테스트 데이터 정확도",
        f"{accuracy * 100:.1f}%"
    )

with col2:
    st.metric(
        "학습에 사용한 전체 데이터",
        f"{len(df)}개"
    )

st.caption(
    "정확도는 전체 데이터를 무작위로 80% 학습용, "
    "20% 테스트용으로 나누어 측정한 결과입니다."
)

st.info(
    "이 프로그램은 꽃잎 길이와 너비만 사용합니다. "
    "따라서 네 가지 특성을 모두 사용하는 일반적인 "
    "Iris 품종 분류 모델과 결과가 다를 수 있습니다."
)
