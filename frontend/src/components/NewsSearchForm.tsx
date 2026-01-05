import { useState, type ChangeEvent, useEffect } from 'react';
import Spinner from './Spinner'; // Import Spinner
import DatePicker from 'react-datepicker'; // Import DatePicker
import 'react-datepicker/dist/react-datepicker.css'; // Import DatePicker CSS

// Interfaces moved from App.tsx
interface NewsItem {
    title: string;
    description: string;
    url: string;
    source_name: string;
    published_at: string;
}


// InputField component moved from App.tsx
interface InputFieldProps {
    id: string;
    label: string;
    type?: string;
    value: string;
    onChange: (e: ChangeEvent<HTMLInputElement>) => void;
    placeholder: string;
    disabled: boolean;
    error?: string; // New: Optional error message
}

const InputField = ({ id, label, type = "text", value, onChange, placeholder, disabled, error }: InputFieldProps) => (
    <div>
        <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
        <input
            type={type}
            id={id}
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            disabled={disabled}
            className={`w-full px-3 py-2 border ${error ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'} rounded-md shadow-sm focus:border-blue-500 disabled:bg-gray-50`}
        />
        {error && <p className="mt-1 text-sm text-red-600">{error}</p>} {/* Display error message */}
    </div>
);

interface NewsSearchFormProps {
    onNewsSelected: (url: string) => void;
    newsApiKey: string;
    setNewsApiKey: (key: string) => void;
    loadingAnalysis: boolean; // To disable search when analysis is ongoing
}

const NewsSearchForm = ({ onNewsSelected, newsApiKey, setNewsApiKey, loadingAnalysis }: NewsSearchFormProps) => {
    const [showAdvancedFilters, setShowAdvancedFilters] = useState<boolean>(false); // New state for toggling advanced filters
    const [searchKeyword, setSearchKeyword] = useState<string>('');
    const [from_date, setFromDate] = useState<Date | null>(null); // Change to Date object, initialized to null
    const [to_date, setToDate] = useState<Date | null>(null); // Change to Date object, initialized to null
    const [language, setLanguage] = useState<string>('ko');
    const [sources, setSources] = useState<string>('');
    const [sort_by, setSortBy] = useState<'relevancy' | 'popularity' | 'publishedAt'>('publishedAt');
    const [domains, setDomains] = useState<string>(''); // New state
    const [excludeDomains, setExcludeDomains] = useState<string>(''); // New state
    const [qInTitle, setQInTitle] = useState<string>(''); // New state

    const [searchResults, setSearchResults] = useState<NewsItem[]>([]);
    const [searchLoading, setSearchLoading] = useState<boolean>(false);
    const [searchError, setSearchError] = useState<string | null>(null);

    const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

    const performSearch = async () => {
        setSearchLoading(true);
        setSearchError(null);
        setSearchResults([]);

        try {
            let queryParams = new URLSearchParams();
            queryParams.append('q', searchKeyword);
            if (from_date) queryParams.append('from_date', from_date.toISOString().split('T')[0]); // Convert Date to YYYY-MM-DD
            if (to_date) queryParams.append('to_date', to_date.toISOString().split('T')[0]); // Convert Date to YYYY-MM-DD
            if (language) queryParams.append('language', language);
            if (sources) queryParams.append('sources', sources);
            if (sort_by) queryParams.append('sort_by', sort_by);
            if (domains) queryParams.append('domains', domains); // New parameter
            if (excludeDomains) queryParams.append('exclude_domains', excludeDomains); // New parameter
            if (qInTitle) queryParams.append('q_in_title', qInTitle); // New parameter
            if (newsApiKey) queryParams.append('news_api_key', newsApiKey);

            const response = await fetch(`${backendUrl}/search?${queryParams.toString()}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
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

    const handleResultClick = (url: string) => {
        onNewsSelected(url); // Pass the URL up to App.tsx
        setSearchResults([]); // Clear search results after selection
        setSearchKeyword(''); // Clear search keyword
    };

    return (
        <aside className="lg:col-span-1 p-6 bg-white rounded-xl shadow-lg">
            <div className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-800">뉴스 검색</h2>
                <InputField id="searchKeyword" label="검색 키워드" value={searchKeyword} onChange={(e) => setSearchKeyword(e.target.value)} placeholder="예: 인공지능, 경제" disabled={searchLoading || loadingAnalysis} />
                
                {/* Toggle for Advanced Filters */}
                <button 
                    type="button" 
                    onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                    className="text-primary-600 hover:text-primary-700 text-sm font-medium focus:outline-none focus:underline mt-2 mb-4"
                >
                    {showAdvancedFilters ? '고급 필터 숨기기 ▲' : '고급 필터 보기 ▼'}
                </button>

                {showAdvancedFilters && (
                    <div className="space-y-4"> {/* Added space-y-4 for better spacing within advanced filters */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label htmlFor="fromDate" className="block text-sm font-medium text-gray-700 mb-1">시작일</label>
                                <DatePicker
                                    id="fromDate"
                                    selected={from_date}
                                    onChange={(date: Date | null) => setFromDate(date)}
                                    dateFormat="yyyy-MM-dd"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
                                    disabled={searchLoading || loadingAnalysis}
                                    placeholderText="YYYY-MM-DD"
                                />
                            </div>
                            <div>
                                <label htmlFor="toDate" className="block text-sm font-medium text-gray-700 mb-1">종료일</label>
                                <DatePicker
                                    id="toDate"
                                    selected={to_date}
                                    onChange={(date: Date | null) => setToDate(date)}
                                    dateFormat="yyyy-MM-dd"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
                                    disabled={searchLoading || loadingAnalysis}
                                    placeholderText="YYYY-MM-DD"
                                />
                            </div>
                            
                            <div>
                                <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-1">언어</label>
                                <select id="language" value={language} onChange={(e) => setLanguage(e.target.value)} disabled={searchLoading || loadingAnalysis} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed">
                                    <option value="ko">한국어</option>
                                    <option value="en">영어</option>
                                    <option value="jp">일본어</option>
                                    {/* Add more languages as supported by NewsAPI */}
                                </select>
                            </div>

                            <div>
                                <label htmlFor="sortBy" className="block text-sm font-medium text-gray-700 mb-1">정렬 기준</label>
                                <select id="sortBy" value={sort_by} onChange={(e) => setSortBy(e.target.value as "relevancy" | "popularity" | "publishedAt")} disabled={searchLoading || loadingAnalysis} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed">
                                    <option value="publishedAt">최신순</option>
                                    <option value="relevancy">관련성</option>
                                    <option value="popularity">인기순</option>
                                </select>
                            </div>
                        </div>
                        
                        <InputField id="sources" label="뉴스 소스 (쉼표로 구분)" value={sources} onChange={(e) => setSources(e.target.value)} placeholder="예: bbc-news,the-verge" disabled={searchLoading || loadingAnalysis} />
                        <InputField id="domains" label="포함할 도메인 (쉼표로 구분)" value={domains} onChange={(e) => setDomains(e.target.value)} placeholder="예: bbc.co.uk,techcrunch.com" disabled={searchLoading || loadingAnalysis} /> {/* New InputField */}
                        <InputField id="excludeDomains" label="제외할 도메인 (쉼표로 구분)" value={excludeDomains} onChange={(e) => setExcludeDomains(e.target.value)} placeholder="예: ynet.co.il" disabled={searchLoading || loadingAnalysis} /> {/* New InputField */}
                        <InputField id="qInTitle" label="제목에 포함된 키워드 (선택 사항)" value={qInTitle} onChange={(e) => setQInTitle(e.target.value)} placeholder="예: COVID-19" disabled={searchLoading || loadingAnalysis} /> {/* New InputField */}
                    </div>
                )}
                <InputField id="newsApiKey" label="NewsAPI Key (선택 사항)" type="password" value={newsApiKey} onChange={(e) => setNewsApiKey(e.target.value)} placeholder="NewsAPI 키 입력" disabled={searchLoading || loadingAnalysis} />

                <button onClick={performSearch} disabled={searchLoading || !searchKeyword || loadingAnalysis} className="w-full bg-primary-600 text-white font-bold py-3 px-4 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors">
                    {searchLoading ? '검색 중...' : '뉴스 검색'}
                </button>

                {searchError && <div className="text-red-600 bg-red-50 p-3 rounded-lg text-sm"><strong>오류:</strong> {searchError}</div>}
                
                {searchLoading && (
                    <div className="flex justify-center items-center py-4">
                        <Spinner />
                    </div>
                )}

                {searchResults.length > 0 && (
                    <div className="space-y-3 max-h-80 overflow-y-auto pr-2"> {/* Increased max-h and added pr-2 for scrollbar */}
                        <h3 className="font-semibold text-gray-700">검색 결과 ({searchResults.length}개)</h3>
                        {searchResults.map((item, index) => (
                            <div key={index} onClick={() => handleResultClick(item.url)} className="cursor-pointer p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors shadow-sm">
                                <p className="text-blue-700 font-medium text-base mb-1">{item.title}</p>
                                {item.description && <p className="text-xs text-gray-600 line-clamp-2">{item.description}</p>} {/* Show description */}
                                <p className="text-xs text-gray-500 mt-1">{item.source_name} - {new Date(item.published_at).toLocaleDateString()}</p>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </aside>
    );
};

export default NewsSearchForm;