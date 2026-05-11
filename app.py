import googleapiclient.discovery

# 1. API 설정
API_KEY = "YOUR_API_KEY_HERE"
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)

def get_precise_similar_channels(target_channel_id):
    # [STEP 1] 타겟 채널의 상세 정보(주제, 키워드, 카테고리) 가져오기
    channel_request = youtube.channels().list(
        part="snippet,topicDetails,brandingSettings",
        id=target_channel_id
    )
    channel_response = channel_request.execute()

    if not channel_response['items']:
        print("채널을 찾을 수 없습니다.")
        return

    item = channel_response['items'][0]
    channel_title = item['snippet']['title']
    
    # 1-1. 메타 태그(Keywords) 추출
    # 채널 설정에 등록된 키워드들을 가져옵니다.
    keywords = item.get('brandingSettings', {}).get('channel', {}).get('keywords', "")
    # 1-2. 주제(Topic) 추출
    topics = item.get('topicDetails', {}).get('topicCategories', [])
    topic_keyword = topics[0].split('/')[-1] if topics else ""

    # [검색어 조합 전략] 
    # 채널 키워드 중 앞부분 일부와 주제 단어를 조합하여 검색 정밀도를 높입니다.
    refined_query = f"{topic_keyword} {keywords.split(' ')[0] if keywords else ''}".strip()
    
    print(f"🔍 기준 채널: {channel_title}")
    print(f"🏷️ 분석된 조합 키워드: {refined_query}")
    print("-" * 50)

    # [STEP 2] 카테고리 ID 고정 및 검색 실행
    # 유튜브에서 가장 활발한 '엔터테인먼트(24)' 또는 '노하우/스타일(26)' 등으로 고정 가능합니다.
    # 여기서는 검색 시 가장 범용적인 'Video' 카테고리 성격에 맞게 쿼리를 던집니다.
    search_request = youtube.search().list(
        part="snippet",
        q=refined_query,
        type="channel",
        maxResults=15,
        relevanceLanguage="ko",
        # videoCategoryId는 search(type='video')일 때만 작동하므로, 
        # 채널 검색에서는 q(검색어)에 카테고리 성격 단어를 포함하는 것이 가장 정확합니다.
        topicId="/m/019_v2" # 예: '보안/기술' 관련 토픽 ID (필요시 변경 가능)
    )
    search_response = search_request.execute()

    # [STEP 3] 결과 출력
    print(f"✅ '{channel_title}' 채널과 메타데이터가 유사한 채널:")
    count = 0
    for item in search_response['items']:
        sim_title = item['snippet']['title']
        sim_id = item['snippet']['channelId']
        
        if sim_id != target_channel_id:
            count += 1
            print(f"{count}. {sim_title}")
            print(f"   - 채널 링크: https://www.youtube.com/channel/{sim_id}")

# 2. 실행 (분석하고 싶은 채널 ID 입력)
if __name__ == "__main__":
    # 테스트용 채널 ID 입력
    target_id = "UC_x5XG1OV2P6uYZ5FHS9vNg" 
    get_precise_similar_channels(target_id)
