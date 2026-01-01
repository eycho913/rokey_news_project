import re
from typing import Optional
from bs4 import BeautifulSoup
from services.news_client import NewsItem # NewsItem을 가져와서 사용합니다.

class TextExtractionError(Exception):
    """텍스트 추출 및 정제 관련 예외"""
    pass

def _remove_html_tags(text: str) -> str:
    """HTML 태그를 제거하고 텍스트를 추출합니다."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "lxml") # 'lxml' 파서를 사용하여 더 견고하게 파싱
    return soup.get_text()

def _remove_whitespace(text: str) -> str:
    """불필요한 공백 (여러 공백, 줄바꿈)을 제거하고 단일 공백으로 대체합니다."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text) # 여러 공백을 단일 공백으로
    text = text.strip() # 양쪽 끝 공백 제거
    return text

def _truncate_text(text: str, max_length: int) -> str:
    """텍스트를 지정된 최대 길이로 자릅니다."""
    if not text:
        return ""
    if len(text) > max_length:
        # 단어 중간에 잘리지 않도록 마지막 공백을 찾아 자릅니다.
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        if last_space != -1:
            truncated = truncated[:last_space]
        return truncated + "..."
    return text

def extract_and_clean(news_item: NewsItem, max_length: int = 4000) -> str:
    """
    NewsItem에서 본문을 추출하고, HTML 태그 및 불필요한 공백을 제거한 후
    지정된 최대 길이로 자릅니다. 본문이 없는 경우 대체 텍스트를 생성합니다.

    Args:
        news_item (NewsItem): 처리할 뉴스 아이템 객체.
        max_length (int): 텍스트의 최대 길이.

    Returns:
        str: 정제되고 잘린 텍스트 또는 대체 텍스트.
    """
    original_content = news_item.content

    if original_content:
        try:
            cleaned_text = _remove_html_tags(original_content)
            cleaned_text = _remove_whitespace(cleaned_text)
            final_text = _truncate_text(cleaned_text, max_length)
            return final_text
        except Exception as e:
            # HTML 파싱 또는 정제 중 오류 발생 시, 대체 텍스트로 폴백
            print(f"Error during text cleaning for '{news_item.title}': {e}")
            pass # 아래 대체 텍스트 생성 로직으로 넘어감

    # 본문이 없거나 처리 중 오류가 발생한 경우 대체 텍스트 생성
    alt_text = f"{news_item.title}. "
    if news_item.description:
        alt_text += news_item.description + " "
    alt_text += f"출처: {news_item.source_name}."
    return _truncate_text(_remove_whitespace(alt_text), max_length)
