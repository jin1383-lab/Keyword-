# [1단계] 사용자 입력 받기 (이름, 핸들, ID 모두 가능)
user_input = st.text_input("분석할 채널명 또는 핸들을 입력하세요", placeholder="예: 조슈아 매거진, @joshuamagazine")

if st.button("분석 시작"):
    # [2단계] 자연어 검색을 통해 채널 ID 추출 (search.list 사용)
    search_res = youtube.search().list(
        part="snippet",
        q=user_input,
        type="channel",
        maxResults=1,
        relevanceLanguage="ko"
    ).execute()

    if not search_res.get('items'):
        st.error("입력하신 키워드로 채널을 찾을 수 없습니다.")
    else:
        # 드디어 찾은 진짜 채널 ID!
        target_channel_id = search_res['items'][0]['id']['channelId']
        target_title = search_res['items'][0]['snippet']['title']
        
        st.success(f"🎯 분석 대상 확정: {target_title} (ID: {target_channel_id})")

        # [3단계] 이제 이 ID를 가지고 앞서 만든 '상세 지표(구독자, 조회수)' 수집으로 연결
        # stats_res = youtube.channels().list(part="statistics...", id=target_channel_id).execute()
        # ... 이후 필터링 및 키워드 추출 로직 실행 ...
