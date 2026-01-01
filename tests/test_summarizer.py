import pytest
from unittest.mock import patch, Mock
import os
import google.generativeai as genai

from services.summarizer import GeminiSummarizer, SummarizerException

DUMMY_GEMINI_API_KEY = "dummy_gemini_api_key"

@pytest.fixture
def gemini_summarizer():
    with patch.dict(os.environ, {"GEMINI_API_KEY": DUMMY_GEMINI_API_KEY}):
        # genai.configure가 한 번만 호출되도록 모의
        with patch("google.generativeai.configure") as mock_configure:
            summarizer = GeminiSummarizer(api_key=DUMMY_GEMINI_API_KEY)
            mock_configure.assert_called_once_with(api_key=DUMMY_GEMINI_API_KEY)
            yield summarizer

def _create_mock_response(text_content: str, finish_reason: str = "STOP") -> Mock:
    """Gemini API 응답 Mock 객체를 생성합니다."""
    mock_response = Mock()
    mock_response.text = text_content # 직접 접근 가능하도록 설정
    mock_response.parts = [Mock(text=text_content)] # .parts 접근 시 사용
    mock_response.prompt_feedback = Mock(block_reason=None)
    mock_response.candidates = [Mock(finish_reason=finish_reason)]
    return mock_response

def test_gemini_summarizer_init_no_api_key():
    """API 키 없이 초기화 시 ValueError 발생 테스트"""
    with pytest.raises(ValueError, match="GEMINI_API_KEY is required."):
        GeminiSummarizer(api_key="")

@patch("google.generativeai.GenerativeModel")
def test_summarize_success(mock_generative_model, gemini_summarizer):
    """성공적인 요약 및 불릿 포인트/결론 파싱 테스트"""
    mock_model_instance = Mock()
    mock_generative_model.return_value = mock_model_instance
    
    # 모델이 반환할 요약 내용
    mock_summary_text = (
        "- 불릿 포인트 1\n"
        "- 불릿 포인트 2\n"
        "결론: 이 기사는 중요합니다."
    )
    mock_model_instance.generate_content.return_value = _create_mock_response(mock_summary_text)

    test_text = "뉴스 기사 본문 내용입니다."
    summary = gemini_summarizer.summarize(test_text, "short")

    assert "불릿 포인트 1" in summary
    assert "결론: 이 기사는 중요합니다." in summary
    mock_model_instance.generate_content.assert_called_once()
    assert gemini_summarizer._cache != {} # 캐시에 저장되었는지 확인

@patch("google.generativeai.GenerativeModel")
def test_summarize_api_error(mock_generative_model, gemini_summarizer):
    """Gemini API 호출 중 오류 발생 테스트 (예: 네트워크 오류)"""
    mock_model_instance = Mock()
    mock_generative_model.return_value = mock_model_instance
    mock_model_instance.generate_content.side_effect = Exception("API connection error")

    with pytest.raises(SummarizerException, match="API connection error"):
        gemini_summarizer.summarize("테스트 텍스트", "medium")

@patch("google.generativeai.GenerativeModel")
def test_summarize_content_blocked_safety(mock_generative_model, gemini_summarizer):
    """안전성 정책으로 인해 콘텐츠가 차단된 경우 테스트"""
    mock_model_instance = Mock()
    mock_generative_model.return_value = mock_model_instance
    
    mock_response = _create_mock_response("", finish_reason="SAFETY")
    mock_response.parts = [] # 텍스트 없음
    mock_response.prompt_feedback = Mock(block_reason="SAFETY_REASON") # 프롬프트 차단 시
    
    mock_model_instance.generate_content.return_value = mock_response

    test_text = "위험한 내용의 텍스트입니다."
    with pytest.raises(SummarizerException) as excinfo:
        gemini_summarizer.summarize(test_text, "short")
    assert "안전성 정책에 의해 차단되었습니다" in str(excinfo.value)

@patch("google.generativeai.GenerativeModel")
def test_summarize_empty_text_input(mock_generative_model, gemini_summarizer):
    """빈 텍스트 입력 시 요약 안 함 테스트"""
    summary = gemini_summarizer.summarize("", "short")
    assert summary is None
    mock_generative_model.assert_not_called() # 모델 호출 안 됨 확인

@patch("google.generativeai.GenerativeModel")
def test_summarize_caching(mock_generative_model, gemini_summarizer):
    """요약 캐싱 기능 테스트"""
    mock_model_instance = Mock()
    mock_generative_model.return_value = mock_model_instance

    mock_summary_text = "- 캐시된 요약입니다.\n결론: 캐시 테스트."
    mock_model_instance.generate_content.return_value = _create_mock_response(mock_summary_text)

    test_text = "캐싱 테스트 텍스트입니다."

    # 첫 번째 호출 - API 호출 및 캐시 저장
    summary1 = gemini_summarizer.summarize(test_text, "medium")
    mock_model_instance.generate_content.assert_called_once()
    assert summary1 == mock_summary_text # 파싱된 결과가 캐시되므로

    # 두 번째 호출 - 캐시에서 반환, API 호출 없음
    mock_model_instance.generate_content.reset_mock() # 호출 카운트 초기화
    summary2 = gemini_summarizer.summarize(test_text, "medium")
    mock_model_instance.generate_content.assert_not_called()
    assert summary2 == mock_summary_text

    # 다른 length_option은 다른 캐시 키를 사용해야 함
    mock_model_instance.generate_content.return_value = _create_mock_response("- 다른 요약.\n결론: 다른 길이.")
    summary3 = gemini_summarizer.summarize(test_text, "long")
    mock_model_instance.generate_content.assert_called_once()
    assert summary3 == "- 다른 요약.\n결론: 다른 길이."
