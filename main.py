import streamlit as st
st.title('나의 첫 웹사이트')
a=st.text_input('이름을 입력하시오')
b=st.selectbox('좋아하는 디저트를 선택하시용',['딸기케이크','딸기 타르트','딸기 컵케이크','딸기 머핀'])
if st.button('인사말 생성'):
  st.write('반갑습니다!')
