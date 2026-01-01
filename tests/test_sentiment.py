import pytest
from unittest.mock import patch, Mock
import os
import google.generativeai as genai
import json

from services.sentiment import GeminiSentimentAnalyzer, SentimentException
from services.news_client import SentimentResult # SentimentResult dataclass import

DUMMY_GEMINI_API_KEY = "dummy_gemini_api_key"

@pytest.fixture
def sentiment_analyzer():
    with patch.dict(os.environ, {"GEMINI_API_KEY": DUMMY_GEMINI_API_KEY}):
        with patch("google.generativeai.configure"): # configure는 한번만 호출되므로 모의
            analyzer = GeminiSentimentAnalyzer(api_key=DUMMY_GEMINI_API_KEY)
            yield analyzer

def _create_mock_response(text_content: str, finish_reason: str = "STOP") -> Mock:
    """Gemini API 응답 Mock 객체를 생성합니다."""
    mock_response = Mock()
    mock_response.text = text_content # 직접 접근 가능하도록 설정
    mock_response.parts = [Mock(text=text_content)] # .parts 접근 시 사용
    mock_response.prompt_feedback = Mock(block_reason=None)
    mock_response.candidates = [Mock(finish_reason=finish_reason)]
    return mock_response

def test_sentiment_analyzer_init_no_api_key():
    """API 키 없이 초기화 시 ValueError 발생 테스트"""
    with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
        GeminiSentimentAnalyzer(api_key="")

def test_sentiment_analyzer_init_invalid_thresholds():
    """잘못된 임계값 설정 시 ValueError 발생 테스트"""
    with pytest.raises(ValueError, match="임계값은 -1.0과 1.0 사이여야 하며"):
        GeminiSentimentAnalyzer(api_key=DUMMY_GEMINI_API_KEY, positive_threshold=0.1, negative_threshold=0.2)
    with pytest.raises(ValueError, match="임계값은 -1.0과 1.0 사이여야 하며"):
        GeminiSentimentAnalyzer(api_key=DUMMY_GEMINI_API_KEY, positive_threshold=1.5)

@patch("google.generativeai.GenerativeModel")
def test_analyze_positive_sentiment(mock_generative_model, sentiment_analyzer):
    """긍정 감성 분석 성공 테스트"""
    mock_model_instance = Mock()
    mock_generative_model.return_value = mock_model_instance
    
    gemini_output = '{"label": "positive", "score": 0.8}'
    mock_model_instance.generate_content.return_value = _create_mock_response(gemini_output)

    result = sentiment_analyzer.analyze("이 제품 정말 최고입니다!")
    assert result.label == "positive"
    assert result.score == 0.8
    mock_model_instance.generate_content.assert_called_once()

@patch("google.generativeai.GenerativeModel")
def test_analyze_negative_sentiment(mock_generative_model, sentiment_analyzer):
    """부정 감성 분석 성공 테스트"""
    mock_model_instance = Mock()
    mock_generative_model.return_value = mock_model_instance
    
    gemini_output = '{"label": "negative", "score": -0.7}'
    mock_model_instance.generate_content.return_value = _create_mock_response(gemini_output)

    result = sentiment_analyzer.analyze("정말 실망스럽고 최악의 경험이었습니다.")
    assert result.label == "negative"
    assert result.score == -0.7

@patch("google.generativeai.GenerativeModel")
def test_analyze_neutral_sentiment(mock_generative_model, sentiment_analyzer):
    """중립 감성 분석 성공 테스트"""
    mock_model_instance = Mock()
    mock_generative_model.return_value = mock_model_instance
    
    gemini_output = '{"label": "neutral", "score": 0.1}' # 기본 임계값 0.3, -0.3 안에서 중립
    mock_model_instance.generate_content.return_value = _create_mock_response(gemini_output)

    result = sentiment_analyzer.analyze("새로운 정책이 발표되었습니다.")
    assert result.label == "neutral"
    assert result.score == 0.1

@patch("google.generativeai.GenerativeModel")
def test_analyze_custom_thresholds(mock_generative_model):
    """사용자 정의 임계값 적용 테스트"""
    mock_model_instance = Mock()
    mock_generative_model.return_value = mock_model_instance
    
    # 임계값: positive >= 0.1, negative <= -0.1
    analyzer_custom = GeminiSentimentAnalyzer(api_key=DUMMY_GEMINI_API_KEY, positive_threshold=0.1, negative_threshold=-0.1)

    # score: 0.15 -> positive
    gemini_output_pos = '{"label": "neutral", "score": 0.15}' 
    mock_model_instance.generate_content.return_value = _create_mock_response(gemini_output_pos)
    result_pos = analyzer_custom.analyze("조금 개선되었습니다.")
    assert result_pos.label == "positive"
    assert result_pos.score == 0.15

    # score: -0.05 -> neutral
    gemini_output_neu = '{"label": "neutral", "score": -0.05}'
    mock_model_instance.generate_content.return_value = _create_mock_response(gemini_output_neu)
    result_neu = analyzer_custom.analyze("변동이 거의 없습니다.")
    assert result_neu.label == "neutral"
    assert result_neu.score == -0.05
    
    # score: -0.2 -> negative
    gemini_output_neg = '{"label": "neutral", "score": -0.2}'
    mock_model_instance.generate_content.return_value = _create_mock_response(gemini_output_neg)
    result_neg = analyzer_custom.analyze("조금 안 좋습니다.")
    assert result_neg.label == "negative"
    assert result_neg.score == -0.2


@patch("google.generativeai.GenerativeModel")
def test_analyze_api_error_fallback(mock_generative_model, sentiment_analyzer):
    """Gemini API 호출 중 오류 발생 시 중립으로 폴백 테스트"""
    mock_model_instance = Mock()
    mock_generative_model.return_value = mock_model_instance
    mock_model_instance.generate_content.side_effect = Exception("API connection error")

    result = sentiment_analyzer.analyze("테스트 텍스트")
    assert result.label == "neutral"
    assert result.score == 0.0 # 폴백 시 기본값 0.0

@patch("google.generativeai.GenerativeModel")
def test_analyze_content_blocked_safety_fallback(mock_generative_model, sentiment_analyzer):
    """안전성 정책으로 인해 콘텐츠가 차단된 경우 중립으로 폴백 테스트"""
    mock_model_instance = Mock()
    mock_generative_model.return_value = mock_model_instance
    
    mock_response = _create_mock_response("", finish_reason="SAFETY")
    mock_response.parts = [] # 텍스트 없음
    mock_response.prompt_feedback = Mock(block_reason="SAFETY_REASON")
    
    mock_model_instance.generate_content.return_value = mock_response

    result = sentiment_analyzer.analyze("위험한 내용의 텍스트입니다.")
    assert result.label == "neutral"
    assert result.score == 0.0

@patch("google.generativeai.GenerativeModel")
def test_analyze_empty_text_input_fallback(mock_generative_model, sentiment_analyzer):
    """빈 텍스트 입력 시 중립으로 폴백 테스트"""
    result = sentiment_analyzer.analyze("")
    assert result.label == "neutral"
    assert result.score == 0.0
    mock_generative_model.assert_not_called()

@patch("google.generativeai.GenerativeModel")
def test_analyze_caching(mock_generative_model, sentiment_analyzer):
    """감성 분석 캐싱 기능 테스트"""
    mock_model_instance = Mock()
    mock_generative_model.return_value = mock_model_instance

    gemini_output = '{"label": "positive", "score": 0.9}'
    mock_model_instance.generate_content.return_value = _create_mock_response(gemini_output)

    test_text = "캐싱 테스트 텍스트입니다."

    # 첫 번째 호출 - API 호출 및 캐시 저장
    result1 = sentiment_analyzer.analyze(test_text)
    mock_model_instance.generate_content.assert_called_once()
    assert result1.label == "positive"
    assert sentiment_analyzer._cache != {}

    # 두 번째 호출 - 캐시에서 반환, API 호출 없음
    mock_model_instance.generate_content.reset_mock()
    result2 = sentiment_analyzer.analyze(test_text)
    mock_model_instance.generate_content.assert_not_called()
    assert result2.label == "positive"
    assert result2.score == 0.9

@patch("google.generativeai.GenerativeModel")
def test_analyze_invalid_json_fallback(mock_generative_model, sentiment_analyzer):
    """Gemini가 유효하지 않은 JSON을 반환할 때 중립으로 폴백 테스트"""
    mock_model_instance = Mock()
    mock_generative_model.return_value = mock_model_instance
    
    invalid_json_output = "이것은 유효하지 않은 JSON입니다."
    mock_model_instance.generate_content.return_value = _create_mock_response(invalid_json_output)

    result = sentiment_analyzer.analyze("텍스트")
    assert result.label == "neutral"
    assert result.score == 0.0
    mock_model_instance.generate_content.assert_called_once()

@patch("google.generativeai.GenerativeModel")
def test_analyze_json_missing_fields_fallback(mock_generative_model, sentiment_analyzer):
    """Gemini JSON 출력에 필요한 필드가 없을 때 중립으로 폴백 테스트"""
    mock_model_instance = Mock()
    mock_generative_model.return_value = mock_model_instance
    
    json_missing_field = '{"score": 0.5}' # label 필드 없음
    mock_model_instance.generate_content.return_value = _create_mock_response(json_missing_field)

    result = sentiment_analyzer.analyze("텍스트")
    assert result.label == "neutral"
    assert result.score == 0.0
    mock_model_instance.generate_content.assert_called_once()

@patch("google.generativeai.GenerativeModel")
def test_analyze_score_clipping(mock_generative_model, sentiment_analyzer):
    """Gemini가 -1.0 ~ 1.0 범위를 벗어나는 스코어 반환 시 클리핑 테스트"""
    mock_model_instance = Mock()
    mock_generative_model.return_value = mock_model_instance
    
    # 2.0 -> 1.0으로 클리핑
    gemini_output_high = '{"label": "positive", "score": 2.0}'
    mock_model_instance.generate_content.return_value = _create_mock_response(gemini_output_high)
    result_high = sentiment_analyzer.analyze("매우 긍정적!")
    assert result_high.label == "positive"
    assert result_high.score == 1.0 # 클리핑 확인

    # -2.0 -> -1.0으로 클리핑
    gemini_output_low = '{"label": "negative", "score": -2.0}'
    mock_model_instance.generate_content.return_value = _create_mock_response(gemini_output_low)
    result_low = sentiment_analyzer.analyze("매우 부정적!")
    assert result_low.label == "negative"
    assert result_low.score == -1.0 # 클리핑 확인
