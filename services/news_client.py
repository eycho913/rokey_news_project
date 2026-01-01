from dataclasses import dataclass, asdict
from datetime import date
import json
import os
from typing import List, Optional

import requests

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
    published_at: str
    content: Optional[str] = None # 원문 내용
    processed_content: Optional[str] = None # 정제된 본문 내용을 위한 필드 추가
    summary: Optional[str] = None # 요약 내용을 위한 필드 추가
    sentiment: Optional[SentimentResult] = None # 감성 분석 결과를 위한 필드 추가

class NewsAPIException(Exception):
    """NewsAPI 관련 예외"""
    pass

class NewsClient:
    """NewsAPI를 호출하여 뉴스를 가져오는 클라이언트"""
    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key is required.")
        self.api_key = api_key

    def get_news(
        self,
        keyword: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        language: str = "ko",
        page_size: int = 20,
    ) -> List[NewsItem]:
        """NewsAPI를 통해 뉴스 기사를 검색합니다."""
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
            raise NewsAPIException("요청 시간이 초과되었습니다. (Timeout)")
        except requests.exceptions.RequestException as e:
            if e.response:
                if e.response.status_code == 429:
                    raise NewsAPIException("API 요청 할당량을 초과했습니다. (429 Too Many Requests)")
                raise NewsAPIException(f"API 요청 실패: {e.response.status_code} {e.response.text}")
            raise NewsAPIException(f"API 요청 중 오류 발생: {e}")

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