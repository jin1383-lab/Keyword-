import streamlit as st
import googleapiclient.discovery
from collections import Counter
import re

st.set_page_config(page_title="Advanced Channel Analyzer", page_icon="📊", layout="wide")
st.title("📊 유튜브 정밀 채널 및 키워드 분석기")

# 사이드바 필터 설정
st.sidebar.header("🎯 검색 필터 및 설정")
api_key = st.sidebar.text_input("YouTube API Key", type="password")
min_sub = st.sidebar.number_input("최소 구독자 수", value=1000, step=1000)
min_vids = st.sidebar.number_input("최소 영상 수", value=10, step=5)

if api_key:
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    user_input = st.text_input("채널 핸들(@) 또는 검색 키워드", placeholder="@joshuamagazine")

    if st.button("데이터 분석 및 키워드 추출 시작"):
        try:
            # 1. 후보 채널군 검색
            search_res = youtube.search().list(
                part="snippet",
                q=user_input + " 이슈 쇼츠",
                type="channel",
                maxResults=15,
                relevanceLanguage="ko"
            ).execute()

            candidate_ids = [item['snippet']['channelId'] for item in search_res['items']]
            
            if not candidate_ids:
                st.warning("후보 채널을 찾지 못했습니다.")
            else:
                # 2. 채널별 상세 통계(구독자, 영상수, 조회수) 일괄 수집
                stats_res = youtube.channels().list(
                    part="statistics,snippet",
                    id=",".join(candidate_ids)
                ).execute()

                all_titles = ""
                valid_channels = []

                # 필터링 및 데이터 정리
                for ch in stats_res['items']:
                    stat = ch['statistics']
                    sub = int(stat.get('subscriberCount', 0))
                    vid = int(stat.get('videoCount', 0))
                    view = int(stat.get('viewCount', 0))

                    if sub >= min_sub and vid >= min_vids:
                        valid_channels.append({
                            "title": ch['snippet']['title'],
                            "id": ch['id'],
                            "thumb": ch['snippet']['thumbnails']['medium']['url'],
                            "sub": sub,
                            "vid": vid,
                            "view": view
                        })
                        # 키워드 분석용 텍스트 수집 (채널 설명 포함)
                        all_titles += " " + ch['snippet']['title'] + " " + ch['snippet']['description']

                # 3. 키워드 추출 (제목 및 설명 기반)
                words = re.findall(r'[가-힣]{2,}', all_titles)
                stop_words = ['영상', '진짜', '이유', '현재', '결국', '충격', '채널', '구독']
                filtered_words = [w for w in words if w not in stop_words]
                keyword_counts = Counter(filtered_words).most_common(10)

                # 4. 결과 출력
                st.divider()
                
                # --- [상단] 키워드 및 해시태그 섹션 ---
                st.subheader("🏷️ 추천 해시태그 및 트렌드 키워드")
                hashtag_str = " ".join([f"#{w[0]}" for w in keyword_counts])
                st.code(hashtag_str, language="markdown")
                
                # --- [하단] 상세 채널 리스트 (구독자, 영상수 포함) ---
                st.subheader(f"✅ 필터 조건 통과 채널 ({len(valid_channels)}개)")
                
                cols = st.columns(3)
                for idx, ch in enumerate(valid_channels):
                    with cols[idx % 3]:
                        st.image(ch['thumb'], use_container_width=True)
                        st.markdown(f"### **[{ch['title']}](https://www.youtube.com/channel/{ch['id']})**")
                        # 💡 여기에 요청하신 핵심 지표들을 큼직하게 배치했습니다.
                        st.markdown(f"""
                        - 👥 **구독자 수**: {ch['sub']:,}명
                        - 🎬 **총 영상 수**: {ch['vid']:,}개
                        - 👁️ **누적 조회수**: {ch['view']:,}회
                        """)
                        st.divider()

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
else:
    st.info("사이드바에 API Key를 먼저 입력해 주세요.")
