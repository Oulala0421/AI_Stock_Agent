"""
News Agent V3 - Commentary Engine (Fact-Opinion Decoupled)

Architecture Evolution:
V1 (Old): LLM searches and analyzes (hallucination risk)
V2 (Hybrid): Perplexity + local logic (still unstable)
V3 (Current): GoogleNewsSearcher (facts) + NewsAgent (commentary)

Role: AI Logic Designer
Purpose: Convert NewsAgent from "Searcher" to "Commentator"
- Accept hard facts from GoogleNewsSearcher
- Generate structured JSON analysis
- No search capability (fact-fetching delegated to GoogleNewsSearcher)

Design Principles:
- Separation of Concerns: Facts (Google) vs Opinion (AI)
- Structured Output: JSON mode for reliability
- Graceful Degradation: Handle empty news gracefully
- Cost Efficiency: Use Gemini 1.5 Flash (cheap, fast, long context)

Author: AI Logic Designer
Date: 2025-12-08
Sprint: 2 - Truth Over Hallucination
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsAgent:
    """
    News Commentator using Gemini 1.5 Flash
    
    Role: Analyst, NOT Searcher
    - Receives hard facts from GoogleNewsSearcher
    - Provides structured investment commentary
    - Outputs JSON for integration with StockHealthCard
    
    Architecture:
    - Input: List of news articles (from GoogleNewsSearcher)
    - Process: LLM analysis with structured prompt
    - Output: JSON with sentiment, moat impact, prediction
    
    Why Gemini 1.5 Flash?
    - Cost: $0.075/1M input tokens (cheaper than GPT-4)
    - Speed: Fast response time
    - Context: 1M token window (handles many news articles)
    - JSON Mode: Native support for structured output
    """
    
    def __init__(self):
        """
        Initialize NewsAgent with Gemini API
        
        Fallbacks:
        1. Gemini (primary)
        2. Disabled if no API key
        """
        self.api_key = Config.get("GEMINI_API_KEY")
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            logger.warning("⚠️  GEMINI_API_KEY not found. News analysis disabled.")
            logger.info("💡 Set GEMINI_API_KEY in .env to enable AI commentary")
            return
        
        try:
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            
            # Safety settings - BLOCK_NONE for all categories
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # Try Gemini 2.5 Flash first (thinking model - needs more tokens)
            try:
                self.model = genai.GenerativeModel(
                    'gemini-2.5-flash',
                    generation_config={
                        "temperature": 0.2,  # Lower for consistency (value investing)
                        "top_p": 0.95,
                        "max_output_tokens": 8192,  # High limit for thinking model
                        "response_mime_type": "application/json"
                    },
                    safety_settings=safety_settings
                )
                self.model_name = "Gemini 2.5 Flash"
                logger.info("✅ NewsAgent initialized (Gemini 2.5 Flash)")
                
            except Exception as e:
                # Fallback to Gemini 2.0 Flash (more stable)
                logger.warning(f"⚠️  Gemini 2.5 Flash failed: {e}")
                logger.info("🔄 Falling back to Gemini 2.0 Flash...")
                
                self.model = genai.GenerativeModel(
                    'gemini-2.0-flash',
                    generation_config={
                        "temperature": 0.2,
                        "top_p": 0.95,
                        "max_output_tokens": 4096,
                        "response_mime_type": "application/json"
                    },
                    safety_settings=safety_settings
                )
                self.model_name = "Gemini 2.0 Flash"
                logger.info("✅ NewsAgent initialized (Gemini 2.0 Flash - Fallback)")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {e}")
            self.enabled = False
    
    def analyze_news(self, symbol: str, news_list: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """
        Analyze news articles and generate structured investment commentary
        
        This is the core "Commentator" function:
        - Receives hard facts (from GoogleNewsSearcher)
        - Generates AI opinion (structured JSON)
        - NO hallucination (facts are pre-verified)
        
        Args:
            symbol: Stock ticker (e.g., "TSLA")
            news_list: List of news articles from GoogleNewsSearcher
                      Each article has: title, date, source, snippet
        
        Returns:
            Structured analysis (JSON):
            {
                "sentiment": "Positive/Negative/Neutral",
                "sentiment_score": 75,  # -100 to +100
                "moat_impact": "Strengthened/Weakened/Unchanged",
                "prediction": "Bullish/Bearish/Neutral",
                "confidence": 0.85,  # 0.0 - 1.0
                "summary_reason": "一句話理由"
            }
            
            Returns None if analysis fails or agent is disabled
        
        Fallback Scenarios:
        - Empty news_list: Return neutral stance
        - API error: Return None (graceful degradation)
        - Invalid JSON: Attempt to parse or return None
        """
        if not self.enabled:
            logger.debug(f"News analysis skipped for {symbol} (agent disabled)")
            return None
        
        # Fallback: No news available
        if not news_list:
            logger.info(f"⚠️  No news for {symbol}, returning neutral analysis")
            return {
                "sentiment": "Neutral",
                "sentiment_score": 0,
                "moat_impact": "Unchanged",
                "prediction": "Neutral",
                "confidence": 0.5,
                "summary_reason": "無重大新聞，建議以技術面為主要判斷依據"
            }
        
        try:
            # Prepare news summary for LLM
            news_summary = self._format_news_for_llm(news_list)
            
            # Generate analysis
            logger.info(f"🤖 Analyzing {len(news_list)} news articles for {symbol}...")
            
            prompt = self._create_analysis_prompt(symbol, news_summary)
            
            # Generate content with error handling
            try:
                response = self.model.generate_content(prompt)
            except Exception as gen_error:
                logger.error(f"❌ Generate content failed: {gen_error}")
                return None
            
            # Check if response has valid parts
            if not response.parts:
                # Diagnostic output for debugging
                finish_reason = response.candidates[0].finish_reason if response.candidates else "UNKNOWN"
                logger.error(f"❌ No response parts. Finish reason: {finish_reason}")
                
                # Check prompt feedback (safety filters)
                if hasattr(response, 'prompt_feedback'):
                    logger.error(f"   Prompt feedback: {response.prompt_feedback}")
                
                # Fallback to neutral stance
                logger.info("🔄 Using fallback neutral analysis")
                return {
                    "sentiment": "Neutral",
                    "sentiment_score": 0,
                    "moat_impact": "Unchanged",
                    "prediction": "Neutral",
                    "confidence": 0.5,
                    "summary_reason": "AI 分析無法完成，建議以技術面為主"
                }
            
            # Parse JSON response
            analysis = json.loads(response.text)
            
            # Validate required fields
            required_fields = ["sentiment", "sentiment_score", "moat_impact", "prediction", "confidence", "summary_reason"]
            if all(field in analysis for field in required_fields):
                logger.info(f"✅ Analysis complete: {analysis['sentiment']} (Score: {analysis['sentiment_score']}, Conf: {analysis['confidence']:.0%})")
                return analysis
            else:
                logger.warning(f"⚠️  Incomplete analysis response: {analysis}")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.debug(f"   Raw response: {response.text if 'response' in locals() else 'N/A'}")
            return None
            
        except Exception as e:
            logger.error(f"❌ News analysis failed for {symbol}: {type(e).__name__}")
            logger.error(f"   Details: {str(e)}")
            return None
    
    def _format_news_for_llm(self, news_list: List[Dict[str, str]]) -> str:
        """
        Format news articles into a structured string for LLM
        
        Args:
            news_list: List of news articles
        
        Returns:
            Formatted string with numbered articles
        """
        formatted = ""
        for i, article in enumerate(news_list, 1):
            formatted += f"\n【新聞 {i}】\n"
            formatted += f"標題: {article['title']}\n"
            formatted += f"時間: {article['date']}\n"
            formatted += f"來源: {article['source']}\n"
            if article.get('snippet'):
                formatted += f"摘要: {article['snippet']}\n"
        
        return formatted.strip()
    
    def _create_analysis_prompt(self, symbol: str, news_summary: str) -> str:
        """
        Create structured prompt for news analysis
        
        Optimized for thinking models (Gemini 2.5 Flash)
        """
        prompt = f"""Think step-by-step about the impact on {symbol}'s moat and cash flow, then provide the final JSON output.

Analyze news for {symbol} as a value investor:

News Articles:
{news_summary}

Analysis Steps:
1. Assess sentiment (Positive/Negative/Neutral)
2. Assign Sentiment Score (-100 to +100)
    - -100: Extreme Fear / Bankruptcy Risk
    - -50: Negative Trend
    - 0: Neutral / Mixed
    - +50: Positive Trend
    - +100: Extreme Greed / Breakthrough
3. Evaluate moat impact (Strengthened/Weakened/Unchanged)
4. Predict trend (Bullish/Bearish/Neutral)
5. Determine confidence (0.0-1.0)
6. Summarize key reason (Traditional Chinese, <40 chars)

Output JSON format (no markdown):
{{
    "sentiment": "Positive|Negative|Neutral",
    "sentiment_score": Integer (-100 to 100),
    "moat_impact": "Strengthened|Weakened|Unchanged",
    "prediction": "Bullish|Bearish|Neutral",
    "confidence": 0.XX,
    "summary_reason": "簡潔理由"
}}
"""
        return prompt
    
    def get_market_outlook(self, events_data: str) -> str:
        """
        Generate market outlook based on economic events (legacy method)
        
        This method is kept for backward compatibility with main.py
        It receives hard facts (events_data) and provides AI interpretation
        
        Args:
            events_data: String containing economic events and earnings calendar
        
        Returns:
            AI-generated market outlook commentary
        """
        if not self.enabled:
            return "AI 市場分析功能未啟用（缺少 GEMINI_API_KEY）"
        
        try:
            prompt = f"""你是一位宏觀經濟分析師。

【任務】
基於以下真實的經濟數據與財報行程，提供本週市場展望。

【輸入數據】
{events_data}

【分析要求】
1. 解讀重要經濟數據對市場的影響
2. 評估重點公司財報可能帶來的波動
3. 給出操作建議（偏多/偏空/觀望）

【輸出格式】
簡潔的市場解讀（<200字），避免重複輸入數據。

請開始分析。
"""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"❌ Market outlook generation failed: {e}")
            return "市場分析暫時無法取得"


# Module test
if __name__ == "__main__":
    print("🧪 Testing NewsAgent V3 (Commentator)\n")
    
    agent = NewsAgent()
    
    if agent.enabled:
        # Mock news data (simulating GoogleNewsSearcher output)
        mock_news = [
            {
                "title": "Tesla Unveils Revolutionary Battery Technology",
                "date": "2 hours ago",
                "source": "Reuters",
                "snippet": "Tesla announced a breakthrough in solid-state battery technology, promising 50% longer range."
            },
            {
                "title": "Morgan Stanley Upgrades Tesla to Overweight",
                "date": "1 day ago",
                "source": "Bloomberg",
                "snippet": "Analyst cites strong demand and production efficiency improvements."
            }
        ]
        
        print("Testing analyze_news() with mock data...\n")
        result = agent.analyze_news("TSLA", mock_news)
        
        if result:
            print("✅ Analysis Result:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("❌ Analysis failed")
    else:
        print("⚠️  Agent not enabled (missing GEMINI_API_KEY)")
