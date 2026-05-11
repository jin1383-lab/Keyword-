import streamlit as st
import googleapiclient.discovery
from collections import Counter
import re

# 1. 페이지 설정
st.set_page_config(page_title="YouTube Pro Analyzer", page_icon="🎬", layout="wide")
st.title("🎬 영상 길이 필터가 포함된 채널 & 키워드 분석기")

# 2. 사이드바 설정
st.sidebar.header("⚙️ 검색 및 필터 설정")
api_key = st.sidebar.text_input("YouTube API Key", type="password")

# [신규] 영상 길이 필터 추가
duration_option = st.sidebar.selectbox(
    "🎥 영상 길이 필터 (유사 채널 검색 기준)",
    options=["any", "short", "medium", "long"],
    format_func=lambda x: {
        "any": "모든 길이",
        "short": "쇼츠 (4분 미만)",
        "medium": "일반 (4분~20분)",
        "long": "장편 (20분 이상)"
    }[x]
)

st.sidebar.subheader("🔍 채널 성과 지표 필터")
min_sub = st.sidebar.number_input("최소 구독자 수", value=1000, step=1000)
min_vids = st.sidebar.number_input("최소 업로드 영상 수", value=10, step=5)
min_views = st.sidebar.number_input("최소 누적 조회수", value=50000, step=10000)

if api_key:
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    user_input = st.text_input("분석할 채널명 또는 키워드 입력", placeholder="예: 조슈아 매거진")

    if st.button("정밀 분석 시작"):
        try:
            with st.spinner('데이터를 분석 중입니다...'):
                # [STEP 1] 검색어 보정 및 후보 채널 검색
                # videoDuration 필터는 type='video'일 때 가장 정확하므로 영상 검색 후 채널을 역추적합니다.
                search_res = youtube.search().list(
                    part="snippet",
                    q=user_input,
                    type="video", # 영상 기반으로 검색해야 길이 필터가 정확히 먹힙니다.
                    videoDuration=duration_option,
                    maxResults=25,
                    relevanceLanguage="ko"
                ).execute()

                # 검색된 영상들의 채널 ID 추출 (중복 제거)
                candidate_ids = list(set([item['snippet']['channelId'] for item in search_res['items']]))

                if not candidate_ids:
                    st.warning("조건에 맞는 검색 결과가 없습니다.")
                else:
                    # [STEP 2] 채널 상세 통계 수집
                    stats_res = youtube.channels().list(
                        part="statistics,snippet",
                        id=",".join(candidate_ids)
                    ).execute()

                    valid_channels = []
                    all_text = ""

                    for ch in stats_res['items']:
                        stat = ch['statistics']
                        sub = int(stat.get('subscriberCount', 0))
                        vid = int(stat.get('videoCount', 0))
                        view = int(stat.get('viewCount', 0))

                        if sub >= min_sub and vid >= min_vids and view >= min_views:
                            valid_channels.append({
                                "title": ch['snippet']['title'],
                                "id": ch['id'],
                                "thumb": ch['snippet']['thumbnails']['medium']['url'],
                                "sub": sub, "vid": vid, "view": view
                            })
                            all_text += f" {ch['snippet']['title']} {ch['snippet'].get('description', '')}"

                    # [STEP 3] 결과 출력
                    if not valid_channels:
                        st.error("필터 조건을 만족하는 채널이 없습니다.")
                    else:
                        st.divider()
                        # 키워드 추출
                        words = re.findall(r'[가-힣]{2,}', all_text)
                        stop_words = ['영상', '진짜', '이유', '결국', '채널', '구독', '최근']
                        keyword_counts = Counter([w for w in words if w not in stop_words]).most_common(10)
                        
                        st.subheader("🏷️ 분석 기반 추천 해시태그")
                        st.code(" ".join([f"#{w[0]}" for w in keyword_counts]))

                        st.subheader(f"✅ 검색된 유사 채널 ({len(valid_channels)}개)")
                        cols = st.columns(3)
                        for idx, ch in enumerate(valid_channels):
                            with cols[idx % 3]:
                                st.image(ch['thumb'], use_container_width=True)
                                st.markdown(f"**[{ch['title']}](https://www.youtube.com/channel/{ch['id']})**")
                                st.caption(f"👥 {ch['sub']:,}명 | 🎬 {ch['vid']:,}개 | 👁️ {ch['view']:,}회")
                                st.divider()

        except Exception as e:
            st.error(f"오류: {e}")
else:
    st.info("API Key를 입력해주세요.")
