import time
import random
from pytrends.request import TrendReq
from requests.exceptions import Timeout, ConnectionError

class TrendHashtagGenerator:
    def __init__(self):
        # 1. 세션 유지 및 타임아웃 설정
        self.pytrends = TrendReq(
            hl='ko-KR', 
            tz=360, 
            retries=3,          # 자체 재시도 설정
            backoff_factor=0.5, # 지연 계수
            timeout=(10, 25)    # (연결 타임아웃, 읽기 타임아웃)
        )

    def get_context_with_retry(self, keyword, geo, max_retries=3):
        """에러 발생 시 지수 백오프를 적용하여 재시도하는 로직"""
        for i in range(max_retries):
            try:
                # 요청 간 랜덤 지연 (429 에러 방지의 핵심)
                time.sleep(random.uniform(2, 5)) 
                
                self.pytrends.build_payload([keyword], geo=geo, timeframe='now 7-d')
                related = self.pytrends.related_queries()
                
                rising = related[keyword]['rising']
                return rising['query'].head(5).tolist() if rising is not None and not rising.empty else []
            
            except Exception as e:
                wait_time = (2 ** i) + random.random() # 2, 4, 8초... 점진적 증가
                print(f"⚠️ {geo} 데이터 로드 실패 ({e}). {wait_time:.2f}초 후 재시도...")
                time.sleep(wait_time)
        
        return [] # 모든 재시도 실패 시 빈 리스트 반환

    def generate_final_prompt(self, emotion_keyword):
        countries = {'KR': 'ko', 'US': 'en-US', 'JP': 'ja'}
        context_results = {}

        for code in countries.keys():
            print(f"🔍 {code} 트렌드 데이터 수집 중...")
            context_results[code] = self.get_context_with_retry(emotion_keyword, code)

        # Gemini에게 보낼 최종 프롬프트 구성
        prompt = f"""
        당신은 다국어 SNS 마케팅 전문가입니다. 
        사용자가 입력한 감정 키워드 '{emotion_keyword}'와 관련된 최신 구글 트렌드 데이터를 기반으로 
        인스타그램/스레드용 해시태그를 생성하세요.

        [구글 트렌드 실시간 연관어]
        - 한국: {context_results['KR']}
        - 미국: {context_results['US']}
        - 일본: {context_results['JP']}

        [출력 규칙]
        1. 각 국가별로 10개의 해시태그를 생성할 것.
        2. 일본어는 현지인들이 자주 쓰는 감성 태그(예: #～と繋がりたい)를 반드시 포함할 것.
        3. 결과는 아래와 같이 언어별 코드 블록으로 제공하여 복사가 가능하게 할 것.
        
        ### 🇰🇷 한국어 태그
        ```
        #태그1 #태그2 ...
        ```
        (영어, 일본어도 동일한 형식)
        """
        return prompt

# 사용 예시
generator = TrendHashtagGenerator()
final_prompt = generator.generate_final_prompt("행복")
print(final_prompt)
