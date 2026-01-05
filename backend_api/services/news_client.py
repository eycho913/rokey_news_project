import time # Added for caching
from typing import List, Optional, Literal # Added Literal
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
    CACHE_TTL_SECONDS = 300  # Cache Time-To-Live: 5 minutes

    def __init__(self, api_key: Optional[str] = None):
        # NewsAPI 키는 선택 사항. URL 스크래핑에는 필요 없음.
        self.api_key = api_key
        self._news_cache = {}  # Stores cached news items
        self._cache_timestamps = {} # Stores when each cache entry was made

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
        # Check cache for web scraped content
        if url in self._news_cache and \
           (time.time() - self._cache_timestamps.get(url, 0) < self.CACHE_TTL_SECONDS):
            logger.info(f"Returning web scraped content from cache for URL: {url}")
            return self._news_cache[url]

        start_time = time.time() # Start timing for web scraping
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status() # HTTP 에러 발생 시 예외 throw
            logger.info(f"Web scraping GET request for {url} took {time.time() - start_time:.2f} seconds.") # Log request time
        except requests.exceptions.Timeout:
            logger.error(f"Web scraping GET request for {url} timed out after {time.time() - start_time:.2f} seconds.") # Log timeout
            raise NewsAPIException(f"URL 요청 시간이 초과되었습니다: {url}")
        except requests.exceptions.RequestException as e:
            # 상태 코드에 따라 NewsAPIException에 status_code 전달
            status_code = e.response.status_code if e.response is not None else None
            logger.error(f"Web scraping GET request for {url} failed after {time.time() - start_time:.2f} seconds with status {status_code}: {e}") # Log failure
            raise NewsAPIException(f"URL 요청 실패: {url} - {e}", status_code=status_code)
        
        parse_start_time = time.time() # Start timing for parsing
        soup = BeautifulSoup(response.text, 'html.parser')

        # 메타 태그에서 정보 추출 시도
        title = soup.find('meta', property='og:title')
        title = title['content'] if title else soup.title.string if soup.title else '제목 없음'

        description = soup.find('meta', property='og:description')
        description = description['content'] if description else None
        
        # 기사 본문 추출 (더 정교한 로직 필요할 수 있음)
        content_extract_start_time = time.time()
        content = self._extract_article_content(soup)
        logger.info(f"Article content extraction from {url} took {time.time() - content_extract_start_time:.2f} seconds.")
        
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
                logger.warning(f"Failed to extract sufficient content from {url}.") # Log warning
                return None # 본문을 추출할 수 없는 경우

        logger.info(f"Full web scraping and parsing for {url} took {time.time() - parse_start_time:.2f} seconds.") # Log parsing time

        news_item = NewsItem(
            title=title,
            description=description,
            url=url,
            source_name=source_name,
            published_at=published_at,
            content=content,
        )
        # Store in cache
        self._news_cache[url] = news_item
        self._cache_timestamps[url] = time.time()

        return news_item

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3),
           retry=(retry_if_exception_type(requests.exceptions.RequestException) |
                  retry_if_exception(lambda e: isinstance(e, NewsAPIException) and e.status_code == 429)))
    def get_news(
        self, 
        keyword: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        language: str = "ko",
        sources: Optional[str] = None,
        sort_by: Literal["relevancy", "popularity", "publishedAt"] = "publishedAt",
        page_size: int = 20,
        domains: Optional[str] = None, # New parameter
        exclude_domains: Optional[str] = None, # New parameter
        q_in_title: Optional[str] = None, # New parameter
    ) -> List[NewsItem]:
        """NewsAPI를 통해 뉴스 기사를 검색하고 캐싱합니다."""
        if not self.api_key:
            raise NewsAPIException("NewsAPI 키가 제공되지 않아 뉴스 검색 기능을 사용할 수 없습니다.")

        # Generate a cache key from all relevant parameters
        cache_key_params = {
            "keyword": keyword,
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
            "language": language,
            "sources": sources,
            "sort_by": sort_by,
            "page_size": page_size,
            "domains": domains, # New in cache key
            "exclude_domains": exclude_domains, # New in cache key
            "q_in_title": q_in_title, # New in cache key
        }
        cache_key = json.dumps(cache_key_params, sort_keys=True)

        # Check cache
        if cache_key in self._news_cache and \
           (time.time() - self._cache_timestamps.get(cache_key, 0) < self.CACHE_TTL_SECONDS):
            logger.info(f"Returning news from cache for keyword: {keyword}")
            return self._news_cache[cache_key]

        params = {
            "q": keyword,
            "language": language,
            "pageSize": page_size,
            "apiKey": self.api_key,
        }
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()
        if sources:
            params["sources"] = sources
        if sort_by:
            params["sortBy"] = sort_by
        if domains: # New parameter
            params["domains"] = domains
        if exclude_domains: # New parameter
            params["excludeDomains"] = exclude_domains
        if q_in_title: # New parameter
            params["qInTitle"] = q_in_title

        start_time = time.time() # Start timing for NewsAPI call
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            logger.info(f"NewsAPI GET request for keyword '{keyword}' took {time.time() - start_time:.2f} seconds.") # Log request time
        except requests.exceptions.Timeout:
            logger.error(f"NewsAPI GET request for keyword '{keyword}' timed out after {time.time() - start_time:.2f} seconds.") # Log timeout
            raise NewsAPIException("NewsAPI 요청 시간이 초과되었습니다. (Timeout)")
        except requests.exceptions.RequestException as e:
            if e.response:
                status_code = e.response.status_code
                logger.error(f"NewsAPI GET request for keyword '{keyword}' failed after {time.time() - start_time:.2f} seconds with status {status_code}: {e.response.text}") # Log failure
                if status_code == 429:
                    raise NewsAPIException("NewsAPI 요청 할당량을 초과했습니다. (429 Too Many Requests)", status_code=status_code)
                raise NewsAPIException(f"NewsAPI 요청 실패: {status_code} {e.response.text}", status_code=status_code)
            logger.error(f"NewsAPI GET request for keyword '{keyword}' failed after {time.time() - start_time:.2f} seconds: {e}") # Log failure
            raise NewsAPIException(f"NewsAPI 요청 중 오류 발생: {e}")

        data = response.json()
        articles_data = data.get("articles", [])

        if not articles_data:
            return []

        # Convert raw dicts to NewsItem objects
        news_items = [
            NewsItem(
                title=article.get("title", ""),
                description=article.get("description"),
                url=article.get("url", ""),
                source_name=article.get("source", {}).get("name", ""),
                published_at=article.get("publishedAt", ""),
                content=article.get("content"),
            )
            for article in articles_data
        ]

        # Store in cache
        self._news_cache[cache_key] = news_items
        self._cache_timestamps[cache_key] = time.time()

        return news_items


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



