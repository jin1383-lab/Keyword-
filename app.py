import streamlit as st
import googleapiclient.discovery
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime, timedelta
from collections import Counter
import re

# 1. 페이지 설정
st.set_page_config(page_title="Global Shorts Finder V1", page_icon="🌎", layout="wide")
st.title("🌎 글로벌 쇼츠 탐색 및 기간별 트렌드 분석기")

# 2. 사이드바 설정
st.sidebar.header("⚙️ 검색 설정")
api_key = st.sidebar.text_input("YouTube API Key", type="password")

# [국가 선택 필터]
country_option = st.sidebar.selectbox(
    "📍 검색 대상 국가",
    options=["None", "US", "KR", "JP"],
    format_func=lambda x: {"None": "글로벌 (전체)", "US": "미국", "KR": "한국", "JP": "일본"}[x]
)

# [신규: 기간 설정 필터]
period_option = st.sidebar.selectbox(
    "📅 업로드 기간 설정",
    options=["3days", "1week", "1month", "3months", "6months", "1year", "all"],
    index=2, # 기본값 '한달'
    format_func=lambda x: {
        "3days": "최근 3일",
        "1week": "최근 1주일",
        "1month": "최근 한달",
        "3months": "최근 3개월",
        "6months": "최근 6개월",
        "1year": "최근 1년",
        "all": "전체 기간"
    }[x]
)

st.sidebar.subheader("🔍 채널 필터링 조건")
min_sub = st.sidebar.number_input("최소 구독자 수", value=1000, step=1000)
min_views = st.sidebar.number_input("최소 누적 조회수", value=50000, step=10000)

# --- 기간 계산 함수 ---
def get_published_after(option):
    if option == "all":
        return None
    now = datetime.utcnow()
    delta_map = {
        "3days": timedelta(days=3),
        "1week": timedelta(weeks=1),
        "1month": timedelta(days=30),
        "3months": timedelta(days=90),
        "6months": timedelta(days=180),
        "1year": timedelta(days=365)
    }
    target_date = now - delta_map[option]
    # 유튜브 API가 요구하는 RFC 3339 형식 (예: 2024-01-01T00:00:00Z)
    return target_date.strftime('%Y-%m-%dT%H:%M:%SZ')

if api_key:
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    user_input = st.text_input("분석할 키워드 또는 채널명", placeholder="예: 해외이슈 쇼츠")

    if st.button("데이터 분석 시작"):
        try:
            with st.spinner(f'데이터 분석 중... (기간: {period_option})'):
                # [STEP 1] 검색 조건 설정
                published_after = get_published_after(period_option)
                
                search_params = {
                    "part": "snippet",
                    "q": user_input,
                    "type": "video",
                    "maxResults": 25,
                    "order": "viewCount" # 조회수 높은 순으로 정렬
                }
                
                if country_option != "None":
                    search_params["regionCode"] = country_option
                if published_after:
                    search_params["publishedAfter"] = published_after

                search_res = youtube.search().list(**search_params).execute()
                
                # 중복 없는 채널 ID 추출
                candidate_ids = list(set([item['snippet']['channelId'] for item in search_res['items']]))

                # [STEP 2] 채널 상세 정보 수집
                if not candidate_ids:
                    st.warning("해당 기간 내에 검색된 데이터가 없습니다.")
                else:
                    stats_res = youtube.channels().list(
                        part="statistics,snippet",
                        id=",".join(candidate_ids)
                    ).execute()

                    valid_channels = []
                    for ch in stats_res['items']:
                        stat = ch['statistics']
                        sub = int(stat.get('subscriberCount', 0))
                        view = int(stat.get('viewCount', 0))

                        if sub >= min_sub and view >= min_views:
                            valid_channels.append({
                                "title": ch['snippet']['title'],
                                "id": ch['id'],
                                "thumb": ch['snippet']['thumbnails']['medium']['url'],
                                "sub": sub, "view": view
                            })

                    # [STEP 3] 결과 출력
                    if valid_channels:
                        st.subheader(f"✅ 필터 통과 채널 (검색 기간: {period_option})")
                        cols = st.columns(3)
                        for idx, ch in enumerate(valid_channels):
                            with cols[idx % 3]:
                                st.image(ch['thumb'], use_container_width=True)
                                st.markdown(f"**[{ch['title']}](https://www.youtube.com/channel/{ch['id']})**")
                                st.caption(f"👥 {ch['sub']:,}명 | 👁️ {ch['view']:,}회")
                                st.divider()
                    else:
                        st.error("설정한 채널 지표(구독자/조회수)를 만족하는 채널이 없습니다.")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
else:
    st.info("API Key를 입력하면 도구가 활성화됩니다.")
