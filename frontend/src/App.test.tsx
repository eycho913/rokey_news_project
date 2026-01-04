import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';

describe('App', () => {
  it('renders main heading', () => {
    render(<App />);
    expect(screen.getByText(/뉴스 요약 & 감성 분석/i)).toBeInTheDocument();
  });

  it('renders news search section heading', () => {
    render(<App />);
    expect(screen.getByText(/뉴스 검색/i)).toBeInTheDocument();
  });

  it('renders article analysis section heading', () => {
    render(<App />);
    expect(screen.getByText(/기사 분석/i)).toBeInTheDocument();
  });
});
