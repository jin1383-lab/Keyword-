import streamlit as st
import googleapiclient.discovery

# 1. 페이지 설정
st.set_page_config(page_title="YouTube Channel Finder", page_icon="📺")
st.title("📺 유사 채널 탐색기")
st.markdown("기준 채널의 메타데이터와 토픽을 분석해 비슷한 채널을 추천합니다.")

# 2. API 키 설정 (Streamlit Secrets 또는 사이드바 입력)
# 로컬 테스트 시에는 사이드바에 입력하거나 .streamlit/secrets.toml을 사용하세요.
api_key = st.sidebar.text_input("YouTube API Key를 입력하세요", type="password")

if api_key:
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    # 3. 사용자 입력
    target_id = st.text_input("분석할 채널 ID를 입력하세요 (예: UC_x5XG1OV2P6uYZ5FHS9vNg)")

    if st.button("유사 채널 찾기"):
        try:
            # [STEP 1] 기준 채널 데이터 가져오기
            ch_request = youtube.channels().list(
                part="snippet,topicDetails,brandingSettings",
                id=target_id
            )
            ch_response = ch_request.execute()

            if not ch_response['items']:
                st.error("채널을 찾을 수 없습니다. ID를 확인해주세요.")
            else:
                item = ch_response['items'][0]
                ch_title = item['snippet']['title']
                keywords = item.get('brandingSettings', {}).get('channel', {}).get('keywords', "")
                topics = item.get('topicDetails', {}).get('topicCategories', [])
                topic_kw = topics[0].split('/')[-1] if topics else ""
                
                # 검색어 조합
                query = f"{topic_kw} {keywords.split(' ')[0] if keywords else ''}".strip()

                st.subheader(f"🔍 '{ch_title}' 분석 결과")
                st.info(f"분석된 핵심 키워드: **{query}**")

                # [STEP 2] 유사 채널 검색
                search_request = youtube.search().list(
                    part="snippet",
                    q=query,
                    type="channel",
                    maxResults=12,
                    relevanceLanguage="ko"
                )
                search_response = search_request.execute()

                # [STEP 3] 결과 출력 (Grid 레이아웃)
                st.divider()
                cols = st.columns(3) # 3열로 출력
                
                count = 0
                for i, res in enumerate(search_response['items']):
                    sim_id = res['snippet']['channelId']
                    if sim_id == target_id: continue
                    
                    sim_title = res['snippet']['title']
                    sim_thumb = res['snippet']['thumbnails']['medium']['url']
                    
                    with cols[count % 3]:
                        st.image(sim_thumb, use_container_width=True)
                        st.markdown(f"**[{sim_title}](https://www.youtube.com/channel/{sim_id})**")
                    count += 1

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
else:
    st.warning("왼쪽 사이드바에 API Key를 입력해야 기능이 활성화됩니다.")
