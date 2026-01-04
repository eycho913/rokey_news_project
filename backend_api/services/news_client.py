from dataclasses import dataclass, asdict
from datetime import date, datetime
import json
import os
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
import re
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, retry_if_exception

@dataclass
class SentimentResult:
    """감성 분석 결과 데이터 클래스"""
    label: str # 긍정 (positive), 중립 (neutral), 부정 (negative)
    score: float # -1.0 (가장 부정) ~ 1.0 (가장 긍정)

@dataclass
class NewsItem:
    """뉴스 기사 데이터 클래스"""
    title: str
    description: Optional[str]
    url: str
    source_name: str
    published_at: str # ISO 8601 형식 문자열
    content: Optional[str] = None # 원문 내용 (스크래핑된 본문)
    processed_content: Optional[str] = None # 정제된 본문 내용을 위한 필드 추가
    summary: Optional[str] = None # 요약 내용을 위한 필드 추가
    sentiment: Optional[SentimentResult] = None # 감성 분석 결과를 위한 필드 추가

class NewsAPIException(Exception):
    """NewsAPI 관련 예외 또는 일반 뉴스 스크래핑 관련 예외"""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code

class NewsClient:
    """NewsAPI를 호출하거나 URL에서 직접 뉴스를 가져오는 클라이언트"""
    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(self, api_key: Optional[str] = None):
        # NewsAPI 키는 선택 사항. URL 스크래핑에는 필요 없음.
        self.api_key = api_key

    def _extract_article_content(self, soup: BeautifulSoup) -> str:
        """BeautifulSoup 객체에서 기사 본문을 추출합니다."""
        # 흔히 기사 본문이 포함될 수 있는 태그와 클래스를 탐색
        # 더 복잡한 경우 Readability.js 같은 라이브러리 사용을 고려할 수 있음
        for tag in ['article', 'main', 'div', 'p']:
            contents = soup.find_all(tag, class_=re.compile(r'(content|article|body|post)', re.I))
            if contents:
                text_parts = [p.get_text(separator='\n', strip=True) for p in contents]
                full_text = '\n\n'.join(filter(None, text_parts))
                if len(full_text) > 200:  # 최소한의 본문 길이 확인
                    return full_text
        
        # fallback: 모든 텍스트 가져오기 (헤더, 푸터 등 불필요한 내용 포함될 수 있음)
        return soup.get_text(separator='\n', strip=True)

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3),
           retry=retry_if_exception_type(requests.exceptions.RequestException))
    def get_news_from_url(self, url: str) -> Optional[NewsItem]:
        """
        주어진 URL에서 뉴스 기사 본문을 스크래핑하여 NewsItem 객체를 생성합니다.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status() # HTTP 에러 발생 시 예외 throw
        except requests.exceptions.Timeout:
            raise NewsAPIException(f"URL 요청 시간이 초과되었습니다: {url}")
        except requests.exceptions.RequestException as e:
            # 상태 코드에 따라 NewsAPIException에 status_code 전달
            status_code = e.response.status_code if e.response is not None else None
            raise NewsAPIException(f"URL 요청 실패: {url} - {e}", status_code=status_code)
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # 메타 태그에서 정보 추출 시도
        title = soup.find('meta', property='og:title')
        title = title['content'] if title else soup.title.string if soup.title else '제목 없음'

        description = soup.find('meta', property='og:description')
        description = description['content'] if description else None
        
        # 기사 본문 추출 (더 정교한 로직 필요할 수 있음)
        content = self._extract_article_content(soup)
        
        source_name = soup.find('meta', property='og:site_name')
        source_name = source_name['content'] if source_name else url.split('/')[2] # 도메인 이름 사용

        published_time = soup.find('meta', property='article:published_time')
        if not published_time:
            published_time = soup.find('meta', property='og:updated_time')
        if not published_time:
            published_time = soup.find('time')
            if published_time and published_time.has_attr('datetime'):
                published_time = published_time['datetime']
        published_at = published_time['content'] if published_time else datetime.now().isoformat() # ISO 형식으로 변환 시도

        # 최소한의 유효성 검사
        if not content or len(content) < 50: # 너무 짧은 본문은 무시
            # 대안으로 description 사용
            if description and len(description) > 50:
                content = description
            else:
                return None # 본문을 추출할 수 없는 경우

        return NewsItem(
            title=title,
            description=description,
            url=url,
            source_name=source_name,
            published_at=published_at,
            content=content,
        )

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3),
           retry=(retry_if_exception_type(requests.exceptions.RequestException) |
                  retry_if_exception(lambda e: isinstance(e, NewsAPIException) and e.status_code == 429)))
    def get_news(
        self, 
        keyword: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        language: str = "ko",
        page_size: int = 20,
    ) -> List[NewsItem]:
        """NewsAPI를 통해 뉴스 기사를 검색합니다."""
        if not self.api_key:
            raise NewsAPIException("NewsAPI 키가 제공되지 않아 뉴스 검색 기능을 사용할 수 없습니다.")

        params = {
            "q": keyword,
            "language": language,
            "pageSize": page_size,
            "apiKey": self.api_key,
            "sortBy": "publishedAt",
        }
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()  # 2xx 이외의 상태 코드에 대해 예외 발생
        except requests.exceptions.Timeout:
            raise NewsAPIException("NewsAPI 요청 시간이 초과되었습니다. (Timeout)")
        except requests.exceptions.RequestException as e:
            if e.response:
                status_code = e.response.status_code
                if status_code == 429:
                    raise NewsAPIException("NewsAPI 요청 할당량을 초과했습니다. (429 Too Many Requests)", status_code=status_code)
                raise NewsAPIException(f"NewsAPI 요청 실패: {status_code} {e.response.text}", status_code=status_code)
            raise NewsAPIException(f"NewsAPI 요청 중 오류 발생: {e}")

        data = response.json()
        articles = data.get("articles", [])

        if not articles:
            return []

        return [
            NewsItem(
                title=article.get("title", ""),
                description=article.get("description"),
                url=article.get("url", ""),
                source_name=article.get("source", {}).get("name", ""),
                published_at=article.get("publishedAt", ""),
                content=article.get("content"),
            )
            for article in articles
        ]

def save_to_json(news_items: List[NewsItem], directory: str, filename: str):
    """뉴스 아이템 리스트를 JSON 파일로 저장합니다."""
    if not os.path.exists(directory):
        os.makedirs(directory)

    filepath = os.path.join(directory, filename)
    
    # dataclass의 asdict를 사용하여 모든 필드를 딕셔너리로 변환
    # 이때, 중첩된 dataclass (SentimentResult)도 자동으로 변환됩니다.
    dict_items = [asdict(item) for item in news_items]
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(dict_items, f, ensure_ascii=False, indent=4)
        
    return filepath

