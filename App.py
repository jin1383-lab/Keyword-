import streamlit as st
from pytrends.request import TrendReq
import pandas as pd

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Shorts Keyword Finder", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #fafafa; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #161b22; color: white; border: 1px solid #30363d; }
    .stButton>button:hover { border-color: #deff9a; color: #deff9a; }
    .css-10trblm { color: #deff9a !important; } /* 타이틀 색상 */
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Shorts Keyword Finder")
st.caption("본 도구는 Google Trends의 **YouTube 검색 데이터**만을 실시간으로 분석합니다.[span_0](start_span)[span_0](end_span)")

# 2. 유튜브 카테고리 맵핑 (구글 트렌드 카테고리 ID)
category_map = {
    "🎮 게임": 8, "🎵 음악": 35, "🍳 요리": 71, "🐶 반려동물": 66,
    "🏃 스포츠": 20, "🎬 영화/애니": 34, "💡 지식/과학": 174, "🤣 코미디": 3,
    "👗 뷰티/패션": 44, "🚗 자동차": 47, "✈️ 여행": 67, "🏠 일상/Vlog": 28
}

# 3. 레이아웃: 카테고리 선택 (단추형)
st.subheader("1. 카테고리 선택")
cols = st.columns(4)
selected_cat_name = None

for i, (name, cat_id) in enumerate(category_map.items()):
    if cols[i % 4].button(name):
        st.session_state.selected_cat = cat_id
        st.session_state.cat_name = name

current_cat = st.session_state.get('selected_cat', 0)
current_cat_name = st.session_state.get('cat_name', "전체")
st.info(f"현재 선택된 카테고리: **{current_cat_name}**")

# 4. 키워드 입력 및 분석
st.subheader("2. 키워드 입력")
col_input, col_btn = st.columns([4, 1])
search_kw = col_input.text_input("분석할 키워드를 입력하세요", placeholder="예: 레시피, 운동법, 언박싱")

if col_btn.button("분석 실행") or search_kw:
    if not search_kw:
        st.warning("키워드를 입력해주세요.")
    else:
        with st.spinner('유튜브 트렌드 데이터를 가져오는 중...'):
            try:
                # pytrends 설정[span_1](start_span)[span_1](end_span)
                pytrends = TrendReq(hl='ko-KR', tz=540)
                
                # gprop='youtube' 설정으로 유튜브 데이터만 타겟팅[span_2](start_span)[span_2](end_span)
                pytrends.build_payload(
                    [search_kw], 
                    cat=current_cat, 
                    timeframe='today 3-m', 
                    geo='KR', 
                    gprop='youtube'
                )

                # 관련 검색어 가져오기[span_3](start_span)[span_3](end_span)
                related_queries = pytrends.related_queries()
                
                if related_queries.get(search_kw):
                    top_df = related_queries[search_kw]['top']
                    rising_df = related_queries[search_kw]['rising']

                    st.markdown("---")
                    st.subheader(f"📊 '{search_kw}' 유튜브 분석 리포트")
                    
                    res_col1, res_col2 = st.columns(2)

                    with res_col1:
                        st.markdown("### 🏆 인기(Top) 키워드")
                        if top_df is not None:
                            st.table(top_df.rename(columns={'query': '키워드', 'value': '관심도'}).head(10))
                        else:
                            st.write("인기 키워드 데이터가 없습니다.")

                    with res_col2:
                        st.markdown("### 🔥 급상승(Rising) 키워드")
                        if rising_df is not None:
                            # 급상승 수치를 보기 좋게 변환
                            rising_df['value'] = rising_df['value'].apply(lambda x: f"↑{x}%" if isinstance(x, int) else x)
                            st.table(rising_df.rename(columns={'query': '키워드', 'value': '상승률'}).head(10))
                        else:
                            st.write("급상승 키워드 데이터가 없습니다.")
                else:
                    st.error("충분한 트렌드 데이터가 없습니다. 다른 키워드를 입력해 보세요.")

            except Exception as e:
                st.error(f"오류 발생: {e}")
