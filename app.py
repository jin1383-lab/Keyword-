import streamlit as st
import googleapiclient.discovery

st.set_page_config(page_title="Debug Channel Finder", page_icon="🛠️")
st.title("🛠️ 검색 실패 해결 버전: 채널 탐색기")

# 사이드바 설정 (초기값 완화)
st.sidebar.header("🔍 필터 조건 (너무 높으면 결과가 안 나와요)")
min_sub = st.sidebar.number_input("최소 구독자 수", value=100, step=100) # 값을 낮춰서 테스트해보세요
min_vids = st.sidebar.number_input("최소 영상 수", value=5, step=1)

api_key = st.sidebar.text_input("YouTube API Key", type="password")

if api_key:
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    user_input = st.text_input("채널 핸들(@) 또는 주제 입력", placeholder="@joshuamagazine")

    if st.button("추적 시작"):
        try:
            # [보정 로직] 핸들에서 핵심 단어 추출 및 검색어 강화
            search_query = user_input.replace("@", "")
            # 검색어가 너무 짧거나 핸들인 경우, 검색 품질을 높이기 위해 범용 키워드 추가
            final_query = f"{search_query} 이슈 쇼츠 미스터리" 
            
            st.write(f"📡 실제 검색어: `{final_query}` (이 단어로 유튜브를 뒤집니다)")

            # 1. 일단 채널 후보를 넉넉하게 50개 가져옵니다 (최대치)
            search_res = youtube.search().list(
                part="snippet",
                q=final_query,
                type="channel",
                maxResults=50, # 후보군을 늘림
                relevanceLanguage="ko"
            ).execute()

            candidate_ids = [item['snippet']['channelId'] for item in search_res['items']]
            
            if not candidate_ids:
                st.warning("⚠️ 유튜브 API 검색 결과 자체가 0건입니다. 검색어를 바꿔보세요.")
            else:
                st.write(f"🔎 후보 채널 {len(candidate_ids)}개를 찾았습니다. 이제 필터를 적용합니다...")

                # 2. 상세 통계 가져와서 필터링
                stats_res = youtube.channels().list(
                    part="statistics,snippet",
                    id=",".join(candidate_ids)
                ).execute()

                display_count = 0
                cols = st.columns(3)

                for ch in stats_res['items']:
                    stat = ch['statistics']
                    sub = int(stat.get('subscriberCount', 0))
                    vid = int(stat.get('videoCount', 0))

                    # 필터 조건 체크
                    if sub >= min_sub and vid >= min_vids:
                        with cols[display_count % 3]:
                            st.image(ch['snippet']['thumbnails']['medium']['url'])
                            st.markdown(f"**{ch['snippet']['title']}**")
                            st.caption(f"👥 {sub:,}명 | 🎬 {vid:,}개")
                            st.markdown(f"[이동](https://www.youtube.com/channel/{ch['id']})")
                        display_count += 1
                
                if display_count == 0:
                    st.error(f"❌ 후보 {len(candidate_ids)}개 중 조건을 만족하는 채널이 없습니다. 필터를 낮춰보세요!")

        except Exception as e:
            st.error(f"연결 오류: {e}")
