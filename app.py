import googleapiclient.discovery

def get_channel_id(search_query, api_key):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    
    # [핵심] search.list 메서드 호출
    request = youtube.search().list(
        part="snippet",
        q=search_query,      # 사용자가 입력한 자연어 (예: "슈카월드")
        type="channel",      # 채널만 검색하도록 설정
        maxResults=1,        # 가장 정확한 결과 1개만 요청
        relevanceLanguage="ko"
    )
    response = request.execute()

    if response['items']:
        # 검색 결과의 첫 번째 채널 정보 추출
        channel_id = response['items'][0]['id']['channelId']
        channel_title = response['items'][0]['snippet']['title']
        return channel_id, channel_title
    else:
        return None, "검색 결과 없음"

# 사용 예시
# my_id, my_title = get_channel_id("조슈아 매거진", "YOUR_API_KEY")
