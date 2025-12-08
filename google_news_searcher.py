"""
Google News Searcher - Hard Facts Data Provider

Purpose:
- Eradicate AI hallucinations by providing factual news data
- Use SerpApi to fetch real-time Google News results
- Replace LLM's "memory" with hard, timestamped facts

Architecture:
- Independent module for objective data acquisition
- Time-filtered results (prevent historical confusion)
- Graceful error handling (never crash the application)
- Cost-aware (SerpApi free tier: 100 requests/month)

Author: Data Engineer / Integration Specialist
Date: 2025-12-08
Sprint: 2 - Truth Over Hallucination
"""

import os
import logging
from typing import List, Dict, Optional
from serpapi import GoogleSearch
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GoogleNewsSearcher:
    """
    Google News Searcher using SerpApi
    
    Features:
    - Fetches real Google News results (not LLM hallucinations)
    - Time-filtered to prevent outdated information
    - Standardized output format
    - Graceful degradation on errors
    
    Cost Awareness:
    - Free tier: 100 requests/month
    - Use sparingly in production
    - Consider caching for repeated queries
    """
    
    def __init__(self):
        """
        Initialize GoogleNewsSearcher
        
        Reads SERPAPI_API_KEY from Config
        Sets up error handling for missing credentials
        """
        self.api_key = Config.get("SERPAPI_API_KEY")
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            logger.warning("⚠️  SERPAPI_API_KEY not found. News search disabled.")
            logger.info("💡 Set SERPAPI_API_KEY in .env to enable Google News search")
        else:
            logger.info("✅ GoogleNewsSearcher initialized")
    
    def search_news(self, symbol: str, days: int = 3) -> List[Dict[str, str]]:
        """
        Search Google News for a stock symbol with time filter
        
        This is the First Line of Defense against hallucination:
        - Real Google News API results
        - Time-bounded (last N days only)
        - Timestamped sources
        
        Args:
            symbol: Stock ticker symbol (e.g., "NVDA", "AAPL")
            days: Number of days to look back (default: 3)
                  Supported: 1 (24h), 3, 7 (week), 30 (month), 365 (year)
        
        Returns:
            List of news articles, each containing:
            - title: Article headline
            - link: Full URL to article
            - source: Media outlet name
            - date: Publication time (e.g., "2 hours ago")
            - snippet: Brief summary
            
            Returns empty list [] on error (graceful degradation)
        
        Examples:
            >>> searcher = GoogleNewsSearcher()
            >>> news = searcher.search_news("TSLA", days=3)
            >>> for article in news[:3]:
            ...     print(f"{article['date']}: {article['title']}")
        """
        if not self.enabled:
            logger.debug(f"News search skipped for {symbol} (API key not set)")
            return []
        
        try:
            # Construct search query
            # Format: "STOCK_SYMBOL stock" (adding "stock" improves relevance)
            query = f"{symbol} stock"
            
            # Time filter (qdr parameter)
            # Format: qdr:dN where N = number of days
            # Special values: h (hour), d (day), w (week), m (month), y (year)
            time_filter = f"qdr:d{days}"
            
            # SerpApi parameters
            params = {
                "engine": "google",
                "q": query,
                "tbm": "nws",           # News mode
                "tbs": time_filter,     # Time filter (防止幻覺的第一道防線)
                "api_key": self.api_key,
                "num": 10,              # Number of results (max 10 for free tier)
                "gl": "us",             # Country: United States
                "hl": "en"              # Language: English
            }
            
            logger.info(f"🔍 Searching Google News: {symbol} (last {days} days)")
            
            # Execute search
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Extract and standardize news results
            news_results = results.get("news_results", [])
            
            if not news_results:
                logger.warning(f"⚠️  No news found for {symbol} in last {days} days")
                return []
            
            # Standardize output format
            standardized_news = []
            for article in news_results:
                standardized_article = {
                    "title": article.get("title", "No title"),
                    "link": article.get("link", ""),
                    "source": article.get("source", "Unknown source"),
                    "date": article.get("date", "Unknown date"),
                    "snippet": article.get("snippet", "")
                }
                standardized_news.append(standardized_article)
            
            logger.info(f"✅ Found {len(standardized_news)} news articles for {symbol}")
            return standardized_news
            
        except Exception as e:
            # Graceful degradation: log error and return empty list
            logger.error(f"❌ Error fetching news for {symbol}: {type(e).__name__}")
            logger.error(f"   Details: {str(e)}")
            
            # Specific error handling
            if "Invalid API key" in str(e):
                logger.error("💡 Check SERPAPI_API_KEY in .env")
                self.enabled = False  # Disable to prevent repeated failures
            elif "quota" in str(e).lower() or "limit" in str(e).lower():
                logger.error("💡 API quota exceeded (free tier: 100/month)")
                self.enabled = False
            
            return []  # Never crash - return empty list
    
    def format_news_summary(self, news: List[Dict[str, str]], max_articles: int = 5) -> str:
        """
        Format news articles into a readable summary
        
        Args:
            news: List of news articles from search_news()
            max_articles: Maximum number of articles to include
        
        Returns:
            Formatted string with news headlines and timestamps
        """
        if not news:
            return "📰 無相關新聞"
        
        summary = f"📰 最新新聞 ({len(news)} 則):\n"
        
        for i, article in enumerate(news[:max_articles], 1):
            summary += f"\n{i}. {article['title']}\n"
            summary += f"   📅 {article['date']} | {article['source']}\n"
            
            if article.get('snippet'):
                # Truncate snippet to 100 chars
                snippet = article['snippet'][:100]
                if len(article['snippet']) > 100:
                    snippet += "..."
                summary += f"   💬 {snippet}\n"
        
        if len(news) > max_articles:
            summary += f"\n   ... 還有 {len(news) - max_articles} 則新聞"
        
        return summary


# Module test
if __name__ == "__main__":
    print("🧪 Testing GoogleNewsSearcher\n")
    
    searcher = GoogleNewsSearcher()
    
    if searcher.enabled:
        print("Test: Searching news for AAPL...")
        news = searcher.search_news("AAPL", days=3)
        
        if news:
            print(f"\n✅ Found {len(news)} articles\n")
            print(searcher.format_news_summary(news, max_articles=3))
        else:
            print("❌ No news found")
    else:
        print("⚠️  API key not configured")
        print("💡 Set SERPAPI_API_KEY in .env to test")
