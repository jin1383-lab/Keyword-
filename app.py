import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import time
import random
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="Keyword Trend Analyzer", layout="wide")

# 스타일 설정
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #fafafa; }
    section[data-testid="stSidebar"] { background-color: #161b22; }
    /* 버튼 스타일 */
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        background-color: #deff9a; 
        color: #000; 
        font-weight: bold; 
        border: none;
        height: 3em;
    }
    /* 엑셀 느낌의 데이터프레임 스타일 */
    [data-testid="stDataFrame"] {
        border: 1px solid #30363d;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 호출 함수 (보안 및 캐싱)
@st.cache_data(ttl=3600, show_spinner=False)
def get_keyword_trends(keyword, geo, timeframe):
    """사용자가 입력한 키워드를 기반으로 유튜브 트렌드 추출"""
    time.sleep(random.uniform(3, 6)) # 차단 방지용 지연
    try:
        pytrends = TrendReq(
            hl='ko-KR', 
            tz=540, 
            timeout=(15, 30), 
            retries=5, 
            backoff_factor=2 # 429 에러 대응을 위한 지수 백오프
        )
        # 카테고리 0(전체)으로 설정하여 키워드 범용성 확보
        pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo, gprop='youtube')
        related = pytrends.related_queries()
        return {"status": "success", "data": related.get(keyword)}
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            return {"status": "error", "code": 429}
        return {"status": "error", "code": 500, "msg": error_msg}

# 3. 사이드바 - 분석 설정
st.sidebar.title("🔍 검색 설정")

# (1) 키워드 입력 (카테고리 대체)
search_keyword = st.sidebar.text_input("분석할 키워드 입력", placeholder="예: 레시피, 다이어트, 캠핑", help="유튜브 검색 트렌드를 파악할 핵심 키워드를 입력하세요.")

# (2) 국가 선택
country_options = {"대한민국": "KR", "전세계": "", "미국": "US", "일본": "JP", "영국": "GB"}
selected_country = st.sidebar.selectbox("대상 국가", list(country_options.keys()), index=0)
current_geo = country_options[selected_country]

# (3) 기간 설정 (1주 ~ 1년)
time_map = {
    "1주일": "now 7-d", 
    "1달": "today 1-m", 
    "3개월": "today 3-m", 
    "6개월": "today 6-m", 
    "1년": "today 12-m"
}
selected_time_label = st.sidebar.select_slider("분석 기간 선택", options=list(time_map.keys()), value="1달")
selected_timeframe = time_map[selected_time_label]

st.sidebar.markdown("---")
run_analysis = st.sidebar.button("🚀 분석 실행")

# 4. 메인 화면 구성
st.title("📊 Keyword Search Trend Master")
st.markdown(f"현재 검색어: **{search_keyword if search_keyword else '없음'}** | 국가: **{selected_country}** | 기간: **{selected_time_label}**")

if run_analysis:
    if not search_keyword:
        st.warning("분석할 키워드를 입력해 주세요.")
        st.stop()

    with st.spinner(f"'{search_keyword}' 관련 유튜브 데이터를 불러오는 중..."):
        response = get_keyword_trends(search_keyword, current_geo, selected_timeframe)
        
        if response["status"] == "error":
            if response["code"] == 429:
                st.error("🚨 구글 서버에서 일시적인 차단이 발생했습니다. IP를 변경(핫스팟 등)하거나 잠시 후 시도해 주세요.")
            else:
                st.error(f"❌ 오류: {response['msg']}")
            st.stop()
            
        result = response["data"]
        if result:
            top_df = result['top']
            rising_df = result['rising']

            # --- 결과 출력 섹션 (엑셀 형식 UI) ---
            st.markdown("---")
            
            # (1) 인기 검색어 섹션
            st.subheader(f"🏆 '{search_keyword}' 인기 관련 검색어 (Top)")
            st.caption("해당 기간 동안 가장 많이 검색된 연관 키워드입니다.")
            if top_df is not None and not top_df.empty:
                # 시각화 차트
                fig_top = px.bar(top_df.head(10), x='value', y='query', orientation='h',
                                 color='value', color_continuous_scale='Blues')
                fig_top.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
                st.plotly_chart(fig_top, use_container_width=True)
                
                # 엑셀 형식 표 출력
                st.dataframe(top_df.rename(columns={'query': '연관 키워드', 'value': '검색 관심도(0-100)'}), use_container_width=True)
            else:
                st.info("데이터가 충분하지 않습니다.")

            st.markdown("---")

            # (2) 급상승 검색어 섹션
            st.subheader(f"🔥 '{search_keyword}' 급상승 관련 검색어 (Rising)")
            st.caption("전기 대비 검색량이 급격히 늘어난 키워드입니다.")
            if rising_df is not None and not rising_df.empty:
                # 엑셀 형식 표 출력 (차트보다 표를 강조하기 위해 상단 배치)
                display_rising = rising_df.copy()
                st.dataframe(display_rising.rename(columns={'query': '연관 키워드', 'value': '상승률'}), use_container_width=True)
                
                # 시각화 차트
                display_rising['numeric_value'] = display_rising['value'].apply(lambda x: 5000 if x == 'Breakout' else x)
                fig_rising = px.bar(display_rising.head(10), x='numeric_value', y='query', orientation='h',
                                    color='numeric_value', color_continuous_scale='Reds')
                fig_rising.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
                st.plotly_chart(fig_rising, use_container_width=True)
            else:
                st.info("급상승 데이터가 없습니다.")
        else:
            st.warning("연관된 분석 결과가 없습니다. 검색어를 더 포괄적인 단어로 바꿔보세요.")
else:
    st.info("왼쪽 사이드바에서 **키워드**를 입력하고 **[분석 실행]**을 눌러주세요.")
