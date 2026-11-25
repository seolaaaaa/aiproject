
import pandas as pd
import matplotlib.pyplot as plt

# 1. 데이터 불러오기
df = pd.read_csv("universities.csv")

# 2. 데이터 기본 정보
print("데이터 크기:", df.shape)
print("\n데이터 정보")
print(df.info())

# 3. 결측치 확인
print("\n결측치")
print(df.isnull().sum())

# 4. 지역별 대학 데이터 수
region_count = df["시도명"].value_counts()
print("\n지역별 데이터 수")
print(region_count)

# 5. 대학 구분별 데이터 수
print("\n대학 구분별")
print(df["대학구분명"].value_counts())

# 6. 설립 형태별 데이터 수
print("\n설립 형태별")
print(df["설립형태구분명"].value_counts())

# 7. 지역별 그래프
region_count.head(10).plot(
    kind="bar",
    figsize=(10, 5),
    title="지역별 대학 데이터 분석"
)

plt.xlabel("지역")
plt.ylabel("학교 데이터 수")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# 8. 중복 데이터 확인
print("\n중복 학교명:", df["학교명"].duplicated().sum())

# 9. 학교명 고유 개수
print("\n고유 학교명:", df["학교명"].nunique())

