import React from 'react';
import { NewsItem } from '../types'; // Import NewsItem

interface AnalysisResult extends NewsItem {
  summary: string;
  sentiment_label: string;
  sentiment_score: number;
}

interface ResultDisplayProps {
    result: AnalysisResult;
}

const ResultDisplay = ({ result }: ResultDisplayProps) => {
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

export default ResultDisplay;
