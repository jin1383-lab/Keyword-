import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import time
import random
import plotly.express as px  # 차트 시각화를 위한 라이브러리

# 페이지 설정
st.set_page_config(page_title="Shorts Trend Visualizer", layout="wide")

# 1. 유튜브 전용 카테고리 설정
category_info = {
    "🐶 동물": {"id": 66, "seed": "강아지 고양이"},
    "🎮 게임": {"id": 8, "seed": "게임"},
    "🍳 요리": {"id": 71, "seed": "레시피"},
    "🏃 스포츠": {"id": 20, "seed": "스포츠"},
    "🎬 영화": {"id": 34, "seed": "영화"},
    "🤣 코미디": {"id": 3, "seed": "유머"},
    "👗 패션": {"id": 44, "seed": "패션"},
    "🏠 브이로그": {"id": 28, "seed": "Vlog"}
}

# 2. 데이터 호출 함수 (캐싱 적용)
@st.cache_data(ttl=3600)
def get_trends_data(cat_id, seed_keyword, timeframe):
    time.sleep(random.uniform(2, 4)) # 차단 방지 로직
    try:
        pytrends = TrendReq(hl='ko-KR', tz=540, retries=3, backoff_factor=1)
        pytrends.build_payload(
            [seed_keyword], 
            cat=cat_id, 
            timeframe=timeframe, 
            geo='KR', 
            gprop='youtube' # 유튜브 전용 필터
        )
        return pytrends.related_queries().get(seed_keyword)
    except Exception as e:
        return str(e)

# 3. 사이드바 - 검색 설정
st.sidebar.title("⚙️ 검색 설정")
selected_cat_name = st.sidebar.selectbox("카테고리 선택", list(category_info.keys()))
time_option = st.sidebar.radio(
    "분석 기간 선택",
    ["최근 7일", "최근 30일", "최근 90일", "최근 12개월"],
    index=1
)

# 구글 트렌드 API용 기간 파라미터 변환
time_map = {
    "최근 7일": "now 7-d",
    "최근 30일": "today 1-m",
    "최근 90일": "today 3-m",
    "최근 12개월": "today 12-m"
}
selected_timeframe = time_map[time_option]

# 4. 메인 화면 구성
st.title("📈 Shorts Keyword Visualizer")
st.write(f"현재 **{selected_cat_name}** 카테고리의 **{time_option}** 유튜브 검색 데이터를 분석합니다.[cite: 1]")

if st.button(f"{selected_cat_name} 트렌드 분석 시작"):
    cat_id = category_info[selected_cat_name]['id']
    seed_kw = category_info[selected_cat_name]['seed']
    
    with st.spinner("유튜브 데이터를 분석 중입니다..."):
        result = get_trends_data(cat_id, seed_kw, selected_timeframe)
        
        if isinstance(result, dict):
            # 데이터 프레임 준비
            top_df = result['top']
            rising_df = result['rising']

            # --- 인기 검색어 섹션 ---
            st.markdown("---")
            st.subheader(f"🏆 {selected_cat_name} 인기 검색어 TOP 10")
            if top_df is not None and not top_df.empty:
                # 차트 생성 (Plotly)[cite: 1]
                fig_top = px.bar(
                    top_df.head(10), 
                    x='value', 
                    y='query', 
                    orientation='h',
                    title="검색 관심도 (0-100)",
                    labels={'value': '관심도', 'query': '키워드'},
                    color='value',
                    color_continuous_scale='Viridis'
                )
                fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_top, use_container_width=True)
            else:
                st.info("데이터가 충분하지 않습니다.")

            # --- 급상승 검색어 섹션 ---
            st.markdown("---")
            st.subheader(f"🔥 {selected_cat_name} 급상승 검색어 TOP 10")
            if rising_df is not None and not rising_df.empty:
                # 급상승 수치가 'Breakout'인 경우 그래프 표시를 위해 임의의 높은 값 할당[cite: 1]
                display_rising = rising_df.copy().head(10)
                display_rising['numeric_value'] = display_rising['value'].apply(
                    lambda x: 5000 if x == 'Breakout' else x
                )
                
                fig_rising = px.bar(
                    display_rising, 
                    x='numeric_value', 
                    y='query', 
                    orientation='h',
                    title="전기 대비 상승률 (%)",
                    labels={'numeric_value': '상승률', 'query': '키워드'},
                    color='numeric_value',
                    color_continuous_scale='Reds'
                )
                fig_rising.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_rising, use_container_width=True)
                st.caption("'Breakout'은 검색량이 전주기 대비 5000% 이상 폭증한 상태를 의미합니다.[cite: 1]")
            else:
                st.info("급상승 데이터가 없습니다.")
        else:
            st.error(f"오류가 발생했습니다: {result}[cite: 1]")
