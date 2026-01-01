import pytest
from unittest.mock import patch, Mock
from datetime import date
import requests

from services.news_client import NewsClient, NewsItem, NewsAPIException

DUMMY_API_KEY = "test_key"

@pytest.fixture
def news_client():
    return NewsClient(api_key=DUMMY_API_KEY)

def test_get_news_success(news_client):
    """뉴스 API 호출 성공 케이스 테스트"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "ok",
        "totalResults": 1,
        "articles": [
            {
                "source": {"id": "test-source", "name": "Test Source"},
                "author": "Test Author",
                "title": "Test Title",
                "description": "Test Description",
                "url": "https://test.com",
                "urlToImage": "https://test.com/image.jpg",
                "publishedAt": "2023-01-01T00:00:00Z",
                "content": "Test Content",
            }
        ],
    }

    with patch("requests.get", return_value=mock_response) as mock_get:
        news_items = news_client.get_news("test")

        assert len(news_items) == 1
        assert isinstance(news_items[0], NewsItem)
        assert news_items[0].title == "Test Title"
        assert news_items[0].source_name == "Test Source"
        mock_get.assert_called_once()


def test_get_news_rate_limit_error(news_client):
    """뉴스 API가 429 (Too Many Requests) 에러를 반환하는 케이스 테스트"""
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        response=mock_response
    )

    with patch("requests.get", return_value=mock_response):
        with pytest.raises(NewsAPIException) as excinfo:
            news_client.get_news("test")
        assert "429" in str(excinfo.value)


def test_get_news_timeout_error(news_client):
    """뉴스 API 요청 시 Timeout이 발생하는 케이스 테스트"""
    with patch("requests.get", side_effect=requests.exceptions.Timeout):
        with pytest.raises(NewsAPIException) as excinfo:
            news_client.get_news("test")
        assert "Timeout" in str(excinfo.value)


def test_get_news_empty_result(news_client):
    """뉴스 검색 결과가 없는 케이스 테스트"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "ok",
        "totalResults": 0,
        "articles": [],
    }

    with patch("requests.get", return_value=mock_response):
        news_items = news_client.get_news("no-results")
        assert len(news_items) == 0
