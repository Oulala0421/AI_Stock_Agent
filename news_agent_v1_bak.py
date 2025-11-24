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
    - Market Outlook: fetches upcoming earnings and macro events
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

    def get_market_outlook(self) -> str:
        """
        獲取未來 7 天市場展望 (簡化版：上調/下調/波動注意)
        """
        if not self.api_key:
            return "Market outlook unavailable (API key not configured)."
            
        prompt = """
        作為資深美股分析師，請整理「未來 7 天」美股市場最重要的財經事件與財報發布。
        
        請將事件歸納為以下三類，並**嚴格移除所有引用來源標記**（如 [1][2]）：
        
        📈 **上調注意** (利多潛力/強勢板塊)
        📉 **下調注意** (利空風險/弱勢板塊)
        ⚡ **波動注意** (重大財報/總經數據/會議)
        
        格式要求：
        - 使用繁體中文（台灣）。
        - 每一類別下列出 1-2 個最重要事件。
        - 若某類別無重大事件，可略過。
        - 每行格式：`[MM/DD] 事件名稱 - 簡短關鍵影響`
        - **絕對不要**包含 [1], [2] 等引用標記。
        - 保持極度簡潔，不要長篇大論。
        """
        
        try:
            return self._fetch_from_perplexity(prompt, max_tokens=600)
        except Exception as e:
            print(f"❌ Market outlook fetch failed: {e}")
            return "暫無法獲取市場展望。"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout))
    )
    def _fetch_news_with_retry(self, symbol: str) -> str:
        """
        Internal method with retry logic for API calls (for single stock).
        """
        prompt = self._build_prompt(symbol)
        return self._fetch_from_perplexity(prompt)

    def _fetch_from_perplexity(self, prompt: str, max_tokens: int = 300) -> str:
        """
        Generic method to call Perplexity API.
        """
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
            "max_tokens": max_tokens,
            "temperature": 0.2
        }
        
        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=30  # Increased timeout for longer queries
        )
        
        response.raise_for_status()
        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"]["content"]
            return self._format_news_output(content)
        else:
            raise ValueError("Invalid API response structure")
    
    def _build_prompt(self, symbol: str) -> str:
        """
        Build optimized prompt for financial news extraction.
        """
        return f"""Analyze {symbol} stock with focus on GARP strategy factors:

1. Latest news and market sentiment (bullish/bearish)
2. Recent earnings, revenue growth, or guidance updates
3. Major catalysts (product launches, partnerships, regulatory changes)

Provide EXACTLY 3 concise bullet points (max 1 sentence each). Be factual and data-driven. Output in Traditional Chinese (Taiwan)."""
    
    def _format_news_output(self, content: str) -> str:
        """
        Clean and format the API response into mobile-friendly output.
        """
        lines = content.strip().split('\n')
        formatted_lines = []
        for line in lines:
            line = line.strip()
            if line:
                if not line.startswith('-') and not line.startswith('•') and not line.startswith('1.'):
                    line = f"- {line}"
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines) if formatted_lines else "No significant news"
