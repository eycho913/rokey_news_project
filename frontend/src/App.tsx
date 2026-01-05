import { useState, type ChangeEvent } from 'react';
import { NewsItem, LLMProvider } from './types'; // Import from types.ts
import NewsSearchForm from './components/NewsSearchForm'; // Import NewsSearchForm
import Spinner from './components/Spinner'; // Import Spinner
import InputField from './components/InputField'; // Import InputField
import ResultDisplay from './components/ResultDisplay'; // Import ResultDisplay

// App.css is no longer needed, styles are handled by Tailwind classes

interface AnalysisResult extends NewsItem {
  summary: string;
  sentiment_label: string;
  sentiment_score: number;
}

function App() {
  const [newsUrl, setNewsUrl] = useState<string>('');
  const [llmProvider, setLlmProvider] = useState<LLMProvider>('gemini');
  const [llmApiKey, setLlmApiKey] = useState<string>('');
  const [llmModel, setLlmModel] = useState<string>('');
  const [newsApiKey, setNewsApiKey] = useState<string>(''); 

  const [summaryLength, setSummaryLength] = useState<'short' | 'medium' | 'long'>('medium');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false); // for analysis
  const [error, setError] = useState<string | null>(null);

  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

  const analyzeNews = async () => {
    setLoading(true);
    setError(null);
    setAnalysisResult(null);

    try {
      const response = await fetch(`${backendUrl}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          news_url: newsUrl,
          summary_length: summaryLength,
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
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-100 p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        <header className="text-center mb-10">
          <h1 className="text-4xl font-bold text-gray-900">뉴스 요약 & 감성 분석</h1>
          <p className="text-lg text-gray-600 mt-2">AI를 사용하여 뉴스 기사의 핵심을 빠르게 파악하세요.</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: News Search Form */}
          <NewsSearchForm 
            onNewsSelected={setNewsUrl} 
            newsApiKey={newsApiKey} 
            setNewsApiKey={setNewsApiKey} 
            loadingAnalysis={loading} 
          />

          {/* Right Column: Analysis Form and Results */}
          <main className="lg:col-span-2 p-6 bg-white rounded-xl shadow-lg min-h-[600px]">
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold text-gray-800">기사 분석</h2>
              <InputField id="newsUrl" label="뉴스 기사 URL" type="url" value={newsUrl} onChange={(e) => setNewsUrl(e.target.value)} placeholder="분석할 뉴스 기사의 URL을 입력하세요." disabled={loading} />

              <div>
                <label htmlFor="llmProvider" className="block text-sm font-medium text-gray-700 mb-1">LLM 공급자</label>
                <select id="llmProvider" value={llmProvider} onChange={(e: ChangeEvent<HTMLSelectElement>) => setLlmProvider(e.target.value as LLMProvider)} disabled={loading} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed">
                  <option value="gemini">Gemini</option>
                  <option value="openai">OpenAI (or compatible)</option>
                </select>
              </div>

              <InputField id="llmApiKey" label="Open API Key" type="password" value={llmApiKey} onChange={(e) => setLlmApiKey(e.target.value)} placeholder="API 키 입력" disabled={loading} />
              
              {llmProvider === 'openai' && (
                <InputField id="llmModel" label="LLM 모델 (선택 사항)" value={llmModel} onChange={(e) => setLlmModel(e.target.value)} placeholder="gpt-3.5-turbo" disabled={loading} />
              )}

              <div>
                <label htmlFor="summaryLength" className="block text-sm font-medium text-gray-700 mb-1">요약 길이</label>
                <select id="summaryLength" value={summaryLength} onChange={(e: ChangeEvent<HTMLSelectElement>) => setSummaryLength(e.target.value as 'short' | 'medium' | 'long')} disabled={loading} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed">
                  <option value="short">짧게</option>
                  <option value="medium">중간</option>
                  <option value="long">길게</option>
                </select>
              </div>

              <button onClick={analyzeNews} disabled={loading || !newsUrl || !llmApiKey} className="w-full bg-primary-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors">
                {loading ? '분석 중...' : '뉴스 분석 실행'}
              </button>
            </div>
            
            <hr className="my-6 border-gray-200" />

            {loading && <Spinner />}
            {error && <div className="text-red-600 bg-red-50 p-4 rounded-lg"><strong>오류:</strong> {error}</div>}
            {analysisResult && <ResultDisplay result={analysisResult} />}
            {!loading && !error && !analysisResult && (
              <div className="text-center text-gray-500 h-full flex flex-col justify-center items-center">
                <p className="text-lg">분석 결과가 여기에 표시됩니다.</p>
                <p className="text-sm">왼쪽 폼에 정보를 입력하고 분석을 시작하거나, 뉴스 검색을 해보세요.</p>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}

export default App;