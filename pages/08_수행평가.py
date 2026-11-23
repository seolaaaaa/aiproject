
import streamlit as st
import pandas as pd
from pathlib import Path
import re

st.set_page_config(
    page_title="지역별 전문대학 검색",
    page_icon="🎓",
    layout="wide"
)

st.markdown("""
<style>
.block-container {
    max-width: 1100px;
    padding-top: 2rem;
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
    margin: 10px 0 0;
}
</style>
""", unsafe_allow_html=True)


def clean_name(value):
    """열 이름의 BOM, 공백, 괄호, 특수문자 등을 제거"""
    return re.sub(
        r"[^가-힣a-zA-Z0-9]",
        "",
        str(value)
    ).lower()


def normalize_region(value):
    return re.sub(
        r"[^가-힣a-zA-Z0-9]",
        "",
        str(value)
    ).lower()


# CSV 열 이름이 조금 달라도 인식하도록 설정
COLUMN_ALIASES = {
    "대학명": [
        "대학명", "학교명", "기관명", "학교",
        "대학", "college", "university", "name"
    ],
    "영문명": [
        "영문명", "영문학교명", "영문대학명",
        "영문명칭", "englishname"
    ],
    "지역": [
        "지역", "소재지역", "시도", "시도명",
        "권역", "소재지", "지역명"
    ],
    "주소": [
        "주소", "소재지주소", "도로명주소",
        "학교주소", "주소지"
    ],
    "홈페이지": [
        "홈페이지", "웹사이트", "사이트",
        "url", "website", "homepage"
    ],
    "전화": [
        "전화", "전화번호", "대표전화",
        "연락처", "전화번호(대표)"
    ],
    "팩스": ["팩스", "팩스번호"],
    "대표메일": [
        "대표메일", "이메일", "메일",
        "전자우편", "대표이메일", "email"
    ]
}


def read_csv_flexibly(path):
    """인코딩과 구분자 차이를 고려해 CSV 읽기"""
    last_error = None

    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            return pd.read_csv(
                path,
                encoding=encoding,
                dtype=str,
                sep=None,
                engine="python"
            ).fillna("")

        except Exception as exc:
            last_error = exc

    raise ValueError(
        f"CSV 파일을 읽을 수 없습니다: {last_error}"
    )


@st.cache_data
def load_data(file_path, file_modified):
    data = read_csv_flexibly(file_path)

    original_columns = list(data.columns)

    normalized_lookup = {
        clean_name(column): column
        for column in original_columns
    }

    rename_map = {}

    for standard_name, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            found = normalized_lookup.get(
                clean_name(alias)
            )

            if found is not None:
                rename_map[found] = standard_name
                break

    data = data.rename(columns=rename_map)

    # 첫 번째 행에 실제 열 이름이 들어간 경우 처리
    if "대학명" not in data.columns and len(data) > 0:

        first_row = [
            str(x).strip()
            for x in data.iloc[0].tolist()
        ]

        first_lookup = {
            clean_name(x): x
            for x in first_row
        }

        second_rename = {}

        for standard_name, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                found = first_lookup.get(
                    clean_name(alias)
                )

                if found is not None:
                    second_rename[found] = standard_name
                    break

        if second_rename:
            data.columns = first_row
            data = data.iloc[1:].copy()
            data = data.rename(columns=second_rename)

    if "대학명" not in data.columns:
        raise ValueError(
            "대학명 열을 찾지 못했습니다. "
            "현재 CSV에서 읽힌 열 이름: "
            + ", ".join(map(str, data.columns))
            + ". GitHub의 universities.csv가 원본 대학 정보 파일인지 "
            "확인하고 수정본의 파일로 교체해 주세요."
        )

    # 선택 열이 없어도 앱이 실행되도록 빈 열 생성
    for column in [
        "영문명", "지역", "주소", "홈페이지",
        "전화", "팩스", "대표메일"
    ]:
        if column not in data.columns:
            data[column] = ""

    data = data.fillna("")

    data["_지역정규화"] = data["지역"].map(
        normalize_region
    )

    data["_주소정규화"] = data["주소"].map(
        normalize_region
    )

    return data


# 지역 이름 통일
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


# CSV 파일 경로
DATA_FILE = (
    Path(__file__).resolve().parent
    / "universities.csv"
)


# 사이트 상단
st.markdown("""
<div class="hero">
    <h1>🎓 지역별 전문대학 검색</h1>
    <p>
        지역명을 입력하면 해당 지역의
        전문대학 정보를 찾아드립니다.
    </p>
</div>
""", unsafe_allow_html=True)


# 데이터 파일 확인
if not DATA_FILE.exists():
    st.error("universities.csv 파일이 없습니다.")

    st.info(
        "app.py와 universities.csv를 "
        "GitHub 저장소의 같은 폴더에 올려주세요."
    )

    st.stop()


# 데이터 불러오기
try:
    df = load_data(
        str(DATA_FILE),
        DATA_FILE.stat().st_mtime
    )

except Exception as error:
    st.error(f"데이터 오류: {error}")
    st.stop()


# 검색창
st.subheader("🔎 지역 검색")

with st.form("region_search"):

    query = st.text_input(
        "검색할 지역을 입력하세요.",
        placeholder="예: 서울, 경기도, 부산광역시"
    )

    search_clicked = st.form_submit_button(
        "대학 검색",
        use_container_width=True
    )


# 검색 기능
if search_clicked:

    typed = query.strip()

    if not typed:
        st.session_state["searched"] = False
        st.warning("지역명을 입력해 주세요.")

    else:
        canonical = REGION_ALIASES.get(
            typed,
            typed
        )

        key = normalize_region(canonical)
        raw_key = normalize_region(typed)

        # 지역 열에서 검색
        region_match = (
            df["_지역정규화"] == key
        )

        # 주소에서도 검색
        address_match = (
            df["_주소정규화"].str.contains(
                key,
                regex=False,
                na=False
            )
            |
            df["_주소정규화"].str.contains(
                raw_key,
                regex=False,
                na=False
            )
        )

        found = df[
            region_match | address_match
        ].copy()

        found = found.drop_duplicates(
            subset=["대학명", "주소"]
        )

        st.session_state["searched"] = True
        st.session_state["query"] = typed

        st.session_state["found"] = (
            found.drop(
                columns=[
                    "_지역정규화",
                    "_주소정규화"
                ],
                errors="ignore"
            ).to_dict("records")
        )


# 검색 결과
st.divider()
st.subheader("📋 검색 결과")


if not st.session_state.get("searched", False):

    st.info(
        "검색창에 지역명을 입력하고 "
        "대학 검색을 눌러주세요."
    )

else:

    result = pd.DataFrame(
        st.session_state.get("found", [])
    )

    searched = st.session_state.get(
        "query",
        ""
    )

    if result.empty:

        st.warning(
            f"'{searched}' 지역의 대학을 찾지 못했습니다."
        )

        st.caption(
            "검색 가능한 지역: 서울 · 경기 · 인천 · 강원 · "
            "충북 · 충남 · 대전 · 세종 · 전북 · 전남 · 광주 · "
            "경북 · 경남 · 대구 · 부산 · 울산 · 제주"
        )

    else:

        st.success(
            f"'{searched}' 검색 결과: "
            f"총 {len(result)}개 대학"
        )

        # 대학별 정보 출력
        for _, row in result.iterrows():

            with st.container(border=True):

                st.markdown(
                    f"### 🎓 {row.get('대학명', '')}"
                )

                left, right = st.columns(2)

                with left:

                    st.write(
                        f"**지역:** "
                        f"{row.get('지역', '') or '-'}"
                    )

                    st.write(
                        f"**주소:** "
                        f"{row.get('주소', '') or '-'}"
                    )

                    st.write(
                        f"**전화:** "
                        f"{row.get('전화', '') or '-'}"
                    )

                with right:

                    st.write(
                        f"**영문명:** "
                        f"{row.get('영문명', '') or '-'}"
                    )

                    st.write(
                        f"**팩스:** "
                        f"{row.get('팩스', '') or '-'}"
                    )

                    st.write(
                        f"**대표메일:** "
                        f"{row.get('대표메일', '') or '-'}"
                    )

                # 홈페이지 링크
                website = str(
                    row.get("홈페이지", "")
                ).strip()

                if website:

                    if not website.startswith(
                        ("http://", "https://")
                    ):
                        website = "https://" + website

                    st.link_button(
                        "🌐 대학 홈페이지 바로가기",
                        website
                    )

        # 검색 결과 다운로드
        st.download_button(
            "📥 검색 결과 CSV 다운로드",
            data=result.to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name=f"{searched}_전문대학목록.csv",
            mime="text/csv",
            use_container_width=True
        )


# 자료 안내
with st.expander("자료 안내"):

    st.write(
        "사용자가 제공한 한국전문대학교육협의회 "
        "대학 정보 CSV(2020년 10월 7일 기준)를 사용합니다."
    )

    st.write(
        "이 자료는 전문대학 목록이므로 "
        "서울대학교·연세대학교 등 일반 4년제 대학은 "
        "포함되어 있지 않습니다."
    )


st.caption("자료 기준일: 2020.10.07")


    
