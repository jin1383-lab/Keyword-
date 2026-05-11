import streamlit as st
import googleapiclient.discovery
from collections import Counter
import re

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="YouTube Smart Analyzer", page_icon="🚀", layout="wide")
st.title("🚀 유튜브 스마트 채널 분석 및 키워드 추출기")
st.markdown("채널 이름만 입력해도 ID를 자동으로 찾고, 성과 지표와 트렌드 키워드를 분석합니다.")

# 2. 사이드바: 설정 및 필터
st.sidebar.header("⚙️ 설정 및 필터")
api_key = st.sidebar.text_input("YouTube API Key", type="password")

# 필터링 수치 설정
st.sidebar.subheader("🔍 필터 조건")
min_sub = st.sidebar.number_input("최소 구독자 수", value=1000, step=1000)
min_vids = st.sidebar.number_input("최소 업로드 영상 수", value=10, step=5)
min_views = st.sidebar.number_input("최소 누적 조회수", value=50000, step=10000)

if api_key:
    # 유튜브 API 빌드
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    # 3. 사용자 입력부
    user_input = st.text_input("분석할 채널명 또는 핸들을 입력하세요", placeholder="예: 조슈아 매거진, @joshuamagazine")

    if st.button("분석 시작"):
        try:
            with st.spinner('채널을 찾고 데이터를 분석하는 중입니다...'):
                # [STEP 1] 자연어 검색으로 채널 ID 추출
                search_res = youtube.search().list(
                    part="snippet",
                    q=user_input,
                    type="channel",
                    maxResults=1,
                    relevanceLanguage="ko"
                ).execute()

                if not search_res.get('items'):
                    st.error("입력하신 이름으로 채널을 찾을 수 없습니다. 정확한 이름을 입력해주세요.")
                else:
                    # 검색 결과에서 ID와 기본 정보 추출
                    target_item = search_res['items'][0]
                    target_id = target_item['id']['channelId']
                    target_title = target_item['snippet']['title']
                    
                    st.success(f"🎯 분석 대상: **{target_title}** (ID: {target_id})")

                    # [STEP 2] 유사 채널 후보군 검색 (사용자 입력 키워드 기반)
                    # 검색 품질을 위해 '이슈 쇼츠' 키워드를 보정어로 붙입니다.
                    candidate_res = youtube.search().list(
                        part="snippet",
                        q=user_input + " 이슈 쇼츠",
                        type="channel",
                        maxResults=20,
                        relevanceLanguage="ko"
                    ).execute()

                    candidate_ids = [item['snippet']['channelId'] for item in candidate_res['items']]

                    # [STEP 3] 후보 채널들의 상세 통계 데이터 일괄 수집
                    stats_res = youtube.channels().list(
                        part="statistics,snippet",
                        id=",".join(candidate_ids)
                    ).execute()

                    valid_channels = []
                    all_text_for_keywords = ""

                    for ch in stats_res['items']:
                        stat = ch['statistics']
                        sub = int(stat.get('subscriberCount', 0))
                        vid = int(stat.get('videoCount', 0))
                        view = int(stat.get('viewCount', 0))

                        # 필터 조건 적용
                        if sub >= min_sub and vid >= min_vids and view >= min_views:
                            valid_channels.append({
                                "title": ch['snippet']['title'],
                                "id": ch['id'],
                                "thumb": ch['snippet']['thumbnails']['medium']['url'],
                                "sub": sub,
                                "vid": vid,
                                "view": view
                            })
                            # 키워드 분석용 텍스트 (제목 + 설명) 수집
                            all_text_for_keywords += f" {ch['snippet']['title']} {ch['snippet'].get('description', '')}"

                    # [STEP 4] 결과 출력
                    if not valid_channels:
                        st.warning("⚠️ 설정한 필터 조건을 만족하는 유사 채널이 없습니다. 필터를 조정해보세요.")
                    else:
                        st.divider()
                        
                        # 키워드/해시태그 섹션
                        st.subheader("🏷️ 트렌드 키워드 및 추천 해시태그")
                        words = re.findall(r'[가-힣]{2,}', all_text_for_keywords)
                        # 분석에 방해되는 일반적인 단어 제거
                        stop_words = ['영상', '진짜', '이유', '결국', '채널', '구독', '현재', '내용', '통해']
                        keyword_counts = Counter([w for w in words if w not in stop_words]).most_common(10)
                        
                        hashtag_str = " ".join([f"#{w[0]}" for w in keyword_counts])
                        st.code(hashtag_str, language="markdown")

                        # 상세 채널 카드 출력
                        st.subheader(f"✅ 유사 채널 리스트 ({len(valid_channels)}개)")
                        cols = st.columns(3)
                        for idx, ch in enumerate(valid_channels):
                            with cols[idx % 3]:
                                st.image(ch['thumb'], use_container_width=True)
                                st.markdown(f"**[{ch['title']}](https://www.youtube.com/channel/{ch['id']})**")
                                st.write(f"👥 구독자: {ch['sub']:,}명")
                                st.write(f"🎬 영상 수: {ch['vid']:,}개")
                                st.write(f"👁️ 총 조회수: {ch['view']:,}회")
                                st.divider()

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
else:
    st.info("사이드바에 YouTube API Key를 입력하면 분석 도구가 활성화됩니다.")
