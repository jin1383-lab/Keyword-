import streamlit as st
import googleapiclient.discovery

st.set_page_config(page_title="YouTube Smart Finder", page_icon="🔍")
st.title("🔍 유튜브 핸들 기반 유사 채널 탐색기")

api_key = st.sidebar.text_input("YouTube API Key", type="password")

if api_key:
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    # 사용자 입력 (핸들 또는 ID 모두 대응 가능하도록 설계)
    user_input = st.text_input("채널 핸들(@handle) 또는 ID를 입력하세요", placeholder="@google")

    if st.button("분석 시작"):
        try:
            # [STEP 1] 핸들로 채널 ID 추출하기
            # 핸들에서 @가 포함되어 있다면 제거하고 검색
            clean_handle = user_input.replace("@", "")
            
            # forHandle 파라미터를 사용하여 채널 정보 조회
            ch_request = youtube.channels().list(
                part="id,snippet,topicDetails,brandingSettings",
                forHandle=clean_handle
            )
            ch_response = ch_request.execute()

            # 핸들로 검색 결과가 없을 경우 (혹시 ID를 직접 입력했을 경우를 대비한 예외 처리)
            if not ch_response.get('items'):
                ch_request = youtube.channels().list(
                    part="id,snippet,topicDetails,brandingSettings",
                    id=user_input
                )
                ch_response = ch_request.execute()

            if not ch_response.get('items'):
                st.error("채널을 찾을 수 없습니다. 핸들을 정확히 입력했는지 확인해주세요.")
            else:
                item = ch_response['items'][0]
                target_id = item['id'] # 추출된 진짜 ID
                ch_title = item['snippet']['title']
                
                st.success(f"✅ 채널 확인 완료: **{ch_title}** (ID: {target_id})")
                
                # [STEP 2] 메타데이터 분석 및 검색어 조합
                keywords = item.get('brandingSettings', {}).get('channel', {}).get('keywords', "")
                topics = item.get('topicDetails', {}).get('topicCategories', [])
                topic_kw = topics[0].split('/')[-1] if topics else "Video"
                
                # 검색어 조합 (주제 + 채널 키워드 첫 번째 단어)
                query = f"{topic_kw} {keywords.split(' ')[0] if keywords else ''}".strip()

                # [STEP 3] 유사 채널 검색
                search_request = youtube.search().list(
                    part="snippet",
                    q=query,
                    type="channel",
                    maxResults=12,
                    relevanceLanguage="ko"
                )
                search_response = search_request.execute()

                # [STEP 4] 결과 출력
                st.divider()
                st.subheader(f"💡 '{ch_title}'와 비슷한 추천 채널")
                cols = st.columns(3)
                
                count = 0
                for res in search_response['items']:
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
    st.warning("사이드바에 API Key를 입력해주세요.")
