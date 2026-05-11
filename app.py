import streamlit as st
import googleapiclient.discovery
from collections import Counter
import re

st.set_page_config(page_title="Pro Analyzer v2", page_icon="📈", layout="wide")
st.title("📈 누적 조회수 필터가 포함된 채널 분석기")

# 사이드바: 필터 설정 (누적 조회수 추가)
st.sidebar.header("🎯 정밀 필터 설정")
api_key = st.sidebar.text_input("YouTube API Key", type="password")
min_sub = st.sidebar.number_input("최소 구독자 수", value=1000, step=1000)
min_vids = st.sidebar.number_input("최소 영상 수", value=10, step=5)
# 💡 누적 조회수 필터 추가
min_views = st.sidebar.number_input("최소 누적 조회수", value=50000, step=10000)

if api_key:
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    user_input = st.text_input("분석할 채널 핸들(@) 또는 주제 입력", placeholder="@joshuamagazine")

    if st.button("필터링 및 분석 시작"):
        try:
            # 1. 후보 채널군 검색 (1단계)
            search_res = youtube.search().list(
                part="snippet",
                q=user_input + " 이슈 쇼츠",
                type="channel",
                maxResults=20,
                relevanceLanguage="ko"
            ).execute()

            candidate_ids = [item['snippet']['channelId'] for item in search_res['items']]
            
            if not candidate_ids:
                st.warning("후보 채널을 찾지 못했습니다.")
            else:
                # 2. 채널별 상세 통계 일괄 수집 (2단계)
                stats_res = youtube.channels().list(
                    part="statistics,snippet",
                    id=",".join(candidate_ids)
                ).execute()

                all_content_text = ""
                valid_channels = []

                # 필터링 로직 수행
                for ch in stats_res['items']:
                    stat = ch['statistics']
                    sub = int(stat.get('subscriberCount', 0))
                    vid = int(stat.get('videoCount', 0))
                    view = int(stat.get('viewCount', 0))

                    # 💡 모든 조건을 만족해야 리스트에 포함
                    if sub >= min_sub and vid >= min_vids and view >= min_views:
                        valid_channels.append({
                            "title": ch['snippet']['title'],
                            "id": ch['id'],
                            "thumb": ch['snippet']['thumbnails']['medium']['url'],
                            "sub": sub,
                            "vid": vid,
                            "view": view
                        })
                        all_content_text += f" {ch['snippet']['title']} {ch['snippet'].get('description', '')}"

                # 3. 결과 출력
                if not valid_channels:
                    st.error("❌ 설정한 필터(조회수 포함)를 만족하는 채널이 없습니다. 조건을 완화해 보세요.")
                else:
                    # 키워드 분석 (상위 10개)
                    words = re.findall(r'[가-힣]{2,}', all_content_text)
                    keyword_counts = Counter([w for w in words if w not in ['영상', '이유', '결국']]).most_common(10)
                    
                    st.subheader("🏷️ 추천 해시태그")
                    st.code(" ".join([f"#{w[0]}" for w in keyword_counts]))

                    st.divider()
                    st.subheader(f"✅ 필터 통과 채널 ({len(valid_channels)}개)")
                    
                    cols = st.columns(3)
                    for idx, ch in enumerate(valid_channels):
                        with cols[idx % 3]:
                            st.image(ch['thumb'], use_container_width=True)
                            st.markdown(f"### **[{ch['title']}](https://www.youtube.com/channel/{ch['id']})**")
                            # 조회수 지표 강조
                            st.write(f"👥 구독자: **{ch['sub']:,}명**")
                            st.write(f"🎬 영상 수: **{ch['vid']:,}개**")
                            st.write(f"👁️ **누적 조회수: {ch['view']:,}회**")
                            st.divider()

        except Exception as e:
            st.error(f"오류: {e}")
