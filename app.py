import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import time
import random
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="YouTube Global Trend Master", layout="wide")

# 스타일 설정
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #fafafa; }
    section[data-testid="stSidebar"] { background-color: #161b22; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #deff9a; color: #000; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #c4f06d; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 호출 함수 (보안 및 캐싱)
@st.cache_data(ttl=3600, show_spinner=False)
def get_safe_trends(keyword, cat_id, geo, timeframe):
    time.sleep(random.uniform(5, 8)) # 차단 방지를 위한 랜덤 지연
    try:
        pytrends = TrendReq(
            hl='ko-KR', 
            tz=540, 
            timeout=(15, 30), 
            retries=5, 
            backoff_factor=2
        )
        pytrends.build_payload([keyword], cat=cat_id, timeframe=timeframe, geo=geo, gprop='youtube')
        related = pytrends.related_queries()
        return {"status": "success", "data": related.get(keyword)}
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            return {"status": "error", "code": 429}
        return {"status": "error", "code": 500, "msg": error_msg}

# 3. 사이드바 - 분석 설정
st.sidebar.title("🛠️ YouTube 설정")

# (1) 국가 선택
country_options = {
    "전세계 (Global)": "", 
    "대한민국": "KR", 
    "미국": "US", 
    "일본": "JP", 
    "영국": "GB", 
    "인도": "IN", 
    "브라질": "BR"
}
selected_country_label = st.sidebar.selectbox("🎯 대상 국가", list(country_options.keys()), index=1)
current_geo = country_options[selected_country_label]

# (2) 유튜브 공식 15개 카테고리 매핑
# 구글 트렌드 카테고리 ID를 유튜브 표준에 맞춰 구성했습니다.
category_info = {
    "🎬 영화/애니메이션": {"id": 34, "seed": "영화"},
    "🚗 자동차/탈것": {"id": 47, "seed": "자동차"},
    "🎵 음악": {"id": 35, "seed": "음악"},
    "🐶 반려동물/동물": {"id": 66, "seed": "강아지"},
    "🏃 스포츠": {"id": 20, "seed": "스포츠"},
    "✈️ 여행/이벤트": {"id": 67, "seed": "여행"},
    "🎮 게임": {"id": 8, "seed": "게임"},
    "🏠 인물/브이로그": {"id": 28, "seed": "브이로그"},
    "🤣 코미디": {"id": 3, "seed": "유머"},
    "📺 엔터테인먼트": {"id": 24, "seed": "예능"},
    "📰 뉴스/정치": {"id": 16, "seed": "뉴스"},
    "💡 노하우/스타일": {"id": 44, "seed": "패션"},
    "📖 교육": {"id": 5, "seed": "교육"},
    "🔬 과학기술": {"id": 174, "seed": "과학"},
    "📢 비영리/사회운동": {"id": 93, "seed": "기부"}
}
selected_cat_name = st.sidebar.selectbox("📂 유튜브 카테고리", list(category_info.keys()))
current_cat_id = category_info[selected_cat_name]['id']
current_seed = category_info[selected_cat_name]['seed']

# (3) 분석 기간 선택
time_map = {
    "최근 7일": "now 7-d", 
    "최근 30일": "today 1-m", 
    "최근 90일": "today 3-m", 
    "최근 12개월": "today 12-m"
}
selected_time_label = st.sidebar.selectbox("📅 분석 기간", list(time_map.keys()), index=1)
selected_timeframe = time_map[selected_time_label]

st.sidebar.markdown("---")
run_analysis = st.sidebar.button("🚀 분석 실행")

# 4. 메인 화면 구성
st.title("📊 YouTube Shorts Global Trend")
st.markdown(f"현재 설정: **{selected_country_label}** | **{selected_cat_name}** | **{selected_time_label}**")

if run_analysis:
    with st.spinner("구글 트렌드 데이터를 분석 중입니다..."):
        response = get_safe_trends(current_seed, current_cat_id, current_geo, selected_timeframe)
        
        if response["status"] == "error":
            if response["code"] == 429:
                st.error("🚨 **차단 알림**: 너무 많은 요청이 발생했습니다. IP 변경(핫스팟) 후 시도해 주세요.")
            else:
                st.error(f"❌ 오류: {response['msg']}")
            st.stop()
            
        result = response["data"]
        if result:
            top_df, rising_df = result['top'], result['rising']
            
            # 인기 키워드 차트
            st.subheader(f"🏆 {selected_cat_name} 인기 키워드")
            if top_df is not None and not top_df.empty:
                fig_top = px.bar(top_df.head(15), x='value', y='query', orientation='h',
                                 color='value', color_continuous_scale='Blues',
                                 labels={'value': '검색 관심도', 'query': '키워드'})
                fig_top.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
                st.plotly_chart(fig_top, use_container_width=True)
            else:
                st.info("데이터가 충분하지 않습니다.")

            # 급상승 키워드 차트
            st.subheader(f"🔥 {selected_cat_name} 급상승 키워드")
            if rising_df is not None and not rising_df.empty:
                display_rising = rising_df.copy().head(15)
                display_rising['numeric_value'] = display_rising['value'].apply(lambda x: 5000 if x == 'Breakout' else x)
                fig_rising = px.bar(display_rising, x='numeric_value', y='query', orientation='h',
                                    color='numeric_value', color_continuous_scale='Reds',
                                    labels={'numeric_value': '상승률 (%)', 'query': '키워드'})
                fig_rising.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
                st.plotly_chart(fig_rising, use_container_width=True)
            else:
                st.info("급상승 데이터가 없습니다.")
        else:
            st.warning("분석 결과가 없습니다. 다른 기간을 선택해 보세요.")
else:
    st.info("사이드바에서 카테고리와 국가를 선택한 후 **[분석 실행]** 버튼을 눌러주세요.")
