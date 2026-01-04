from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, Literal, List
import json
import os # Import the os module to access environment variables

from services.news_client import NewsClient, NewsAPIException, NewsItem, SentimentResult
from services.text_extract import extract_and_clean

# Import both Gemini and OpenAI services
from services.summarizer import GeminiSummarizer
from services.sentiment import GeminiSentimentAnalyzer
from services.openai_summarizer import OpenAISummarizer
from services.openai_sentiment import OpenAISentimentAnalyzer

# Generic exceptions
from services.summarizer import SummarizerException
from services.sentiment import SentimentException


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
    # LLM Configuration fields are now Optional again for UI input, with env vars taking precedence
    llm_provider: Optional[Literal["gemini", "openai"]] = None
    llm_api_key: Optional[str] = None
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
    news_api_key: Optional[str] = Query(None, alias="news_api_key", description="Optional NewsAPI Key, backend env var takes precedence"),
):
    # Prioritize NEWS_API_KEY from environment variable
    news_api_key_used = os.getenv("NEWS_API_KEY") or news_api_key
    
    if not news_api_key_used:
        raise HTTPException(
            status_code=500, detail="NEWS_API_KEY not configured on the backend server or provided in UI."
        )
    
    news_client = NewsClient(api_key=news_api_key_used)
    try:
        articles = news_client.get_news(keyword=q, page_size=page_size)
        return articles
    except NewsAPIException as e:
        raise HTTPException(status_code=500, detail=f"News search failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during news search: {e}")


@app.post("/analyze")
async def analyze_news_endpoint(request: AnalyzeRequest):
    # Prioritize LLM configuration from environment variables, fallback to request body
    llm_api_key_used = os.getenv("LLM_API_KEY") or request.llm_api_key
    if not llm_api_key_used:
        raise HTTPException(status_code=500, detail="LLM_API_KEY not configured on the backend server or provided in UI.")
    
    llm_provider_used = os.getenv("LLM_PROVIDER") or request.llm_provider or "gemini" # Default to gemini
    llm_model_used = os.getenv("LLM_MODEL") or request.llm_model
    llm_api_base_used = os.getenv("LLM_API_BASE") or (str(request.llm_api_base) if request.llm_api_base else None)

    news_client = NewsClient() # Initialize without API key if only scraping by URL

    # Based on the provider, instantiate the correct services
    if llm_provider_used == "gemini":
        summarizer = GeminiSummarizer(api_key=llm_api_key_used)
        sentiment_analyzer = GeminiSentimentAnalyzer(api_key=llm_api_key_used)
    elif llm_provider_used == "openai":
        summarizer = OpenAISummarizer(
            api_key=llm_api_key_used,
            model=llm_model_used or "gpt-3.5-turbo", # Default model
            api_base=llm_api_base_used,
        )
        sentiment_analyzer = OpenAISentimentAnalyzer(
            api_key=llm_api_key_used,
            model=llm_model_used or "gpt-3.5-turbo", # Default model
            api_base=llm_api_base_used,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported LLM provider configured on backend: {llm_provider_used}")

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

