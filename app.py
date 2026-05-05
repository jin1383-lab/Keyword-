import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import time
import random
import plotly.express as px
from io import BytesIO  # 엑셀 파일 다운로드를 위한 메모리 버퍼

# 1. 페이지 설정
st.set_page_config(page_title="YouTube Trend to Excel", layout="wide")

# 2. 데이터 호출 함수 (보안 및 캐싱)
@st.cache_data(ttl=3600, show_spinner=False)
def get_safe_trends(keyword, cat_id, geo, timeframe):
    time.sleep(random.uniform(5, 8))
    try:
        pytrends = TrendReq(hl='ko-KR', tz=540, timeout=(15, 30), retries=5, backoff_factor=2)
        pytrends.build_payload([keyword], cat=cat_id, timeframe=timeframe, geo=geo, gprop='youtube')
        related = pytrends.related_queries()
        return {"status": "success", "data": related.get(keyword)}
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg: return {"status": "error", "code": 429}
        return {"status": "error", "code": 500, "msg": error_msg}

# 3. 사이드바 설정 (이전과 동일)
st.sidebar.title("🛠️ 분석 설정")
country_options = {"전세계 (Global)": "", "대한민국": "KR", "미국": "US", "일본": "JP", "영국": "GB"}
selected_country_label = st.sidebar.selectbox("🎯 대상 국가", list(country_options.keys()), index=1)
current_geo = country_options[selected_country_label]

category_info = {
    "🎬 영화/애니메이션": {"id": 34, "seed": "영화"}, "🚗 자동차/탈것": {"id": 47, "seed": "자동차"},
    "🎵 음악": {"id": 35, "seed": "음악"}, "🐶 반려동물/동물": {"id": 66, "seed": "강아지"},
    "🏃 스포츠": {"id": 20, "seed": "스포츠"}, "✈️ 여행/이벤트": {"id": 67, "seed": "여행"},
    "🎮 게임": {"id": 8, "seed": "게임"}, "🏠 인물/브이로그": {"id": 28, "seed": "브이로그"},
    "🤣 코미디": {"id": 3, "seed": "유머"}, "📺 엔터테인먼트": {"id": 24, "seed": "예능"},
    "📰 뉴스/정치": {"id": 16, "seed": "뉴스"}, "💡 노하우/스타일": {"id": 44, "seed": "패션"},
    "📖 교육": {"id": 5, "seed": "교육"}, "🔬 과학기술": {"id": 174, "seed": "과학"},
    "📢 비영리/사회운동": {"id": 93, "seed": "기부"}
}
selected_cat_name = st.sidebar.selectbox("📂 유튜브 카테고리", list(category_info.keys()))
current_cat_id = category_info[selected_cat_name]['id']
current_seed = category_info[selected_cat_name]['seed']

time_map = {"최근 7일": "now 7-d", "최근 30일": "today 1-m", "최근 90일": "today 3-m"}
selected_time_label = st.sidebar.selectbox("📅 분석 기간", list(time_map.keys()), index=1)
selected_timeframe = time_map[selected_time_label]

st.sidebar.markdown("---")
run_analysis = st.sidebar.button("🚀 분석 및 엑셀 생성")

# 4. 메인 화면 및 분석 로직
st.title("📊 YouTube Trend Excel Exporter")

if run_analysis:
    with st.spinner("데이터를 추출하여 엑셀 형식으로 변환 중입니다..."):
        response = get_safe_trends(current_seed, current_cat_id, current_geo, selected_timeframe)
        
        if response["status"] == "error":
            st.error("🚨 구글 서버 차단 또는 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
            st.stop()
            
        result = response["data"]
        if result:
            top_df = result['top']
            rising_df = result['rising']

            # --- 엑셀 파일 생성 로직 (메모리 버퍼 사용) ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                if top_df is not None:
                    top_df.to_excel(writer, sheet_name='인기 검색어', index=False)
                if rising_df is not None:
                    rising_df.to_excel(writer, sheet_name='급상승 검색어', index=False)
            processed_data = output.getvalue()

            # 다운로드 버튼
            st.download_button(
                label="📥 분석 결과 엑셀 다운로드 (.xlsx)",
                data=processed_data,
                file_name=f"YT_Trend_{selected_country_label}_{selected_cat_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.markdown("---")

            # 화면에 엑셀 형식(Dataframe)으로 보여주기
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📑 인기 검색어 (Top)")
                if top_df is not None:
                    st.dataframe(top_df, use_container_width=True) # 엑셀 시트 형태 UI
                else: st.write("데이터 없음")

            with col2:
                st.subheader("📈 급상승 검색어 (Rising)")
                if rising_df is not None:
                    st.dataframe(rising_df, use_container_width=True)
                else: st.write("데이터 없음")
        else:
            st.warning("결과 데이터가 없습니다.")
else:
    st.info("왼쪽 설정을 확인한 후 버튼을 눌러주세요.")
