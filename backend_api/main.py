from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, Literal, List
import json
import os
import time # Import time for logging
from datetime import date # Import date for query parameters

# Cache imports
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

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

import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


app = FastAPI()

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Request {request.method} {request.url.path} processed in {process_time:.4f} seconds with status {response.status_code}")
    response.headers["X-Process-Time"] = str(process_time)
    return response

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

@app.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    logger.info("FastAPI cache initialized with InMemoryBackend.")

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
    logger.info("Root endpoint accessed.")
    return {"message": "FastAPI backend is running!"}

@app.get("/search", response_model=List[NewsItem])
@cache(expire=300) # Cache search results for 5 minutes
async def search_news_endpoint(
    q: str = Query(..., description="Keyword to search for news articles"),
    from_date: Optional[date] = Query(None, description="Start date for published articles (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="End date for published articles (YYYY-MM-DD)"),
    language: str = Query("ko", description="Language of the articles (e.g., 'en', 'ko')"),
    sources: Optional[str] = Query(None, description="Comma-separated list of news sources (e.g., 'bbc-news,the-verge')"),
    sort_by: Literal["relevancy", "popularity", "publishedAt"] = Query("publishedAt", description="Order to sort the articles in"),
    page_size: int = Query(20, ge=1, le=100, description="Number of articles to return (max 100)"),
    domains: Optional[str] = Query(None, description="Comma-separated list of domains to search within (e.g., 'bbc.co.uk,techcrunch.com')"), # New parameter
    exclude_domains: Optional[str] = Query(None, description="Comma-separated list of domains to exclude (e.g., 'ynet.co.il')"), # New parameter
    q_in_title: Optional[str] = Query(None, description="Search only for articles where the keyword is in the title"), # New parameter
    news_api_key: Optional[str] = Query(None, alias="news_api_key", description="Optional NewsAPI Key, backend env var takes precedence"),
):
    logger.info(f"Search endpoint accessed with keyword: {q}, from_date: {from_date}, to_date: {to_date}, language: {language}, sources: {sources}, sort_by: {sort_by}, page_size: {page_size}, domains: {domains}, exclude_domains: {exclude_domains}, q_in_title: {q_in_title}") # Updated log
    # Prioritize NEWS_API_KEY from environment variable
    news_api_key_used = os.getenv("NEWS_API_KEY") or news_api_key
    
    if not news_api_key_used:
        logger.error("NEWS_API_KEY not configured for search endpoint.")
        raise HTTPException(
            status_code=500, detail="NEWS_API_KEY not configured on the backend server or provided in UI."
        )
    
    news_client = NewsClient(api_key=news_api_key_used)
    try:
        articles = news_client.get_news(
            keyword=q,
            from_date=from_date,
            to_date=to_date,
            language=language,
            sources=sources,
            sort_by=sort_by,
            page_size=page_size,
            domains=domains, # Pass new parameter
            exclude_domains=exclude_domains, # Pass new parameter
            q_in_title=q_in_title # Pass new parameter
        )
        logger.info(f"Successfully retrieved {len(articles)} articles for keyword: {q}")
        return articles
    except NewsAPIException as e:
        logger.error(f"NewsAPIException in search endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"News search failed: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during news search: {e}", exc_info=True)
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
        start_get_content = time.time()
        news_item: Optional[NewsItem] = news_client.get_news_from_url(str(request.news_url))
        logger.info(f"news_client.get_news_from_url took {time.time() - start_get_content:.2f} seconds.")
        
        if not news_item:
            raise HTTPException(status_code=400, detail="Could not fetch news content from the provided URL. Please check the URL or try another one.")

        # 2. Clean the content
        start_clean_content = time.time()
        news_item.processed_content = extract_and_clean(news_item)
        logger.info(f"extract_and_clean took {time.time() - start_clean_content:.2f} seconds.")
        
        # 3. Summarize
        if news_item.processed_content:
            try:
                start_summarize = time.time()
                news_item.summary = summarizer.summarize(news_item.processed_content, request.summary_length)
                logger.info(f"summarizer.summarize took {time.time() - start_summarize:.2f} seconds.")
            except SummarizerException as e:
                news_item.summary = f"Summarization failed: {e}"
        else:
            news_item.summary = "No content to summarize."
        
        # 4. Sentiment Analysis
        if news_item.processed_content:
            try:
                start_sentiment = time.time()
                news_item.sentiment = sentiment_analyzer.analyze(news_item.processed_content)
                logger.info(f"sentiment_analyzer.analyze took {time.time() - start_sentiment:.2f} seconds.")
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

