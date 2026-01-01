import pytest
from unittest.mock import patch, Mock
import os

# app.py의 main 함수를 직접 가져올 수 없으므로,
# main 함수 내의 로직을 테스트하기 위해 Streamlit과 서비스들을 모의해야 합니다.
# 여기서는 app.py 전체를 모의하기보다, app.py가 의존하는 서비스들이 잘 연동되는지
# 간접적으로 확인하는 방향으로 테스트를 작성합니다.

# Streamlit 앱의 동작을 테스트하는 것은 UI 테스트 프레임워크가 필요하며,
# 여기서는 서비스 간의 통합 로직에 중점을 둡니다.

# 주요 서비스들의 모의 객체를 생성하는 fixture
@pytest.fixture
def mock_news_client():
    with patch("services.news_client.NewsClient") as MockNewsClient:
        instance = MockNewsClient.return_value
        yield instance

@pytest.fixture
def mock_summarizer():
    with patch("services.summarizer.GeminiSummarizer") as MockSummarizer:
        instance = MockSummarizer.return_value
        yield instance

@pytest.fixture
def mock_sentiment_analyzer():
    with patch("services.sentiment.GeminiSentimentAnalyzer") as MockSentimentAnalyzer:
        instance = MockSentimentAnalyzer.return_value
        yield instance

# app.py의 Streamlit 컴포넌트들을 모의하는 fixture
@pytest.fixture
def mock_streamlit():
    with patch("streamlit.text_input") as mock_text_input, \
         patch("streamlit.selectbox") as mock_selectbox, \
         patch("streamlit.button") as mock_button, \
         patch("streamlit.spinner") as mock_spinner, \
         patch("streamlit.progress") as mock_progress, \
         patch("streamlit.success") as mock_success, \
         patch("streamlit.warning") as mock_warning, \
         patch("streamlit.error") as mock_error, \
         patch("streamlit.write") as mock_write, \
         patch("streamlit.markdown") as mock_markdown, \
         patch("streamlit.subheader") as mock_subheader, \
         patch("streamlit.slider") as mock_slider, \
         patch("streamlit.session_state") as mock_session_state, \
         patch("streamlit.sidebar") as mock_sidebar:

        # 사이드바 컨텍스트 매니저 모의
        mock_sidebar.__enter__.return_value = mock_sidebar
        mock_sidebar.__exit__.return_value = None

        # st.session_state의 속성들을 모의하여 초기화
        mock_session_state.processed_news = []
        mock_session_state.selected_article_index = None

        yield Mock(
            text_input=mock_text_input,
            selectbox=mock_selectbox,
            button=mock_button,
            spinner=mock_spinner,
            progress=mock_progress,
            success=mock_success,
            warning=mock_warning,
            error=mock_error,
            write=mock_write,
            markdown=mock_markdown,
            subheader=mock_subheader,
            slider=mock_slider,
            session_state=mock_session_state,
            sidebar=mock_sidebar,
            expander=Mock(), # st.expander도 모의
            download_button=Mock(), # st.download_button도 모의
        )

# NewsItem 더미 데이터
@pytest.fixture
def dummy_news_item():
    from services.news_client import NewsItem, SentimentResult
    return NewsItem(
        title="Test News Title",
        description="Test News Description",
        url="http://test.com",
        source_name="Test Source",
        published_at="2023-01-01T00:00:00Z",
        content="Full content of the test news article.",
        processed_content="Processed content of the test news article.",
        summary="Summary of the test news article.",
        sentiment=SentimentResult(label="neutral", score=0.1)
    )

# 환경 변수를 설정하는 fixture
@pytest.fixture(autouse=True)
def set_env_vars():
    with patch.dict(os.environ, {
        "NEWS_API_KEY": "dummy_news_api_key",
        "GEMINI_API_KEY": "dummy_gemini_api_key",
    }):
        yield

def test_main_app_flow_success(
    mock_streamlit,
    mock_news_client,
    mock_summarizer,
    mock_sentiment_analyzer,
    dummy_news_item
):
    """
    app.py의 주요 흐름이 성공적으로 작동하는지 통합 테스트.
    Streamlit UI 상호작용과 서비스 호출을 모의합니다.
    """
    from app import main # app.py의 main 함수를 가져옵니다.

    # Streamlit 입력 모의
    mock_streamlit.text_input.return_value = "AI" # 키워드
    mock_streamlit.selectbox.return_value = "medium" # 요약 길이
    mock_streamlit.slider.side_effect = [0.3, -0.3] # 긍정/부정 임계값
    mock_streamlit.button.side_effect = [True, False] # "뉴스 검색 및 분석 실행" 버튼 클릭, "결과 초기화"는 클릭 안 함

    # 서비스 모의 응답 설정
    mock_news_client.get_news.return_value = [dummy_news_item]
    mock_summarizer.summarize.return_value = dummy_news_item.summary
    mock_sentiment_analyzer.analyze.return_value = dummy_news_item.sentiment

    # main 함수 실행 (한 번의 Streamlit 런을 시뮬레이션)
    main()

    # NewsClient 호출 확인
    mock_news_client.get_news.assert_called_once_with(keyword="AI", page_size=10)

    # Summarizer 호출 확인
    mock_summarizer.summarize.assert_called_once_with(
        dummy_news_item.processed_content, "medium"
    )

    # SentimentAnalyzer 호출 확인
    mock_sentiment_analyzer.analyze.assert_called_once_with(dummy_news_item.processed_content)

    # Streamlit 출력 확인 (일부만)
    mock_streamlit.progress.assert_any_call(10, text="뉴스 검색 중...")
    mock_streamlit.progress.assert_any_call(100, text="모든 뉴스 분석 완료!")
    mock_streamlit.success.assert_called_once()
    mock_streamlit.subheader.assert_any_call(dummy_news_item.title)
    mock_streamlit.write.assert_any_call(dummy_news_item.summary)
    mock_streamlit.markdown.assert_any_call(
        f"**감성**: <span style='color:orange; font-weight:bold'>neutral</span> (스코어: 0.10)",
        unsafe_allow_html=True,
    )

    # 세션 상태에 결과 저장 확인
    assert len(mock_streamlit.session_state.processed_news) == 1
    assert mock_streamlit.session_state.processed_news[0].title == "Test News Title"
    
    # 다운로드 버튼 호출 확인 (정확한 내용은 확인 어렵지만, 호출은 되어야 함)
    mock_streamlit.download_button.assert_called()


def test_main_app_flow_no_api_keys(mock_streamlit):
    """API 키가 없을 때 오류 메시지 표시 테스트"""
    from app import main

    with patch.dict(os.environ, {}, clear=True): # 환경 변수 모두 제거
        # Streamlit 입력 모의
        mock_streamlit.text_input.return_value = "AI"
        mock_streamlit.selectbox.return_value = "medium"
        mock_streamlit.button.return_value = True

        main()

        mock_streamlit.error.assert_any_call("NewsAPI 키가 설정되지 않았습니다. `.env` 파일을 확인해주세요.")

def test_main_app_flow_no_keyword(mock_streamlit):
    """키워드 없이 검색 시 경고 메시지 표시 테스트"""
    from app import main

    mock_streamlit.text_input.return_value = "" # 빈 키워드
    mock_streamlit.selectbox.return_value = "medium"
    mock_streamlit.button.return_value = True

    main()

    mock_streamlit.warning.assert_called_once_with("키워드를 입력해주세요.")
    
def test_main_app_flow_no_news_found(mock_streamlit, mock_news_client):
    """뉴스 검색 결과가 없을 때 경고 메시지 표시 테스트"""
    from app import main

    mock_streamlit.text_input.return_value = "없는 키워드"
    mock_streamlit.selectbox.return_value = "medium"
    mock_streamlit.button.return_value = True

    mock_news_client.get_news.return_value = [] # 빈 뉴스 리스트 반환

    main()

    mock_streamlit.warning.assert_called_once_with("검색된 뉴스가 없습니다.")
    mock_streamlit.progress.return_value.empty.assert_called_once()
