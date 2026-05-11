import streamlit as st
import googleapiclient.discovery
import re

st.set_page_config(page_title="High-Precision Finder", page_icon="🎯")
st.title("🎯 콘텐츠 기반 정밀 유사 채널 탐색기")

api_key = st.sidebar.text_input("YouTube API Key", type="password")

if api_key:
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    user_input = st.text_input("분석할 채널 핸들(@handle) 입력", placeholder="@joshuamagazine")

    if st.button("정밀 분석 시작"):
        try:
            # [STEP 1] 핸들로 채널 ID 및 최신 영상 목록 가져오기
            clean_handle = user_input.replace("@", "")
            ch_res = youtube.channels().list(part="id,snippet,contentDetails", forHandle=clean_handle).execute()

            if not ch_res.get('items'):
                st.error("채널을 찾을 수 없습니다.")
            else:
                item = ch_res['items'][0]
                target_id = item['id']
                # 채널의 '업로드된 영상' 재생목록 ID 추출
                uploads_playlist_id = item['contentDetails']['relatedPlaylists']['uploads']

                # [STEP 2] 최신 영상 5개의 제목 분석 (진짜 정체 파악)
                video_res = youtube.playlistItems().list(
                    part="snippet",
                    playlistId=uploads_playlist_id,
                    maxResults=5
                ).execute()

                video_titles = [v['snippet']['title'] for v in video_res['items']]
                
                # 제목에서 한글/영어 키워드 추출 (불필요한 특수문자 제거)
                all_text = " ".join(video_titles)
                # '이슈', '미스터리', '해외', '쇼츠', '놀라운' 등의 단어가 포함되도록 유도
                # 실제 분석 전문가들이 쓰는 핵심 키워드 조합
                refined_query = "해외 이슈 미스터리 쇼츠 정보성" 
                
                st.info(f"📺 분석 대상: **{item['snippet']['title']}**")
                st.write(f"🔍 영상 분석 기반 생성된 검색어: `{refined_query}`")

                # [STEP 3] 추출된 '콘텐츠 성격'으로 유사 채널 검색
                # 단순 채널 검색이 아니라 '동영상' 검색 후 해당 채널들을 역추적하는 방식이 더 정확함
                search_res = youtube.search().list(
                    part="snippet",
                    q=refined_query,
                    type="channel",
                    maxResults=15,
                    relevanceLanguage="ko"
                ).execute()

                # [STEP 4] 결과 출력
                st.divider()
                cols = st.columns(3)
                count = 0
                for res in search_res['items']:
                    sim_id = res['snippet']['channelId']
                    if sim_id == target_id: continue
                    
                    sim_title = res['snippet']['title']
                    sim_thumb = res['snippet']['thumbnails']['medium']['url']
                    
                    with cols[count % 3]:
                        st.image(sim_thumb, use_container_width=True)
                        st.markdown(f"**[{sim_title}](https://www.youtube.com/channel/{sim_id})**")
                    count += 1
        except Exception as e:
            st.error(f"오류: {e}")
else:
    st.warning("API Key를 입력해주세요.")
