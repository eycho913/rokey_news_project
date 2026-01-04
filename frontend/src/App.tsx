import { useState } from 'react';
import './App.css';

interface AnalysisResult {
  title: string;
  description: string;
  url: string;
  source_name: string;
  published_at: string;
  summary: string;
  sentiment_label: string;
  sentiment_score: number;
}

type LLMProvider = 'gemini' | 'openai';

function App() {
  const [newsUrl, setNewsUrl] = useState<string>('');
  const [llmProvider, setLlmProvider] = useState<LLMProvider>('gemini');
  const [llmApiKey, setLlmApiKey] = useState<string>('');
  const [llmModel, setLlmModel] = useState<string>('');
  const [newsApiKey, setNewsApiKey] = useState<string>('');
  const [summaryLength, setSummaryLength] = useState<'short' | 'medium' | 'long'>('medium');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'; // FastAPI backend URL

  const analyzeNews = async () => {
    setLoading(true);
    setError(null);
    setAnalysisResult(null);

    try {
      const response = await fetch(`${backendUrl}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          news_url: newsUrl,
          summary_length: summaryLength,
          news_api_key: newsApiKey || null,
          llm_provider: llmProvider,
          llm_api_key: llmApiKey,
          llm_model: llmModel || null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '뉴스 분석 중 오류가 발생했습니다.');
      }

      const data: AnalysisResult = await response.json();
      setAnalysisResult(data);
    } catch (err: any) {
      setError(err.message || '알 수 없는 오류가 발생했습니다.');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (score: number) => {
    if (score >= 4) return 'green'; // 긍정
    if (score <= 2) return 'red';   // 부정
    return 'orange';                // 중립
  };

  return (
    <div className="container">
      <h1>뉴스 요약 & 감성 분석</h1>
      <div className="input-section">
        <label htmlFor="newsUrl">뉴스 기사 URL:</label>
        <input
          type="url"
          id="newsUrl"
          value={newsUrl}
          onChange={(e) => setNewsUrl(e.target.value)}
          placeholder="분석할 뉴스 기사의 URL을 입력하세요."
          disabled={loading}
        />

        <label htmlFor="llmProvider">LLM 공급자:</label>
        <select
          id="llmProvider"
          value={llmProvider}
          onChange={(e) => setLlmProvider(e.target.value as LLMProvider)}
          disabled={loading}
        >
          <option value="gemini">Gemini</option>
          <option value="openai">OpenAI (or compatible)</option>
        </select>

        <label htmlFor="llmApiKey">Open API Key:</label>
        <input
          type="password"
          id="llmApiKey"
          value={llmApiKey}
          onChange={(e) => setLlmApiKey(e.target.value)}
          placeholder="사용할 LLM의 API 키를 입력하세요."
          disabled={loading}
        />
        
        {llmProvider === 'openai' && (
            <>
                <label htmlFor="llmModel">LLM 모델 (선택 사항):</label>
                <input
                  type="text"
                  id="llmModel"
                  value={llmModel}
                  onChange={(e) => setLlmModel(e.target.value)}
                  placeholder="예: gpt-3.5-turbo, gpt-4"
                  disabled={loading}
                />
            </>
        )}

        <label htmlFor="newsApiKey">NewsAPI Key (선택 사항):</label>
        <input
          type="password"
          id="newsApiKey"
          value={newsApiKey}
          onChange={(e) => setNewsApiKey(e.target.value)}
          placeholder="NewsAPI 키를 입력하세요 (선택 사항)."
          disabled={loading}
        />

        <label htmlFor="summaryLength">요약 길이:</label>
        <select
          id="summaryLength"
          value={summaryLength}
          onChange={(e) => setSummaryLength(e.target.value as 'short' | 'medium' | 'long')}
          disabled={loading}
        >
          <option value="short">짧게</option>
          <option value="medium">중간</option>
          <option value="long">길게</option>
        </select>

        <button onClick={analyzeNews} disabled={loading || !newsUrl || !llmApiKey}>
          {loading ? '분석 중...' : '뉴스 분석 실행'}
        </button>
      </div>

      {error && <div className="error-message">오류: {error}</div>}

      {analysisResult && (
        <div className="result-section">
          <h2>분석 결과</h2>
          <h3>{analysisResult.title}</h3>
          <p>
            <strong>출처:</strong> {analysisResult.source_name} |{' '}
            <strong>게시일:</strong> {new Date(analysisResult.published_at).toLocaleDateString()}
          </p>
          <p>
            <a href={analysisResult.url} target="_blank" rel="noopener noreferrer">
              기사 원문 링크
            </a>
          </p>

          <p>
            <strong>감성:</strong>{' '}
            <span style={{ color: getSentimentColor(analysisResult.sentiment_score), fontWeight: 'bold' }}>
              {analysisResult.sentiment_label}
            </span>{' '}
            (점수: {analysisResult.sentiment_score.toFixed(1)}점)
          </p>

          <div className="summary-section">
            <strong>요약:</strong>
            <p>{analysisResult.summary}</p>
          </div>

          <p className="description-text">
            <strong>설명:</strong> {analysisResult.description}
          </p>
        </div>
      )}
    </div>
  );
}

export default App;