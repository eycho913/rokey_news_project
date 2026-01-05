// frontend/src/types.ts

export interface NewsItem {
    title: string;
    description: string;
    url: string;
    source_name: string;
    published_at: string;
}

export type LLMProvider = 'gemini' | 'openai';
