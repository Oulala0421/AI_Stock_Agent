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
import yaml
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
    """
    
    def __init__(self):
        """
        Initialize NewsAgent with Gemini API
        """
        self.api_key = Config.get("GEMINI_API_KEY")
        self.enabled = bool(self.api_key)
        
        # Load Prompts
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), 'prompts.yaml')
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.prompts = yaml.safe_load(f)
            logger.info("✅ Validated prompts.yaml")
        except Exception as e:
            logger.error(f"❌ Failed to load prompts.yaml: {e}")
            self.prompts = {}

        if not self.enabled:
            logger.warning("⚠️  GEMINI_API_KEY not found. News analysis disabled.")
            logger.info("💡 Set GEMINI_API_KEY in .env to enable AI commentary")
            return
        
        try:
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            
            # Safety settings
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # Try Configured Model first
            model_id = Config.get("AI_MODEL", "gemini-2.5-flash")
            fallback_id = Config.get("AI_MODEL_FALLBACK", "gemini-2.0-flash")
            
            try:
                self.model = genai.GenerativeModel(
                    model_id,
                    generation_config={
                        "temperature": 0.2,
                        "top_p": 0.95,
                        "max_output_tokens": 8192,
                        "response_mime_type": "application/json"
                    },
                    safety_settings=safety_settings
                )
                self.model_name = model_id
                logger.info(f"✅ NewsAgent initialized ({model_id})")
                
            except Exception as e:
                logger.warning(f"⚠️  {model_id} failed: {e}")
                logger.info(f"🔄 Falling back to {fallback_id}...")
                
                self.model = genai.GenerativeModel(
                    fallback_id,
                    generation_config={
                        "temperature": 0.2,
                        "top_p": 0.95,
                        "max_output_tokens": 4096,
                        "response_mime_type": "application/json"
                    },
                    safety_settings=safety_settings
                )
                self.model_name = fallback_id
                logger.info(f"✅ NewsAgent initialized ({fallback_id} - Fallback)")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {e}")
            self.enabled = False

    def analyze_news(self, symbol: str, news_list: List[Dict[str, str]], valuation_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze news articles and generate structured investment commentary
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
            
            prompt = self._create_analysis_prompt(symbol, news_list, valuation_data)
            
            # Generate content with error handling
            try:
                response = self.model.generate_content(prompt)
            except Exception as gen_error:
                logger.error(f"❌ Generate content failed: {gen_error}")
                return None
            
            # Check if response has valid parts
            if not response.parts:
                finish_reason = response.candidates[0].finish_reason if response.candidates else "UNKNOWN"
                logger.error(f"❌ No response parts. Finish reason: {finish_reason}")
                return None
            
            # Parse JSON response
            analysis = json.loads(response.text)
            
            # Validate required fields
            required_fields = ["sentiment", "sentiment_score", "confidence", "summary_reason"]
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
        """Format news articles into a structured string for LLM"""
        formatted = ""
        for i, article in enumerate(news_list, 1):
            formatted += f"\n【新聞 {i}】\n"
            formatted += f"標題: {article['title']}\n"
            formatted += f"時間: {article['date']}\n"
            formatted += f"來源: {article['source']}\n"
            if article.get('snippet'):
                formatted += f"摘要: {article['snippet']}\n"
        return formatted.strip()
    
    def _create_analysis_prompt(self, symbol: str, news_list: List[Dict], valuation_data: Optional[Dict]) -> str:
        """
        Create the analysis prompt for the AI model.
        Phase 11.1: Load from YAML
        """
        news_text = "\n".join([f"- {n['title']} ({n['date']}): {n['snippet']}" for n in news_list])
        
        # Format Hard Data Block
        hard_data_block = ""
        if valuation_data:
            # Safe extraction with defaults
            price = float(valuation_data.get('price') or 0.0)
            intrinsic = float(valuation_data.get('intrinsic_value') or 0.0)
            mos = float(valuation_data.get('mos') or 0.0)
            rating = valuation_data.get('rating', 'N/A')
            r_min = float(valuation_data.get('monte_carlo_min') or 0.0)
            r_max = float(valuation_data.get('monte_carlo_max') or 0.0)
            
            hard_data_block = f"""
【硬數據】
- 股票: {symbol}
- 現價: ${price:.2f}
- DCF內在價值: ${intrinsic:.2f} (安全邊際 MoS: {mos:.1%})
- 評級: {rating}
- 波動區間: ${r_min:.2f} - ${r_max:.2f}
"""
        else:
            hard_data_block = f"【硬數據】\n- 股票: {symbol}\n- 暫無估值數據"

        # Load Template
        template = self.prompts.get('stock_analysis', '')
        if not template:
            logger.error("❌ 'stock_analysis' prompt missing in YAML")
            return "Error: Prompt Missing"
        
        # Add Valuation-Narrative Alignment Instruction
        valuation_instruction = ""
        if valuation_data:
             if "Overvalued" in valuation_data.get('rating', ''):
                 valuation_instruction = "⚠️ 重要：量化指標顯示股價「嚴重高估」。除非有極其強烈的基本面反轉理由，否則請勿建議「積極買入 (Accumulate)」。建議偏向「持有 (Hold)」或「觀望」。"
             elif "Undervalued" in valuation_data.get('rating', ''):
                 valuation_instruction = "💡 提示：量化指標顯示股價「低估」，可強調價值投資機會。"

        # Append instruction to hard_data_block or prompt
        hard_data_block += f"\n【AI 寫作指引】\n{valuation_instruction}"
            
        return template.format(hard_data_block=hard_data_block, news_text=news_text)

    def get_market_outlook(self, events_data: str) -> str:
        """
        Generate market outlook based on economic events
        """
        if not self.enabled:
            return "AI 市場分析功能未啟用（缺少 GEMINI_API_KEY）"
        
        try:
            template = self.prompts.get('market_outlook', '')
            if not template:
                return "Error: Market Outlook Prompt Missing"
                
            prompt = template.format(events_data=events_data)
            
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
