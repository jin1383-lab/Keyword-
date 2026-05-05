import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import time
import random
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="Global Shorts Trend", layout="wide")

# 스타일 설정 (사이드바 디자인 강화)
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #fafafa; }
    section[data-testid="stSidebar"] { background-color: #161b22; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #deff9a; color: #000; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 호출 함수 (보안 및 캐싱 유지)
@st.cache_data(ttl=3600, show_spinner=False)
def get_safe_trends(keyword, cat_id, geo, timeframe):
    time.sleep(random.uniform(5, 10)) # 봇 감지 방지 지연
    try:
        pytrends = TrendReq(
            hl='ko-KR', 
            tz=540, 
            timeout=(15, 30), 
            retries=5, 
            backoff_factor=2 # 지수 백오프 적용
        )
        pytrends.build_payload([keyword], cat=cat_id, timeframe=timeframe, geo=geo, gprop='youtube')
        related = pytrends.related_queries()
        return {"status": "success", "data": related.get(keyword)}
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            return {"status": "error", "code": 429}
        return {"status": "error", "code": 500, "msg": error_msg}

# 3. 사이드바 - 모든 분석 설정 통합
st.sidebar.title("⚙️ 분석 설정")

# (1) 국가 선택
country_options = {"전세계 (Global)": "", "대한민국": "KR", "미국": "US", "일본": "JP", "영국": "GB"}
selected_country_label = st.sidebar.selectbox("대상 국가", list(country_options.keys()), index=1)
current_geo = country_options[selected_country_label]

# (2) 카테고리 선택[cite: 1]
category_info = {
    "🐶 동물": {"id": 66, "seed": "강아지"}, 
    "🎮 게임": {"id": 8, "seed": "게임"},
    "🍳 요리": {"id": 71, "seed": "레시피"}, 
    "🏃 스포츠": {"id": 20, "seed": "스포츠"},
    "🎬 영화": {"id": 34, "seed": "영화"}, 
    "🤣 코미디": {"id": 3, "seed": "유머"},
    "👗 패션": {"id": 44, "seed": "패션"}, 
    "🏠 브이로그": {"id": 28, "seed": "Vlog"}
}
selected_cat_name = st.sidebar.selectbox("콘텐츠 카테고리", list(category_info.keys()))
current_cat_id = category_info[selected_cat_name]['id']
current_seed = category_info[selected_cat_name]['seed']

# (3) 분석 기간 선택[cite: 1]
time_map = {"최근 7일": "now 7-d", "최근 30일": "today 1-m", "최근 90일": "today 3-m"}
selected_time_label = st.sidebar.selectbox("분석 기간", list(time_map.keys()), index=1)
selected_timeframe = time_map[selected_time_label]

st.sidebar.markdown("---")
run_analysis = st.sidebar.button("🚀 분석 실행")

# 4. 메인 화면 구성
st.title("🌍 Global Shorts Keyword Visualizer")
st.info(f"📍 **설정 확인**: {selected_country_label} | {selected_cat_name} | {selected_time_label}")

if run_analysis:
    with st.spinner("구글 트렌드에서 유튜브 데이터를 안전하게 가져오고 있습니다..."):
        response = get_safe_trends(current_seed, current_cat_id, current_geo, selected_timeframe)
        
        if response["status"] == "error":
            if response["code"] == 429:
                st.error("🚨 **[429 차단]** 요청이 너무 많습니다. IP를 변경(핫스팟)하거나 잠시 후 시도해 주세요.[cite: 1]")
            else:
                st.error(f"❌ 오류: {response['msg']}")
            st.stop()
            
        result = response["data"]
        if result:
            top_df, rising_df = result['top'], result['rising']
            
            # 인기 키워드 차트
            if top_df is not None and not top_df.empty:
                st.subheader(f"🏆 {selected_cat_name} 인기 키워드 (Top)")
                fig_top = px.bar(top_df.head(10), x='value', y='query', orientation='h',
                                 color='value', color_continuous_scale='Viridis')
                fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_top, use_container_width=True)

            # 급상승 키워드 차트[cite: 1]
            if rising_df is not None and not rising_df.empty:
                st.subheader(f"🔥 {selected_cat_name} 급상승 키워드 (Rising)")
                display_rising = rising_df.copy().head(10)
                display_rising['numeric_value'] = display_rising['value'].apply(lambda x: 5000 if x == 'Breakout' else x)
                fig_rising = px.bar(display_rising, x='numeric_value', y='query', orientation='h',
                                    color='numeric_value', color_continuous_scale='Reds')
                fig_rising.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_rising, use_container_width=True)
                st.caption("'Breakout'은 검색량이 전주기 대비 5000% 이상 폭증한 상태입니다.[cite: 1]")
        else:
            st.warning("분석 결과가 없습니다. 조건을 변경해 보세요.")
else:
    st.write("사이드바에서 조건을 설정한 후 **[분석 실행]** 버튼을 눌러주세요.")
