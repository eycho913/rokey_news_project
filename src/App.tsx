import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './App.css';

// 샘플 뉴스 데이터
const sampleNews = [
  {
    id: 1,
    title: 'React 19 출시! 새로운 기능은?',
    content: 'React 19이 공식적으로 출시되었습니다. 이번 버전에는 자동 메모이제이션, 새로운 훅 등이 포함되어 개발 경험을 크게 향상시킬 것으로 기대됩니다.',
    link: '#',
  },
  {
    id: 2,
    title: 'Vite 5.0, 빌드 성능 대폭 개선',
    content: '차세대 프론트엔드 툴 Vite가 5.0 버전을 릴리스했습니다. SWC 기반의 컴파일러를 도입하여 이전보다 훨씬 빠른 빌드 속도를 자랑합니다.',
    link: '#',
  },
  {
    id: 3,
    title: 'TypeScript 5.5, 타입 추론 능력 강화',
    content: 'TypeScript의 최신 버전인 5.5가 공개되었습니다. 더욱 강력해진 타입 추론과 개선된 에러 메시지로 안정적인 코드 작성을 돕습니다.',
    link: '#',
  },
];

// 뉴스 기사 컴포넌트
function NewsArticle({ title, content, link }: { title: string, content: string, link: string }) {
  return (
    <article className="article">
      <h3>{title}</h3>
      <p>{content}</p>
      <a href={link} target="_blank" rel="noopener noreferrer">
        기사 더보기
      </a>
    </article>
  );
}

function App() {
  const [readmeContent, setReadmeContent] = useState('');

  useEffect(() => {
    // public 폴더의 README.md 파일을 fetch합니다.
    fetch('/README.md')
      .then((response) => {
        if (response.ok) {
          return response.text();
        }
        throw new Error('README.md 파일을 불러오는 데 실패했습니다.');
      })
      .then((text) => {
        setReadmeContent(text);
      })
      .catch((error) => {
        console.error(error);
        setReadmeContent('README.md 내용을 불러올 수 없습니다.');
      });
  }, []);

  return (
    <div className="app">
      <header>
        <h1>Rokey News Project</h1>
      </header>
      <main>
        <section className="news-section">
          {sampleNews.map((news) => (
            <NewsArticle
              key={news.id}
              title={news.title}
              content={news.content}
              link={news.link}
            />
          ))}
        </section>
        <aside className="readme-section">
          <h2>Project README</h2>
          <ReactMarkdown>{readmeContent}</ReactMarkdown>
        </aside>
      </main>
    </div>
  );
}

export default App;
