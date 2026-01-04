import { useState, type ChangeEvent } from 'react';
// App.css is no longer needed, styles are handled by Tailwind classes

interface NewsItem {
  title: string;
  description: string;
  url: string;
  source_name: string;
  published_at: string;
}

interface AnalysisResult extends NewsItem {
  summary: string;
  sentiment_label: string;
  sentiment_score: number;
}

// A simple spinner component
const Spinner = () => (
  <div className="flex justify-center items-center">
    <div className="w-8 h-8 border-4 border-blue-500 border-dashed rounded-full animate-spin"></div>
  </div>
);

// A component for displaying the analysis result
const ResultDisplay = ({ result }: { result: AnalysisResult }) => {
  const getSentimentColor = (score: number) => {
    if (score >= 4) return 'text-green-600'; // 긍정
    if (score <= 2) return 'text-red-600';   // 부정
    return 'text-yellow-600';               // 중립
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-gray-800">{result.title}</h2>
      <div className="text-sm text-gray-500">
        <span><strong>출처:</strong> {result.source_name}</span> |{' '}
        <span><strong>게시일:</strong> {new Date(result.published_at).toLocaleDateString()}</span>
      </div>
      <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
        기사 원문 링크 &rarr;
      </a>
      
      <div className="p-4 bg-gray-50 rounded-lg border">
        <h3 className="font-semibold text-lg mb-2">감성 분석</h3>
        <p className={`text-xl font-bold ${getSentimentColor(result.sentiment_score)}`}>
          {result.sentiment_label}
          <span className="text-sm font-normal text-gray-600 ml-2">
            (점수: {result.sentiment_score.toFixed(1)}점)
          </span>
        </p>
      </div>

      <div className="p-4 bg-gray-50 rounded-lg border">
        <h3 className="font-semibold text-lg mb-2">AI 요약</h3>
        <p className="text-gray-700 whitespace-pre-wrap">{result.summary}</p>
      </div>

      {result.description && (
        <div className="pt-4 border-t">
          <h3 className="font-semibold text-lg mb-2">원본 설명</h3>
          <p className="text-gray-600 italic">{result.description}</p>
        </div>
      )}
    </div>
  );
};

interface InputFieldProps {
    id: string;
    label: string;
    type?: string;
    value: string;
    onChange: (e: ChangeEvent<HTMLInputElement>) => void;
    placeholder: string;
    disabled: boolean;
}

const InputField = ({ id, label, type = "text", value, onChange, placeholder, disabled }: InputFieldProps) => (
  <div>
      <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
          type={type}
          id={id}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
      />
  </div>
);

function App() {
  const [newsUrl, setNewsUrl] = useState<string>('');
  // LLM configuration is now handled entirely on the backend via environment variables.
  // No need for these state variables in the frontend.

  const [summaryLength, setSummaryLength] = useState<'short' | 'medium' | 'long'>('medium');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false); // for analysis
  const [error, setError] = useState<string | null>(null);

  // State for keyword search
  const [searchKeyword, setSearchKeyword] = useState<string>('');
  const [searchResults, setSearchResults] = useState<NewsItem[]>([]);
  const [searchLoading, setSearchLoading] = useState<boolean>(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

  // Function to perform news search
  const performSearch = async () => {
    setSearchLoading(true);
    setSearchError(null);
    setSearchResults([]);
    setNewsUrl(''); // Clear newsUrl when performing a new search
    setAnalysisResult(null); // Clear analysis result

    try {
      const response = await fetch(`${backendUrl}/search?q=${encodeURIComponent(searchKeyword)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          // NewsAPI Key is handled by backend env var
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '뉴스 검색 중 오류가 발생했습니다.');
      }

      const data: NewsItem[] = await response.json();
      setSearchResults(data);
    } catch (err: any) {
      setSearchError(err.message || '뉴스 검색 중 알 수 없는 오류가 발생했습니다.');
      console.error('Search error:', err);
    } finally {
      setSearchLoading(false);
    }
  };

  // Function to analyze news from URL
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
          // LLM configuration (provider, api_key, model, api_base) is now read from backend environment variables.
          // Frontend no longer sends these.
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
  
  // Handle click on a search result
  const handleResultClick = (url: string) => {
    setNewsUrl(url); // Set the URL for analysis
    setSearchResults([]); // Clear search results after selection
    setSearchKeyword(''); // Clear search keyword
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        <header className="text-center mb-10">
          <h1 className="text-4xl font-bold text-gray-900">뉴스 요약 & 감성 분석</h1>
          <p className="text-lg text-gray-600 mt-2">AI를 사용하여 뉴스 기사의 핵심을 빠르게 파악하세요.</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Input Form & Search */}
          <aside className="lg:col-span-1 p-6 bg-white rounded-xl shadow-lg">
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold text-gray-800">뉴스 검색</h2>
              <div className="flex gap-2">
                <InputField id="searchKeyword" label="검색 키워드" value={searchKeyword} onChange={(e) => setSearchKeyword(e.target.value)} placeholder="예: 인공지능, 경제" disabled={searchLoading || loading} />
                <button onClick={performSearch} disabled={searchLoading || !searchKeyword || loading} className="w-auto bg-blue-500 text-white font-bold py-2 px-4 rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors self-end">
                  {searchLoading ? '검색 중...' : '검색'}
                </button>
              </div>
              {searchError && <div className="text-red-600 bg-red-50 p-3 rounded-lg text-sm"><strong>오류:</strong> {searchError}</div>}
              
              {searchResults.length > 0 && (
                <div className="space-y-2 max-h-60 overflow-y-auto border p-3 rounded-md bg-gray-50">
                  <h3 className="font-semibold text-gray-700">검색 결과 ({searchResults.length}개)</h3>
                  {searchResults.map((item, index) => (
                    <div key={index} onClick={() => handleResultClick(item.url)} className="cursor-pointer p-2 hover:bg-blue-50 rounded-md transition-colors border-b last:border-b-0">
                      <p className="text-blue-700 font-medium">{item.title}</p>
                      <p className="text-xs text-gray-500">{item.source_name} - {new Date(item.published_at).toLocaleDateString()}</p>
                    </div>
                  ))}
                </div>
              )}

              <hr className="my-6 border-gray-200" />

              <h2 className="text-2xl font-semibold text-gray-800">기사 분석</h2>
              <InputField id="newsUrl" label="뉴스 기사 URL" type="url" value={newsUrl} onChange={(e) => setNewsUrl(e.target.value)} placeholder="분석할 뉴스 기사의 URL을 입력하세요." disabled={loading || searchLoading} />

              <div>
                <label htmlFor="summaryLength" className="block text-sm font-medium text-gray-700 mb-1">요약 길이</label>
                <select id="summaryLength" value={summaryLength} onChange={(e: ChangeEvent<HTMLSelectElement>) => setSummaryLength(e.target.value as 'short' | 'medium' | 'long')} disabled={loading || searchLoading} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
                  <option value="short">짧게</option>
                  <option value="medium">중간</option>
                  <option value="long">길게</option>
                </select>
              </div>

              <button onClick={analyzeNews} disabled={loading || searchLoading || !newsUrl} className="w-full bg-blue-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors">
                {loading ? '분석 중...' : '뉴스 분석 실행'}
              </button>
            </div>
          </aside>

          {/* Right Column: Results */}
          <main className="lg:col-span-2 p-6 bg-white rounded-xl shadow-lg min-h-[600px]">
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