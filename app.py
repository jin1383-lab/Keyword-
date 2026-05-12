import streamlit as st
import googleapiclient.discovery
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime, timedelta
from collections import Counter
import re

# 1. 페이지 설정
st.set_page_config(page_title="Global Shorts Finder V1", page_icon="🌎", layout="wide")
st.title("🌎 글로벌 쇼츠 탐색 및 정밀 필터 분석기")

# 2. 사이드바 설정
st.sidebar.header("⚙️ 검색 및 필터 설정")
api_key = st.sidebar.text_input("YouTube API Key", type="password")

# [국가 및 기간 설정]
country_option = st.sidebar.selectbox(
    "📍 검색 대상 국가",
    options=["None", "US", "KR", "JP"],
    format_func=lambda x: {"None": "글로벌 (전체)", "US": "미국", "KR": "한국", "JP": "일본"}[x]
)

period_option = st.sidebar.selectbox(
    "📅 업로드 기간",
    options=["3days", "1week", "1month", "3months", "6months", "1year", "all"],
    index=2,
    format_func=lambda x: {
        "3days": "최근 3일", "1week": "최근 1주일", "1month": "최근 한달",
        "3months": "최근 3개월", "6months": "최근 6개월", "1year": "최근 1년", "all": "전체"
    }[x]
)

st.sidebar.divider()

# [수정 포인트: 구독자 및 조회수 범위 설정]
st.sidebar.subheader("👥 구독자 수 범위")
col1, col2 = st.sidebar.columns(2)
min_sub = col1.number_input("최소 구독자", value=0, step=1000)
max_sub = col2.number_input("최대 구독자", value=10000000, step=100000)

st.sidebar.subheader("👁️ 누적 조회수 범위")
col3, col4 = st.sidebar.columns(2)
min_views = col3.number_input("최소 조회수", value=0, step=10000)
max_views = col4.number_input("최대 조회수", value=1000000000, step=1000000)

st.sidebar.subheader("🎬 기타 필터")
min_vids = st.sidebar.number_input("최소 영상 수", value=10, step=5)

# --- 기간 계산 함수 ---
def get_published_after(option):
    if option == "all": return None
    now = datetime.utcnow()
    delta_map = {
        "3days": timedelta(days=3), "1week": timedelta(weeks=1),
        "1month": timedelta(days=30), "3months": timedelta(days=90),
        "6months": timedelta(days=180), "1year": timedelta(days=365)
    }
    return (now - delta_map[option]).strftime('%Y-%m-%dT%H:%M:%SZ')

if api_key:
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    user_input = st.text_input("분석할 키워드 또는 채널명", placeholder="예: 해외이슈 쇼츠")

    if st.button("정밀 분석 시작"):
        try:
            with st.spinner('데이터 필터링 중...'):
                published_after = get_published_after(period_option)
                
                # [STEP 1] 검색 실행
                search_params = {
                    "part": "snippet", "q": user_input, "type": "video",
                    "maxResults": 30, "order": "viewCount"
                }
                if country_option != "None": search_params["regionCode"] = country_option
                if published_after: search_params["publishedAfter"] = published_after

                search_res = youtube.search().list(**search_params).execute()
                candidate_ids = list(set([item['snippet']['channelId'] for item in search_res['items']]))

                if not candidate_ids:
                    st.warning("검색 결과가 없습니다.")
                else:
                    # [STEP 2] 상세 지표 수집 및 범위 필터링
                    stats_res = youtube.channels().list(
                        part="statistics,snippet", id=",".join(candidate_ids)
                    ).execute()

                    valid_channels = []
                    for ch in stats_res['items']:
                        stat = ch['statistics']
                        sub = int(stat.get('subscriberCount', 0))
                        vid = int(stat.get('videoCount', 0))
                        view = int(stat.get('viewCount', 0))

                        # 💡 핵심: 최소값과 최대값 사이인 경우만 포함
                        if (min_sub <= sub <= max_sub) and (min_views <= view <= max_views) and (vid >= min_vids):
                            valid_channels.append({
                                "title": ch['snippet']['title'], "id": ch['id'],
                                "thumb": ch['snippet']['thumbnails']['medium']['url'],
                                "sub": sub, "view": view, "vid": vid
                            })

                    # [STEP 3] 결과 출력
                    if valid_channels:
                        st.subheader(f"✅ 정밀 필터 통과 채널 ({len(valid_channels)}개)")
                        cols = st.columns(3)
                        for idx, ch in enumerate(valid_channels):
                            with cols[idx % 3]:
                                st.image(ch['thumb'], use_container_width=True)
                                st.markdown(f"**[{ch['title']}](https://www.youtube.com/channel/{ch['id']})**")
                                st.caption(f"👥 {ch['sub']:,}명 | 🎬 {ch['vid']:,}개 | 👁️ {ch['view']:,}회")
                                st.divider()
                    else:
                        st.error("설정한 범위(최소~최대)를 만족하는 채널이 없습니다.")

        except Exception as e:
            st.error(f"오류: {e}")
