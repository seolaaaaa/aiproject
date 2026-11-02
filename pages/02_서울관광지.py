
import streamlit as st
import folium
from streamlit_folium import st_folium

# 페이지 설정
st.set_page_config(
    page_title="서울 관광지 TOP 10",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ 서울 관광지 TOP 10")
st.caption(
    "외국인 여행객에게 잘 알려진 서울의 대표 명소를 "
    "지도에서 확인해 보세요!"
)

st.info(
    "아래 목록은 대표 관광지 추천이며, "
    "공식 방문객 수에 따른 순위는 아닙니다."
)

# 관광지 정보
places = [
    {
        "name": "경복궁",
        "lat": 37.5796,
        "lon": 126.9770,
        "desc": "조선 왕조의 대표 궁궐로, 전통 건축과 수문장 교대식을 볼 수 있어요."
    },
    {
        "name": "N서울타워",
        "lat": 37.5512,
        "lon": 126.9882,
        "desc": "남산 정상 부근의 전망 명소로 서울 도심을 한눈에 감상할 수 있어요."
    },
    {
        "name": "명동",
        "lat": 37.5636,
        "lon": 126.9850,
        "desc": "쇼핑과 길거리 음식으로 유명한 번화가예요."
    },
    {
        "name": "북촌한옥마을",
        "lat": 37.5826,
        "lon": 126.9830,
        "desc": "전통 한옥이 모여 있는 동네로 골목 산책과 한옥 풍경을 즐길 수 있어요."
    },
    {
        "name": "인사동",
        "lat": 37.5742,
        "lon": 126.9856,
        "desc": "전통 공예품, 갤러리, 찻집을 만날 수 있는 문화 거리예요."
    },
    {
        "name": "창덕궁",
        "lat": 37.5794,
        "lon": 126.9910,
        "desc": "유네스코 세계유산으로 지정된 궁궐이며 아름다운 후원으로 유명해요."
    },
    {
        "name": "홍대거리",
        "lat": 37.5563,
        "lon": 126.9236,
        "desc": "젊은 문화와 공연, 개성 있는 상점과 카페가 모인 거리예요."
    },
    {
        "name": "동대문디자인플라자(DDP)",
        "lat": 37.5671,
        "lon": 127.0095,
        "desc": "독특한 곡선형 건축물과 전시·디자인 행사가 열리는 복합문화공간이에요."
    },
    {
        "name": "광장시장",
        "lat": 37.5701,
        "lon": 126.9997,
        "desc": "빈대떡과 다양한 한국 길거리 음식을 맛볼 수 있는 전통시장이에요."
    },
    {
        "name": "롯데월드",
        "lat": 37.5111,
        "lon": 127.0982,
        "desc": "실내외 놀이공원과 쇼핑·전망 시설을 함께 즐길 수 있는 인기 명소예요."
    }
]

# 서울 지도 생성
m = folium.Map(
    location=[37.5665, 126.9780],
    zoom_start=11,
    tiles="OpenStreetMap"
)

# 지도에 관광지 마커 표시
for i, place in enumerate(places, start=1):

    popup_html = (
        f"<b>{i}. {place['name']}</b><br>"
        f"{place['desc']}"
    )

    folium.Marker(
        location=[place["lat"], place["lon"]],
        tooltip=f"{i}. {place['name']}",
        popup=folium.Popup(
            popup_html,
            max_width=300
        ),
        icon=folium.DivIcon(
            html=f"""
            <div style="
                background:#2563eb;
                color:white;
                border-radius:50%;
                width:28px;
                height:28px;
                display:flex;
                align-items:center;
                justify-content:center;
                font-weight:bold;
                border:2px solid white;
                box-shadow:0 1px 4px #555;
            ">
                {i}
            </div>
            """
        )
    ).add_to(m)

# 지도 출력
st.subheader("📍 서울 관광지 지도")

st_folium(
    m,
    use_container_width=True,
    height=520,
    returned_objects=[]
)

# 관광지 설명
st.subheader("📖 관광지 간단 소개")

# 두 개의 열로 관광지 표시
cols = st.columns(2)

for i, place in enumerate(places):

    with cols[i % 2]:

        st.markdown(
            f"### {i + 1}. {place['name']}"
        )

        st.write(place["desc"])

        st.divider()
