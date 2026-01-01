import pytest
from services.text_extract import _remove_html_tags, _remove_whitespace, _truncate_text, extract_and_clean
from services.news_client import NewsItem # NewsItem을 가져와서 사용합니다.

def test_remove_html_tags():
    """HTML 태그 제거 테스트"""
    html_text = "<html><body><h1>Title</h1><p>This is a <b>test</b>.</p></body></html>"
    expected = "TitleThis is a test."
    assert _remove_html_tags(html_text) == expected
    assert _remove_html_tags("") == ""
    assert _remove_html_tags(None) == "" # None 입력 처리

def test_remove_whitespace():
    """불필요한 공백 제거 및 정제 테스트"""
    text_with_ws = "  Hello   \nWorld!\tHow are you?  "
    expected = "Hello World! How are you?"
    assert _remove_whitespace(text_with_ws) == expected
    assert _remove_whitespace("  ") == ""
    assert _remove_whitespace("") == ""
    assert _remove_whitespace(None) == "" # None 입력 처리

def test_truncate_text():
    """텍스트 길이 자르기 테스트"""
    long_text = "This is a very long sentence that needs to be truncated for testing purposes."
    # 단어 경계에서 자르기
    assert _truncate_text(long_text, 10) == "This is a..."
    assert _truncate_text(long_text, 20) == "This is a very long..."
    # 정확히 맞거나 짧은 경우
    assert _truncate_text("Short text", 20) == "Short text"
    assert _truncate_text("", 10) == ""
    # 공백 없이 긴 문자열
    long_word = "pneumonoultramicroscopicsilicovolcanoconiosis"
    assert _truncate_text(long_word, 10) == "pneumonoul..." # 공백이 없으면 그냥 자르고 ... 추가
    assert _truncate_text(None, 10) == "" # None 입력 처리


def test_extract_and_clean_with_content():
    """NewsItem에 본문이 있는 경우 추출 및 정제 테스트"""
    news_item = NewsItem(
        title="Test News",
        description="A description.",
        url="http://example.com",
        source_name="Example News",
        published_at="2023-01-01T00:00:00Z",
        content="<p>This is the <b>full</b> HTML content of the article.</p>\n<p>It has multiple lines and   extra spaces.</p>",
    )
    expected = "This is the full HTML content of the article. It has multiple lines and extra spaces."
    assert extract_and_clean(news_item, max_length=200) == expected

def test_extract_and_clean_without_content():
    """NewsItem에 본문이 없는 경우 대체 텍스트 생성 테스트"""
    news_item = NewsItem(
        title="No Content News",
        description="A brief summary for the article.",
        url="http://example.com/nocontent",
        source_name="Missing News",
        published_at="2023-01-01T00:00:00Z",
        content=None,
    )
    expected = "No Content News. A brief summary for the article. 출처: Missing News."
    assert extract_and_clean(news_item, max_length=200) == expected

def test_extract_and_clean_without_content_or_description():
    """NewsItem에 본문과 description이 모두 없는 경우 대체 텍스트 생성 테스트"""
    news_item = NewsItem(
        title="Minimal News",
        description=None,
        url="http://example.com/minimal",
        source_name="Minimal Source",
        published_at="2023-01-01T00:00:00Z",
        content=None,
    )
    expected = "Minimal News. 출처: Minimal Source."
    assert extract_and_clean(news_item, max_length=200) == expected

def test_extract_and_clean_content_truncation():
    """추출된 본문이 너무 길 때 자르기 테스트"""
    long_html_content = "<p>" + "word " * 100 + "</p>" # 약 500자
    news_item = NewsItem(
        title="Long Content",
        description="Desc",
        url="http://example.com",
        source_name="Source",
        published_at="2023-01-01T00:00:00Z",
        content=long_html_content,
    )
    # 50자까지 자르기
    cleaned_truncated = extract_and_clean(news_item, max_length=50)
    assert len(cleaned_truncated) <= 50 + 3 # ... 추가될 수 있으므로
    assert cleaned_truncated.endswith("...")
    assert "word" in cleaned_truncated

def test_extract_and_clean_alt_text_truncation():
    """대체 텍스트가 너무 길 때 자르기 테스트"""
    news_item = NewsItem(
        title="Very Long Title " * 10, # 약 160자
        description="Very Long Description " * 20, # 약 400자
        url="http://example.com/longalt",
        source_name="Long Alt Source",
        published_at="2023-01-01T00:00:00Z",
        content=None,
    )
    cleaned_truncated = extract_and_clean(news_item, max_length=100)
    assert len(cleaned_truncated) <= 100 + 3
    assert cleaned_truncated.endswith("...")
    assert "Very Long Title" in cleaned_truncated or "Very Long Description" in cleaned_truncated
