import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os

# Import the main app instance from your application
from main import app, AnalyzeRequest, AnalyzeResponse, NewsItem, NewsAPIException, HTTPException, SummarizerException, SentimentException

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_env_vars():
    """Fixture to mock environment variables for API keys."""
    with patch.dict(os.environ, {
        "NEWS_API_KEY": "test_news_api_key",
        "LLM_API_KEY": "test_llm_api_key",
        "LLM_PROVIDER": "gemini",
        "LLM_MODEL": "gemini-pro",
        "LLM_API_BASE": "http://mock-llm-api.com",
    }):
        yield

@pytest.fixture
def mock_news_item():
    """Returns a mock NewsItem object."""
    return NewsItem(
        title="Test News",
        description="This is a test description.",
        url="http://test.com/news",
        source_name="Test Source",
        published_at="2026-01-01T00:00:00Z",
        content="This is the full content of the test news article.",
        processed_content="This is the processed content of the test news article."
    )

@pytest.fixture
def mock_analysis_response():
    """Returns a mock AnalyzeResponse object."""
    return AnalyzeResponse(
        title="Test News",
        description="This is a test description.",
        url="http://test.com/news",
        source_name="Test Source",
        published_at="2026-01-01T00:00:00Z",
        summary="This is a test summary.",
        sentiment_label="Positive",
        sentiment_score=4.5
    )

### Test cases for root endpoint ###
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "FastAPI backend is running!"}

### Test cases for /search endpoint ###
@patch('main.NewsClient')
def test_search_news_success(mock_news_client_class, mock_news_item):
    mock_news_client_instance = mock_news_client_class.return_value
    mock_news_client_instance.get_news.return_value = [mock_news_item]

    response = client.get("/search?q=test_keyword")
    assert response.status_code == 200
    assert response.json() == [mock_news_item.model_dump()] # Use model_dump for Pydantic v2
    mock_news_client_instance.get_news.assert_called_once_with(keyword="test_keyword", page_size=20)

@patch('main.os.getenv')
def test_search_news_no_news_api_key(mock_os_getenv):
    mock_os_getenv.side_effect = lambda key, default=None: None if key == "NEWS_API_KEY" else default

    response = client.get("/search?q=test_keyword")
    assert response.status_code == 500
    assert response.json() == {"detail": "NEWS_API_KEY not configured on the backend server."}

@patch('main.NewsClient')
def test_search_news_exception(mock_news_client_class):
    mock_news_client_instance = mock_news_client_class.return_value
    mock_news_client_instance.get_news.side_effect = NewsAPIException("Search failed")

    response = client.get("/search?q=test_keyword")
    assert response.status_code == 500
    assert response.json() == {"detail": "News search failed: Search failed"}

### Test cases for /analyze endpoint ###
@patch('main.NewsClient')
@patch('main.os.getenv')
def test_analyze_news_no_llm_api_key(mock_os_getenv, mock_news_client_class):
    mock_os_getenv.side_effect = lambda key, default=None: {
        "NEWS_API_KEY": "test_news_api_key", # Should not be called in analyze
        "LLM_API_KEY": None,
        "LLM_PROVIDER": "gemini",
        "LLM_MODEL": "gemini-pro",
    }.get(key, default)

    request_payload = {"news_url": "http://test.com/news", "summary_length": "short"}
    response = client.post("/analyze", json=request_payload)
    assert response.status_code == 500
    assert response.json() == {"detail": "LLM_API_KEY not configured on the backend server."}

@patch('main.NewsClient')
@patch('main.os.getenv')
def test_analyze_news_unsupported_llm_provider(mock_os_getenv, mock_news_client_class):
    mock_os_getenv.side_effect = lambda key, default=None: {
        "LLM_API_KEY": "test_llm_api_key",
        "LLM_PROVIDER": "unsupported_provider",
        "LLM_MODEL": "gemini-pro",
    }.get(key, default)

    request_payload = {"news_url": "http://test.com/news", "summary_length": "short"}
    response = client.post("/analyze", json=request_payload)
    assert response.status_code == 400
    assert response.json() == {"detail": "Unsupported LLM provider configured on backend: unsupported_provider"}

@patch('main.NewsClient')
@patch('main.GeminiSummarizer')
@patch('main.GeminiSentimentAnalyzer')
def test_analyze_news_gemini_success(mock_sentiment_analyzer_class, mock_summarizer_class, mock_news_client_class, mock_news_item, mock_analysis_response, mock_env_vars):
    # Mock NewsClient.get_news_from_url
    mock_news_client_instance = mock_news_client_class.return_value
    mock_news_client_instance.get_news_from_url.return_value = mock_news_item

    # Mock text_extract.extract_and_clean
    with patch('main.extract_and_clean', return_value=mock_news_item.processed_content):
        # Mock Summarizer
        mock_summarizer_instance = mock_summarizer_class.return_value
        mock_summarizer_instance.summarize.return_value = mock_analysis_response.summary

        # Mock Sentiment Analyzer
        mock_sentiment_analyzer_instance = mock_sentiment_analyzer_class.return_value
        mock_sentiment_analyzer_instance.analyze.return_value = mock_news_item.sentiment

        request_payload = {"news_url": "http://test.com/news", "summary_length": "short"}
        response = client.post("/analyze", json=request_payload)

        assert response.status_code == 200
        assert response.json() == mock_analysis_response.model_dump()
        mock_news_client_instance.get_news_from_url.assert_called_once_with("http://test.com/news")
        mock_summarizer_instance.summarize.assert_called_once_with(mock_news_item.processed_content, "short")
        mock_sentiment_analyzer_instance.analyze.assert_called_once_with(mock_news_item.processed_content)

@patch('main.NewsClient')
@patch('main.OpenAISummarizer')
@patch('main.OpenAISentimentAnalyzer')
@patch('main.os.getenv')
def test_analyze_news_openai_success(mock_os_getenv, mock_sentiment_analyzer_class, mock_summarizer_class, mock_news_client_class, mock_news_item, mock_analysis_response):
    # Ensure LLM_PROVIDER is set to openai for this test
    mock_os_getenv.side_effect = lambda key, default=None: {
        "NEWS_API_KEY": "test_news_api_key",
        "LLM_API_KEY": "test_llm_api_key",
        "LLM_PROVIDER": "openai",
        "LLM_MODEL": "gpt-3.5-turbo",
        "LLM_API_BASE": "http://mock-openai-api.com",
    }.get(key, default)

    # Mock NewsClient.get_news_from_url
    mock_news_client_instance = mock_news_client_class.return_value
    mock_news_client_instance.get_news_from_url.return_value = mock_news_item

    with patch('main.extract_and_clean', return_value=mock_news_item.processed_content):
        # Mock Summarizer
        mock_summarizer_instance = mock_summarizer_class.return_value
        mock_summarizer_instance.summarize.return_value = mock_analysis_response.summary

        # Mock Sentiment Analyzer
        mock_sentiment_analyzer_instance = mock_sentiment_analyzer_class.return_value
        mock_sentiment_analyzer_instance.analyze.return_value = mock_news_item.sentiment

        request_payload = {"news_url": "http://test.com/news", "summary_length": "short"}
        response = client.post("/analyze", json=request_payload)

        assert response.status_code == 200
        assert response.json() == mock_analysis_response.model_dump()
        mock_news_client_instance.get_news_from_url.assert_called_once_with("http://test.com/news")
        mock_summarizer_instance.summarize.assert_called_once_with(mock_news_item.processed_content, "short")
        mock_sentiment_analyzer_instance.analyze.assert_called_once_with(mock_news_item.processed_content)
        mock_summarizer_class.assert_called_once_with(api_key="test_llm_api_key", model="gpt-3.5-turbo", api_base="http://mock-openai-api.com")
        mock_sentiment_analyzer_class.assert_called_once_with(api_key="test_llm_api_key", model="gpt-3.5-turbo", api_base="http://mock-openai-api.com")

@patch('main.NewsClient')
@patch('main.os.getenv')
def test_analyze_news_url_fetch_failure(mock_os_getenv, mock_news_client_class):
    mock_news_client_instance = mock_news_client_class.return_value
    mock_news_client_instance.get_news_from_url.return_value = None

    request_payload = {"news_url": "http://invalid.com/news", "summary_length": "medium"}
    response = client.post("/analyze", json=request_payload)

    assert response.status_code == 400
    assert response.json() == {"detail": "Could not fetch news content from the provided URL. Please check the URL or try another one."}

@patch('main.NewsClient')
@patch('main.GeminiSummarizer')
@patch('main.GeminiSentimentAnalyzer')
def test_analyze_news_summarization_failure(mock_sentiment_analyzer_class, mock_summarizer_class, mock_news_client_class, mock_news_item, mock_env_vars):
    mock_news_client_instance = mock_news_client_class.return_value
    mock_news_client_instance.get_news_from_url.return_value = mock_news_item

    with patch('main.extract_and_clean', return_value=mock_news_item.processed_content):
        mock_summarizer_instance = mock_summarizer_class.return_value
        mock_summarizer_instance.summarize.side_effect = SummarizerException("LLM summarization error")

        mock_sentiment_analyzer_instance = mock_sentiment_analyzer_class.return_value
        mock_sentiment_analyzer_instance.analyze.return_value = mock_news_item.sentiment # Still get sentiment

        request_payload = {"news_url": "http://test.com/news", "summary_length": "short"}
        response = client.post("/analyze", json=request_payload)

        assert response.status_code == 200
        assert "요약 실패: LLM summarization error" in response.json()["summary"]
        assert response.json()["sentiment_label"] == mock_news_item.sentiment.label

@patch('main.NewsClient')
@patch('main.GeminiSummarizer')
@patch('main.GeminiSentimentAnalyzer')
def test_analyze_news_sentiment_failure(mock_sentiment_analyzer_class, mock_summarizer_class, mock_news_client_class, mock_news_item, mock_env_vars):
    mock_news_client_instance = mock_news_client_class.return_value
    mock_news_client_instance.get_news_from_url.return_value = mock_news_item

    with patch('main.extract_and_clean', return_value=mock_news_item.processed_content):
        mock_summarizer_instance = mock_summarizer_class.return_value
        mock_summarizer_instance.summarize.return_value = mock_news_item.summary # Still get summary

        mock_sentiment_analyzer_instance = mock_sentiment_analyzer_class.return_value
        mock_sentiment_analyzer_instance.analyze.side_effect = SentimentException("LLM sentiment error")

        request_payload = {"news_url": "http://test.com/news", "summary_length": "short"}
        response = client.post("/analyze", json=request_payload)

        assert response.status_code == 200
        assert response.json()["summary"] == mock_news_item.summary
        assert response.json()["sentiment_label"] == "Neutral (Analysis Failed)" # Fallback to neutral
        assert response.json()["sentiment_score"] == 3.0
