import streamlit as st
import googleapiclient.discovery
from collections import Counter
import re

st.set_page_config(page_title="Keyword & Channel Analyzer", page_icon="📈")
st.title("📈 채널 분석 및 트렌드 키워드 추출")

api_key = st.sidebar.text_input("YouTube API Key", type="password")

if api_key:
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    user_input = st.text_input("분석할 채널(@) 또는 주제 입력", placeholder="@joshuamagazine")

    if st.button("정밀 분석 및 키워드 추출"):
        try:
            # 1. 후보 채널 검색
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
                # 2. 채널별 최신 영상의 태그 및 제목 수집
                all_tags = []
                all_titles = ""
                
                with st.spinner('유사 채널의 콘텐츠 데이터를 분석 중입니다...'):
                    for c_id in candidate_ids:
                        video_res = youtube.search().list(
                            part="snippet",
                            channelId=c_id,
                            maxResults=3, # 채널당 최신 영상 3개씩 분석
                            type="video"
                        ).execute()
                        
                        for v in video_res['items']:
                            all_titles += " " + v['snippet']['title']
                            # 상세 태그 정보를 가져오려면 videos().list가 추가로 필요함
                            # 여기서는 제목에서 키워드를 추출하는 방식과 
                            # API에서 제공하는 검색 키워드를 조합합니다.

                # 3. 키워드 정제 (한글 단어 2글자 이상 추출)
                words = re.findall(r'[가-힣]{2,}', all_titles)
                # 불용어 제거 (이슈 채널에서 너무 흔한 단어 제외)
                stop_words = ['영상', '진짜', '이유', '현재', '결국', '충격']
                filtered_words = [w for w in words if w not in stop_words]
                
                keyword_counts = Counter(filtered_words).most_common(10)

                # 4. 결과 시각화
                st.divider()
                st.subheader("🏷️ 분석된 추천 해시태그 & 키워드")
                
                # 해시태그 형태로 표시
                hashtag_str = " ".join([f"#{w[0]}" for w in keyword_counts])
                st.code(hashtag_str, language="markdown")
                
                # 데이터 탭 구성
                tab1, tab2 = st.tabs(["추천 키워드 순위", "검색된 유사 채널"])
                
                with tab1:
                    for i, (word, count) in enumerate(keyword_counts):
                        st.write(f"{i+1}. **{word}** (언급 횟수: {count})")
                
                with tab2:
                    # 이전의 채널 리스트 출력 로직
                    cols = st.columns(3)
                    for idx, item in enumerate(search_res['items']):
                        with cols[idx % 3]:
                            st.image(item['snippet']['thumbnails']['medium']['url'])
                            st.caption(item['snippet']['title'])

        except Exception as e:
            st.error(f"오류 발생: {e}")
