import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import time
import random
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="Global Shorts Trend", layout="wide")

# 스타일 설정
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #fafafa; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #161b22; color: white; border: 1px solid #30363d; }
    .stButton>button:hover { border-color: #deff9a; color: #deff9a; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #161b22; border-radius: 5px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 호출 함수 (429 에러 방지 및 캐싱 강화)
@st.cache_data(ttl=3600, show_spinner=False)
def get_safe_trends(keyword, cat_id, geo, timeframe):
    """구글 서버 차단을 방지하기 위한 안전한 데이터 호출 함수"""
    # 봇 감지 회피를 위한 무작위 지연 (지연 시간 증가)
    time.sleep(random.uniform(5, 10))
    
    try:
        # pytrends 초기화 (재시도 및 타임아웃 강화)
        pytrends = TrendReq(
            hl='ko-KR', 
            tz=540, 
            timeout=(15, 30), 
            retries=5, 
            backoff_factor=2
        )
        
        pytrends.build_payload(
            [keyword], 
            cat=cat_id, 
            timeframe=timeframe, 
            geo=geo, 
            gprop='youtube' # 유튜브 전용 설정
        )
        
        related = pytrends.related_queries()
        return {"status": "success", "data": related.get(keyword)}
    
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            return {"status": "error", "code": 429, "msg": "구글 서버 차단됨 (IP 교체 권장)"}
        return {"status": "error", "code": 500, "msg": error_msg}

# 3. 사이드바 및 설정 데이터
st.title("🌍 Global Shorts Keyword Finder")

# 국가 선택 (탭 형식)
st.subheader("1. 분석 국가 선택")
country_options = {"글로벌": "", "대한민국": "KR", "미국": "US", "일본": "JP"}
selected_country_label = st.tabs(list(country_options.keys()))

# 탭 선택 결과 저장
for i, tab in enumerate(selected_country_label):
    with tab:
        current_geo = list(country_options.values())[i]
        st.caption(f"선택된 지역 코드: {current_geo if current_geo else 'Global'}")

# 카테고리 정보
category_info = {
    "🐶 동물": {"id": 66, "seed": "강아지"}, "🎮 게임": {"id": 8, "seed": "게임"},
    "🍳 요리": {"id": 71, "seed": "레시피"}, "🏃 스포츠": {"id": 20, "seed": "스포츠"},
    "🎬 영화": {"id": 34, "seed": "영화"}, "🤣 코미디": {"id": 3, "seed": "유머"},
    "👗 패션": {"id": 44, "seed": "패션"}, "🏠 브이로그": {"id": 28, "seed": "Vlog"}
}

# 기간 설정
time_map = {"최근 7일": "now 7-d", "최근 30일": "today 1-m", "최근 90일": "today 3-m"}
selected_time_label = st.sidebar.selectbox("분석 기간", list(time_map.keys()), index=1)
selected_timeframe = time_map[selected_time_label]

# 카테고리 선택
st.subheader("2. 카테고리 선택")
cat_cols = st.columns(4)
if 'selected_cat' not in st.session_state:
    st.session_state.selected_cat = 0
    st.session_state.cat_name = "전체"

for i, (name, info) in enumerate(category_info.items()):
    if cat_cols[i % 4].button(name):
        st.session_state.selected_cat = info['id']
        st.session_state.seed = info['seed']
        st.session_state.cat_name = name

st.info(f"선택: **{st.session_state.cat_name}** | 기간: **{selected_time_label}**")

# 4. 분석 실행 섹션
if st.button("🚀 유튜브 트렌드 분석 시작", key="run_btn"):
    seed_kw = st.session_state.get('seed', '유튜브')
    
    with st.spinner("구글 트렌드 데이터를 안전하게 요청 중입니다. 약 10초가 소요됩니다..."):
        response = get_safe_trends(
            seed_kw, 
            st.session_state.selected_cat, 
            current_geo, 
            selected_timeframe
        )
        
        if response["status"] == "error":
            if response["code"] == 429:
                st.error("🚨 **[429 차단 발생]** 너무 잦은 요청으로 구글 서버가 일시적으로 차단했습니다.")
                st.warning("💡 **해결 방법**: 휴대폰 핫스팟으로 연결하여 IP를 변경하거나, 20분 뒤에 다시 시도해 주세요.")
            else:
                st.error(f"❌ 오류 발생: {response['msg']}")
            st.stop()
            
        result = response["data"]
        if result:
            st.markdown("---")
            top_df, rising_df = result['top'], result['rising']
            
            # 시각화 섹션 (인기 검색어)
            if top_df is not None and not top_df.empty:
                st.subheader(f"🏆 {st.session_state.cat_name} 인기 검색어 TOP 10")
                fig_top = px.bar(top_df.head(10), x='value', y='query', orientation='h',
                                 color='value', color_continuous_scale='Viridis',
                                 labels={'value': '관심도', 'query': '키워드'})
                fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_top, use_container_width=True)

            # 시각화 섹션 (급상승 검색어)
            if rising_df is not None and not rising_df.empty:
                st.subheader(f"🔥 {st.session_state.cat_name} 급상승 검색어")
                display_rising = rising_df.copy().head(10)
                display_rising['numeric_value'] = display_rising['value'].apply(lambda x: 5000 if x == 'Breakout' else x)
                fig_rising = px.bar(display_rising, x='numeric_value', y='query', orientation='h',
                                    color='numeric_value', color_continuous_scale='Reds',
                                    labels={'numeric_value': '상승률', 'query': '키워드'})
                fig_rising.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_rising, use_container_width=True)
                st.caption("'Breakout'은 검색량이 전주기 대비 폭증(5000%↑)한 상태입니다.[cite: 1]")
        else:
            st.warning("분석 결과가 없습니다. 다른 카테고리나 기간을 선택해 보세요.")
