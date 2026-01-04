import pytest
from unittest.mock import patch, MagicMock
import requests
from bs4 import BeautifulSoup
import os
import google.generativeai as genai

from services.news_client import NewsClient, NewsAPIException, NewsItem, SentimentResult
from services.text_extract import extract_and_clean, TextExtractionError
from services.summarizer import GeminiSummarizer, SummarizerException
from services.sentiment import GeminiSentimentAnalyzer, SentimentException, LIKERT_SCALE_LABELS
from services.openai_summarizer import OpenAISummarizer
from services.openai_sentiment import OpenAISentimentAnalyzer

### Fixtures ###
@pytest.fixture
def mock_news_item_full():
    return NewsItem(
        title="Test Article Title",
        description="A short description of the test article.",
        url="http://example.com/test-article",
        source_name="Example News",
        published_at="2023-10-27T10:00:00Z",
        content="<html><body><h1>Test Article Title</h1><p>This is the first paragraph of the article.</p><p>This is the second paragraph.</p></body></html>",
        processed_content="Test Article Title. This is the first paragraph of the article. This is the second paragraph."
    )

@pytest.fixture
def mock_news_item_no_content():
    return NewsItem(
        title="Title Only",
        description="Description Only.",
        url="http://example.com/no-content",
        source_name="No Content Source",
        published_at="2023-10-27T10:00:00Z",
        content=None
    )

@pytest.fixture
def mock_gemini_response_summary():
    mock_response = MagicMock()
    mock_part = MagicMock()
    mock_part.text = """- Bullet point 1
- Bullet point 2
Conclusion: This is a conclusion."""
    mock_response.parts = [mock_part]
    mock_response.prompt_feedback = None
    mock_response.candidates = [MagicMock(finish_reason='STOP')]
    return mock_response

@pytest.fixture
def mock_gemini_response_sentiment():
    mock_response = MagicMock()
    mock_part = MagicMock()
    mock_part.text = '{"score": 4}'
    mock_response.parts = [mock_part]
    mock_response.prompt_feedback = None
    mock_response.candidates = [MagicMock(finish_reason='STOP')]
    return mock_response

@pytest.fixture
def mock_openai_response_summary():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock(content="""- Bullet 1
- Bullet 2
Conclusion: Summary.""")
    return mock_response

@pytest.fixture
def mock_openai_response_sentiment():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock(content='{"score": 4}')
    return mock_response

### NewsClient Tests ###
class TestNewsClient:
    def test_init(self):
        client = NewsClient()
        assert client.api_key is None
        client_with_key = NewsClient(api_key="test_key")
        assert client_with_key.api_key == "test_key"

    @patch('requests.get')
    def test_get_news_from_url_success(self, mock_get, mock_news_item_full):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_news_item_full.content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = NewsClient()
        news_item = client.get_news_from_url("http://example.com/test-article")

        assert news_item is not None
        assert news_item.title == "Test Article Title"
        assert "first paragraph" in news_item.content
        mock_get.assert_called_once()

    @patch('requests.get', side_effect=requests.exceptions.Timeout)
    def test_get_news_from_url_timeout(self, mock_get):
        client = NewsClient()
        with pytest.raises(NewsAPIException, match="URL 요청 시간이 초과되었습니다"):
            client.get_news_from_url("http://example.com/timeout")

    @patch('requests.get', side_effect=requests.exceptions.RequestException("Connection error"))
    def test_get_news_from_url_connection_error(self, mock_get):
        client = NewsClient()
        with pytest.raises(NewsAPIException, match="URL 요청 실패"):
            client.get_news_from_url("http://example.com/connection-error")

    @patch('requests.get')
    def test_get_news_from_url_http_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found", response=mock_response)
        mock_get.return_value = mock_response

        client = NewsClient()
        with pytest.raises(NewsAPIException, match="URL 요청 실패"): # NewsAPIException will wrap HTTPError
            client.get_news_from_url("http://example.com/404")

    @patch('requests.get')
    def test_get_news_from_url_no_content_fallback(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body></body></html>" # Empty body
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = NewsClient()
        news_item = client.get_news_from_url("http://example.com/empty")
        assert news_item is None # Should return None if content extraction fails

    @patch('requests.get')
    def test_get_news_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "articles": [
                {"title": "API Test", "description": "Desc", "url": "http://api.com", "source": {"name": "API Source"}, "publishedAt": "2023-01-01T00:00:00Z", "content": "Content"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = NewsClient(api_key="test_api_key")
        articles = client.get_news(keyword="API Test")
        assert len(articles) == 1
        assert articles[0].title == "API Test"
        mock_get.assert_called_once()

    def test_get_news_no_api_key(self):
        client = NewsClient()
        with pytest.raises(NewsAPIException, match="NewsAPI 키가 제공되지 않아 뉴스 검색 기능을 사용할 수 없습니다."):
            client.get_news(keyword="test")

    @patch('requests.get')
    def test_get_news_429_retries(self, mock_get):
        # First two calls fail with 429, third succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Too Many Requests", response=mock_response_429)

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"articles": [{"title": "Success", "url": "http://success.com", "source": {"name": "Src"}, "publishedAt": "2023-01-01T00:00:00Z"}]}
        mock_response_success.raise_for_status.return_value = None

        mock_get.side_effect = [mock_response_429, mock_response_429, mock_response_success]

        client = NewsClient(api_key="test_api_key")
        articles = client.get_news(keyword="retry_test")

        assert mock_get.call_count == 3
        assert len(articles) == 1
        assert articles[0].title == "Success"

    @patch('requests.get')
    def test_get_news_empty_articles(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"articles": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = NewsClient(api_key="test_api_key")
        articles = client.get_news(keyword="no_articles")
        assert len(articles) == 0

### TextExtraction Tests ###
class TestTextExtraction:
    def test_extract_and_clean_basic(self, mock_news_item_full):
        cleaned_text = extract_and_clean(mock_news_item_full)
        assert "Test Article Title" in cleaned_text
        assert "first paragraph" in cleaned_text
        assert "<html>" not in cleaned_text
        assert "  " not in cleaned_text # Check for multiple spaces

    def test_extract_and_clean_no_content_fallback(self, mock_news_item_no_content):
        cleaned_text = extract_and_clean(mock_news_item_no_content)
        assert "Title Only" in cleaned_text
        assert "Description Only" in cleaned_text
        assert "No Content Source" in cleaned_text
        assert "This is the full content" not in cleaned_text

    def test_extract_and_clean_truncation(self, mock_news_item_full):
        long_text_item = NewsItem(
            title="Long Title",
            description="Long Description",
            url="http://long.com",
            source_name="Long Source",
            published_at="2023-01-01T00:00:00Z",
            content="A" * 1000 # Very long content
        )
        cleaned_text = extract_and_clean(long_text_item, max_length=100)
        assert len(cleaned_text) <= 100 + 3 # +3 for ellipsis
        assert cleaned_text.endswith("...")

    def test_extract_and_clean_empty_content(self):
        empty_item = NewsItem(
            title="Empty",
            description=None,
            url="http://empty.com",
            source_name="Empty Source",
            published_at="2023-01-01T00:00:00Z",
            content=""
        )
        cleaned_text = extract_and_clean(empty_item)
        assert "Empty" in cleaned_text
        assert "Empty Source" in cleaned_text

    def test_extract_and_clean_very_short_content(self):
        short_item = NewsItem(
            title="Short",
            description="Short desc",
            url="http://short.com",
            source_name="Short Source",
            published_at="2023-01-01T00:00:00Z",
            content="Very short."
        )
        cleaned_text = extract_and_clean(short_item)
        assert "Short" in cleaned_text # Fallback should be used
        assert "Very short." not in cleaned_text # Because it's too short

### Summarizer (Gemini) Tests ###
class TestGeminiSummarizer:
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_summarize_success(self, mock_generate_content, mock_gemini_response_summary):
        mock_generate_content.return_value = mock_gemini_response_summary
        summarizer = GeminiSummarizer(api_key="fake_key")
        text = "Some long text to summarize."
        summary = summarizer.summarize(text, "short")
        assert "Bullet point 1" in summary
        assert "Conclusion: This is a conclusion." in summary
        mock_generate_content.assert_called_once()
        assert summarizer._cache[summarizer._generate_cache_key(text, "short")] == summary

    @patch('google.generativeai.GenerativeModel.generate_content', side_effect=Exception("API error"))
    def test_summarize_api_failure(self, mock_generate_content):
        summarizer = GeminiSummarizer(api_key="fake_key")
        with pytest.raises(SummarizerException, match="Failed to summarize text with Gemini API"):
            summarizer.summarize("text", "medium")

    def test_summarize_cache(self, mock_news_item_full):
        # Mock generate_content only for the first call
        with patch('google.generativeai.GenerativeModel.generate_content') as mock_gen_content:
            mock_response = MagicMock()
            mock_part = MagicMock()
            mock_part.text = "- Cached Summary"
            mock_response.parts = [mock_part]
            mock_response.prompt_feedback = None
            mock_response.candidates = [MagicMock(finish_reason='STOP')]
            mock_gen_content.return_value = mock_response

            summarizer = GeminiSummarizer(api_key="fake_key")
            text = "Text for caching test"
            summary1 = summarizer.summarize(text, "medium")
            summary2 = summarizer.summarize(text, "medium")

            mock_gen_content.assert_called_once() # Should only call API once
            assert summary1 == summary2
            assert "- Cached Summary" in summary1

    def test_summarize_empty_text(self):
        summarizer = GeminiSummarizer(api_key="fake_key")
        summary = summarizer.summarize("", "short")
        assert summary == "요약할 내용이 없습니다."

    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_summarize_prompt_blocked(self, mock_generate_content):
        mock_response = MagicMock()
        mock_response.parts = []
        mock_response.prompt_feedback = MagicMock(block_reason='SAFETY')
        mock_generate_content.return_value = mock_response

        summarizer = GeminiSummarizer(api_key="fake_key")
        with pytest.raises(SummarizerException, match="프롬프트가 안전성 정책에 의해 차단되었습니다"):
            summarizer.summarize("harmful text", "short")

    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_summarize_candidate_blocked(self, mock_generate_content):
        mock_response = MagicMock()
        mock_response.parts = []
        mock_response.prompt_feedback = None
        mock_response.candidates = [MagicMock(finish_reason='SAFETY')]
        mock_generate_content.return_value = mock_response

        summarizer = GeminiSummarizer(api_key="fake_key")
        with pytest.raises(SummarizerException, match="요약 결과가 안전성 정책에 의해 차단되었습니다"):
            summarizer.summarize("text", "short")


### Sentiment (Gemini) Tests ###
class TestGeminiSentimentAnalyzer:
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_analyze_success(self, mock_generate_content, mock_gemini_response_sentiment):
        mock_generate_content.return_value = mock_gemini_response_sentiment
        analyzer = GeminiSentimentAnalyzer(api_key="fake_key")
        text = "This is a positive text."
        sentiment = analyzer.analyze(text)
        assert sentiment.label == LIKERT_SCALE_LABELS[4]
        assert sentiment.score == 4.0
        mock_generate_content.assert_called_once()
        assert analyzer._cache[analyzer._generate_cache_key(text)] == sentiment

    @patch('google.generativeai.GenerativeModel.generate_content', side_effect=Exception("API error"))
    def test_analyze_api_failure_fallback_neutral(self, mock_generate_content):
        analyzer = GeminiSentimentAnalyzer(api_key="fake_key")
        sentiment = analyzer.analyze("text")
        assert sentiment.label == LIKERT_SCALE_LABELS[3]
        assert sentiment.score == 3.0

    def test_analyze_cache(self):
        with patch('google.generativeai.GenerativeModel.generate_content') as mock_gen_content:
            mock_response = MagicMock()
            mock_part = MagicMock()
            mock_part.text = '{"score": 5}'
            mock_response.parts = [mock_part]
            mock_response.prompt_feedback = None
            mock_response.candidates = [MagicMock(finish_reason='STOP')]
            mock_gen_content.return_value = mock_response

            analyzer = GeminiSentimentAnalyzer(api_key="fake_key")
            text = "Cache test text."
            sentiment1 = analyzer.analyze(text)
            sentiment2 = analyzer.analyze(text)

            mock_gen_content.assert_called_once()
            assert sentiment1.score == 5.0
            assert sentiment1 == sentiment2

    def test_analyze_empty_text_fallback_neutral(self):
        analyzer = GeminiSentimentAnalyzer(api_key="fake_key")
        sentiment = analyzer.analyze("")
        assert sentiment.label == LIKERT_SCALE_LABELS[3]
        assert sentiment.score == 3.0

    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_analyze_invalid_json_output_fallback_neutral(self, mock_generate_content):
        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_part.text = '{"invalid_json": "no_score"}'
        mock_response.parts = [mock_part]
        mock_response.prompt_feedback = None
        mock_response.candidates = [MagicMock(finish_reason='STOP')]
        mock_generate_content.return_value = mock_response

        analyzer = GeminiSentimentAnalyzer(api_key="fake_key")
        sentiment = analyzer.analyze("text")
        assert sentiment.label == LIKERT_SCALE_LABELS[3]
        assert sentiment.score == 3.0

    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_analyze_non_json_output_fallback_neutral(self, mock_generate_content):
        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_part.text = 'Not a JSON output.'
        mock_response.parts = [mock_part]
        mock_response.prompt_feedback = None
        mock_response.candidates = [MagicMock(finish_reason='STOP')]
        mock_generate_content.return_value = mock_response

        analyzer = GeminiSentimentAnalyzer(api_key="fake_key")
        sentiment = analyzer.analyze("text")
        assert sentiment.label == LIKERT_SCALE_LABELS[3]
        assert sentiment.score == 3.0
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_analyze_prompt_blocked(self, mock_generate_content):
        mock_response = MagicMock()
        mock_response.parts = []
        mock_response.prompt_feedback = MagicMock(block_reason='SAFETY')
        mock_generate_content.return_value = mock_response

        analyzer = GeminiSentimentAnalyzer(api_key="fake_key")
        with pytest.raises(SentimentException, match="프롬프트가 안전성 정책에 의해 차단되었습니다"):
            analyzer.analyze("harmful text")
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_analyze_candidate_blocked(self, mock_generate_content):
        mock_response = MagicMock()
        mock_response.parts = []
        mock_response.prompt_feedback = None
        mock_response.candidates = [MagicMock(finish_reason='SAFETY')]
        mock_generate_content.return_value = mock_response

        analyzer = GeminiSentimentAnalyzer(api_key="fake_key")
        with pytest.raises(SentimentException, match="감성 분석 결과가 안전성 정책에 의해 차단되었습니다"):
            analyzer.analyze("text")


### Summarizer (OpenAI) Tests ###
class TestOpenAISummarizer:
    @patch('openai.OpenAI')
    def test_summarize_success(self, mock_openai_class, mock_openai_response_summary):
        mock_openai_instance = mock_openai_class.return_value
        mock_openai_instance.chat.completions.create.return_value = mock_openai_response_summary

        summarizer = OpenAISummarizer(api_key="fake_key")
        text = "Some text to summarize."
        summary = summarizer.summarize(text, "short")
        assert "Bullet 1" in summary
        mock_openai_instance.chat.completions.create.assert_called_once()
        assert summarizer._cache[summarizer._generate_cache_key(text, "short")] == summary

    @patch('openai.OpenAI', side_effect=Exception("API error"))
    def test_summarize_api_failure(self, mock_openai_class):
        summarizer = OpenAISummarizer(api_key="fake_key")
        with pytest.raises(SummarizerException, match="Failed to summarize text with OpenAI compatible API"):
            summarizer.summarize("text", "medium")

    def test_summarize_cache(self, mock_news_item_full):
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai_instance = mock_openai_class.return_value
            mock_openai_instance.chat.completions.create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content="- Cached OpenAI Summary"))])

            summarizer = OpenAISummarizer(api_key="fake_key")
            text = "Text for OpenAI caching test"
            summary1 = summarizer.summarize(text, "medium")
            summary2 = summarizer.summarize(text, "medium")

            mock_openai_instance.chat.completions.create.assert_called_once()
            assert summary1 == summary2
            assert "- Cached OpenAI Summary" in summary1
    
    def test_summarize_empty_text(self):
        summarizer = OpenAISummarizer(api_key="fake_key")
        summary = summarizer.summarize("", "short")
        assert summary == "There is no content to summarize."

### Sentiment (OpenAI) Tests ###
class TestOpenAISentimentAnalyzer:
    @patch('openai.OpenAI')
    def test_analyze_success(self, mock_openai_class, mock_openai_response_sentiment):
        mock_openai_instance = mock_openai_class.return_value
        mock_openai_instance.chat.completions.create.return_value = mock_openai_response_sentiment

        analyzer = OpenAISentimentAnalyzer(api_key="fake_key")
        text = "This is a positive text."
        sentiment = analyzer.analyze(text)
        assert sentiment.label == LIKERT_SCALE_LABELS[4]
        assert sentiment.score == 4.0
        mock_openai_instance.chat.completions.create.assert_called_once()
        assert analyzer._cache[analyzer._generate_cache_key(text)] == sentiment

    @patch('openai.OpenAI')
    def test_analyze_api_failure_fallback_neutral(self, mock_openai_class):
        mock_openai_instance = mock_openai_class.return_value
        mock_openai_instance.chat.completions.create.side_effect = Exception("API error")

        analyzer = OpenAISentimentAnalyzer(api_key="fake_key")
        sentiment = analyzer.analyze("text")
        assert sentiment.label == LIKERT_SCALE_LABELS[3]
        assert sentiment.score == 3.0

    def test_analyze_cache(self):
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai_instance = mock_openai_class.return_value
            mock_openai_instance.chat.completions.create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content='{"score": 5}'))])

            analyzer = OpenAISentimentAnalyzer(api_key="fake_key")
            text = "Cache test text."
            sentiment1 = analyzer.analyze(text)
            sentiment2 = analyzer.analyze(text)

            mock_openai_instance.chat.completions.create.assert_called_once()
            assert sentiment1.score == 5.0
            assert sentiment1 == sentiment2

    def test_analyze_empty_text_fallback_neutral(self):
        analyzer = OpenAISentimentAnalyzer(api_key="fake_key")
        sentiment = analyzer.analyze("")
        assert sentiment.label == LIKERT_SCALE_LABELS[3]
        assert sentiment.score == 3.0

    @patch('openai.OpenAI')
    def test_analyze_invalid_json_output_fallback_neutral(self, mock_openai_class):
        mock_openai_instance = mock_openai_class.return_value
        mock_openai_instance.chat.completions.create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content='{"invalid_json": "no_score"}'))])
        
        analyzer = OpenAISentimentAnalyzer(api_key="fake_key")
        sentiment = analyzer.analyze("text")
        assert sentiment.label == LIKERT_SCALE_LABELS[3]
        assert sentiment.score == 3.0
    
    @patch('openai.OpenAI')
    def test_analyze_non_json_output_fallback_neutral(self, mock_openai_class):
        mock_openai_instance = mock_openai_class.return_value
        mock_openai_instance.chat.completions.create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content='Not a JSON output.'))])

        analyzer = OpenAISentimentAnalyzer(api_key="fake_key")
        sentiment = analyzer.analyze("text")
        assert sentiment.label == LIKERT_SCALE_LABELS[3]
        assert sentiment.score == 3.0
