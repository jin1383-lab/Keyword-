import streamlit as st
import googleapiclient.discovery

st.set_page_config(page_title="Pro Channel Filter", page_icon="⚙️")
st.title("⚙️ 맞춤형 채널 데이터 필터기")

# 사이드바: 필터 설정
st.sidebar.header("🔍 검색 필터 설정")
min_subscribers = st.sidebar.number_input("최소 구독자 수", value=1000, step=500)
min_views = st.sidebar.number_input("최소 총 조회수", value=10000, step=5000)
min_videos = st.sidebar.number_input("최소 업로드 영상 수", value=10, step=5)

api_key = st.sidebar.text_input("YouTube API Key", type="password")

if api_key:
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    user_input = st.text_input("분석할 채널 핸들(@) 또는 키워드 입력", placeholder="@joshuamagazine")

    if st.button("필터링 검색 시작"):
        try:
            # 1. 유사 키워드로 후보 채널군 검색 (최대 20개 추출)
            search_res = youtube.search().list(
                part="snippet",
                q=user_input + " 이슈 쇼츠",
                type="channel",
                maxResults=20,
                relevanceLanguage="ko"
            ).execute()

            candidate_ids = [item['snippet']['channelId'] for item in search_res['items']]
            
            if not candidate_ids:
                st.warning("검색된 후보 채널이 없습니다.")
            else:
                # 2. 후보 채널들의 상세 통계 데이터 한 번에 가져오기 (성능 최적화)
                # 여러 ID를 쉼표로 구분하여 전달하면 쿼터를 아끼고 속도가 빨라집니다.
                stats_res = youtube.channels().list(
                    part="statistics,snippet",
                    id=",".join(candidate_ids)
                ).execute()

                st.subheader(f"✅ 필터 조건 통과 결과")
                cols = st.columns(3)
                display_count = 0

                for ch in stats_res['items']:
                    stat = ch['statistics']
                    sub_count = int(stat.get('subscriberCount', 0))
                    view_count = int(stat.get('viewCount', 0))
                    video_count = int(stat.get('videoCount', 0))

                    # [핵심 로직] 사용자가 설정한 필터 조건 검증
                    if (sub_count >= min_subscribers and 
                        view_count >= min_views and 
                        video_count >= min_videos):
                        
                        with cols[display_count % 3]:
                            st.image(ch['snippet']['thumbnails']['medium']['url'])
                            st.markdown(f"**{ch['snippet']['title']}**")
                            st.caption(f"👥 구독자: {sub_count:,}명")
                            st.caption(f"🎬 영상: {video_count:,}개")
                            st.markdown(f"[채널 이동](https://www.youtube.com/channel/{ch['id']})")
                        display_count += 1
                
                if display_count == 0:
                    st.info("설정한 필터 조건에 맞는 채널이 없습니다. 조건을 완화해보세요.")

        except Exception as e:
            st.error(f"오류: {e}")
