import os
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Optional

class NewsAgent:
    """
    News Intelligence Agent using Perplexity AI's sonar-pro model.
    Provides real-time market intelligence for GARP strategy decisions.
    
    Features:
    - Defensive programming: graceful degradation if API key missing
    - Retry logic for transient failures
    - Cost optimization: designed to be called selectively (PASS/WATCHLIST only)
    """
    
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.model = "sonar-pro"
        self.endpoint = "https://api.perplexity.ai/chat/completions"
        
        if not self.api_key:
            print("⚠️ PERPLEXITY_API_KEY not found. News features will use fallback mode.")
    
    def get_stock_news(self, symbol: str) -> str:
        """
        Fetch concise news summary for a given stock symbol.
        
        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")
        
        Returns:
            str: Formatted news summary (max 3 bullet points) or fallback message
        """
        # Cost Control: If no API key, return safe fallback immediately
        if not self.api_key:
            return "News unavailable (API key not configured)"
        
        try:
            return self._fetch_news_with_retry(symbol)
        except Exception as e:
            print(f"❌ News fetch failed for {symbol}: {e}")
            return "News unavailable (API error)"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout))
    )
    def _fetch_news_with_retry(self, symbol: str) -> str:
        """
        Internal method with retry logic for API calls.
        
        Raises:
            Exception: If all retries exhausted or non-retryable error occurs
        """
        prompt = self._build_prompt(symbol)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a financial analyst specializing in GARP (Growth at a Reasonable Price) investing. Provide concise, actionable market intelligence."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 300,  # Keep it concise
            "temperature": 0.2  # Lower temperature for factual responses
        }
        
        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=15  # 15 second timeout
        )
        
        # Raise for HTTP errors (4xx, 5xx)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract content from response
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"]["content"]
            return self._format_news_output(content)
        else:
            raise ValueError("Invalid API response structure")
    
    def _build_prompt(self, symbol: str) -> str:
        """
        Build optimized prompt for financial news extraction.
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            str: Formatted prompt for Perplexity API
        """
        return f"""Analyze {symbol} stock with focus on GARP strategy factors:

1. Latest news and market sentiment (bullish/bearish)
2. Recent earnings, revenue growth, or guidance updates
3. Major catalysts (product launches, partnerships, regulatory changes)

Provide EXACTLY 3 concise bullet points (max 1 sentence each). Be factual and data-driven."""
    
    def _format_news_output(self, content: str) -> str:
        """
        Clean and format the API response into mobile-friendly output.
        
        Args:
            content: Raw content from Perplexity API
        
        Returns:
            str: Formatted news summary
        """
        # Clean up the content
        lines = content.strip().split('\n')
        
        # Filter out empty lines and ensure we have bullet points
        formatted_lines = []
        for line in lines:
            line = line.strip()
            if line:
                # Ensure each line starts with a bullet point
                if not line.startswith('-') and not line.startswith('•'):
                    line = f"- {line}"
                formatted_lines.append(line)
        
        # Limit to 3 bullet points maximum
        formatted_lines = formatted_lines[:3]
        
        return '\n'.join(formatted_lines) if formatted_lines else "No significant news"
