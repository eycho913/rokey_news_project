from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, Literal, List
import json
import os # Import the os module to access environment variables

from backend-api.services.news_client import NewsClient, NewsAPIException, NewsItem, SentimentResult
from backend-api.services.text_extract import extract_and_clean

# Import both Gemini and OpenAI services
from backend-api.services.summarizer import GeminiSummarizer
from backend-api.services.sentiment import GeminiSentimentAnalyzer
from backend-api.services.openai_summarizer import OpenAISummarizer
from backend-api.services.openai_sentiment import OpenAISentimentAnalyzer

# Generic exceptions
from backend-api.services.summarizer import SummarizerException
from backend-api.services.sentiment import SentimentException


app = FastAPI()

# Add CORS middleware
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",  # Default Vite development server port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request and response
class AnalyzeRequest(BaseModel):
    news_url: HttpUrl
    summary_length: Literal["short", "medium", "long"] = "medium"
    # news_api_key: Optional[str] = None # Removed for security, now handled via env vars in /search or backend config

    # LLM Configuration
    llm_provider: Literal["gemini", "openai"] = "gemini"
    llm_api_key: str
    llm_model: Optional[str] = None
    llm_api_base: Optional[HttpUrl] = None

class AnalyzeResponse(BaseModel):
    title: str
    description: Optional[str]
    url: HttpUrl
    source_name: str
    published_at: str
    summary: Optional[str] = None
    sentiment_label: str
    sentiment_score: float

@app.get("/")
async def read_root():
    return {"message": "FastAPI backend is running!"}

@app.get("/search", response_model=List[NewsItem])
async def search_news_endpoint(
    q: str = Query(..., description="Keyword to search for news articles"),
    page_size: int = Query(20, ge=1, le=100, description="Number of articles to return (max 100)"),
    # For now, `from_date` and `to_date` are not exposed via API, but can be added later.
):
    news_api_key = os.getenv("NEWS_API_KEY")
    if not news_api_key:
        raise HTTPException(
            status_code=500, detail="NEWS_API_KEY not configured on the backend server."
        )
    
    news_client = NewsClient(api_key=news_api_key)
    try:
        articles = news_client.get_news(keyword=q, page_size=page_size)
        return articles
    except NewsAPIException as e:
        raise HTTPException(status_code=500, detail=f"News search failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during news search: {e}")


@app.post("/analyze")
async def analyze_news_endpoint(request: AnalyzeRequest):
    # NEWS_API_KEY is not directly used here for scraping, only for search.
    # The news_client here only needs the URL to scrape.
    news_client = NewsClient() # Initialize without API key if only scraping by URL

    # Based on the provider, instantiate the correct services
    if request.llm_provider == "gemini":
        summarizer = GeminiSummarizer(api_key=request.llm_api_key)
        sentiment_analyzer = GeminiSentimentAnalyzer(api_key=request.llm_api_key)
    elif request.llm_provider == "openai":
        summarizer = OpenAISummarizer(
            api_key=request.llm_api_key,
            model=request.llm_model or "gpt-3.5-turbo", # Default model
            api_base=str(request.llm_api_base) if request.llm_api_base else None,
        )
        sentiment_analyzer = OpenAISentimentAnalyzer(
            api_key=request.llm_api_key,
            model=request.llm_model or "gpt-3.5-turbo", # Default model
            api_base=str(request.llm_api_base) if request.llm_api_base else None,
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported LLM provider.")

    try:
        # 1. Get news content from URL
        news_item: Optional[NewsItem] = news_client.get_news_from_url(str(request.news_url))
        
        if not news_item:
            raise HTTPException(status_code=400, detail="Could not fetch news content from the provided URL. Please check the URL or try another one.")

        # 2. Clean the content
        news_item.processed_content = extract_and_clean(news_item)
        
        # 3. Summarize
        if news_item.processed_content:
            try:
                news_item.summary = summarizer.summarize(news_item.processed_content, request.summary_length)
            except SummarizerException as e:
                news_item.summary = f"Summarization failed: {e}"
        else:
            news_item.summary = "No content to summarize."
        
        # 4. Sentiment Analysis
        if news_item.processed_content:
            try:
                news_item.sentiment = sentiment_analyzer.analyze(news_item.processed_content)
            except SentimentException as e:
                news_item.sentiment = SentimentResult(label="Neutral (Analysis Failed)", score=3.0) 
        else:
            news_item.sentiment = SentimentResult(label="Neutral (No Content)", score=3.0)
        
        # Prepare response
        response_data = AnalyzeResponse(
            title=news_item.title,
            description=news_item.description,
            url=news_item.url,
            source_name=news_item.source_name,
            published_at=news_item.published_at,
            summary=news_item.summary,
            sentiment_label=news_item.sentiment.label,
            sentiment_score=news_item.sentiment.score
        )
        return response_data

    except NewsAPIException as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the news: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unknown error occurred: {e}")

