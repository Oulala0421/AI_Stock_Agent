import time
import yfinance as yf
from typing import List, Optional
from market_data import fetch_and_analyze
from report_formatter import format_stock_report
from data_models import OverallStatus, StockHealthCard
from logger import logger

class AnalysisEngine:
    """
    Core engine for processing stock analysis.
    Decoupled from main.py to improve maintainability and testing.
    """
    
    def __init__(self, strategy, news_agent=None, searcher=None, db=None, pm=None):
        self.strategy = strategy
        self.news_agent = news_agent
        self.searcher = searcher
        self.db = db
        self.pm = pm
        
        self.enable_ai = bool(news_agent) and bool(searcher)

    def process_list(self, symbol_list: List[str], list_name: str) -> List[StockHealthCard]:
        """
        Process a list of stock symbols.
        Returns a list of analyzed StockHealthCards.
        """
        if not symbol_list:
            return []

        print(f"\n💼【{list_name}】")
        results = []

        for symbol in symbol_list:
            try:
                print(f"\n🔍 分析: {symbol}")
                
                # 1. Pre-fetch Data Once
                ticker = yf.Ticker(symbol)
                market_data = fetch_and_analyze(symbol, ticker_obj=ticker)
                
                # 2. GARP Analysis
                card = self.strategy.analyze(symbol, market_data=market_data, ticker_obj=ticker)
                print(f"   ├─ 評級: {card.overall_status}")
                
                news_summary_str = None
                should_analyze_depth = True
                
                # Optimization: Skip API calls for Watchlist rejects
                if list_name == "Watchlist" and card.overall_status == OverallStatus.REJECT.value:
                    should_analyze_depth = False
                    
                if should_analyze_depth:
                    # Risk Analysis (Computed in Strategy)
                    if list_name != "Watchlist" or card.overall_status != OverallStatus.REJECT.value:
                        if hasattr(card, 'monte_carlo_min') and card.monte_carlo_min:
                            print(f"   ├─ 風險評估 (Risk Engine)...")
                            print(f"      📉 波動區間: ${card.monte_carlo_min:.2f} - ${card.monte_carlo_max:.2f}")
                    
                    # AI Analysis
                    if self.enable_ai:
                        news_summary_str = self._run_ai_analysis(symbol, card)
                    else:
                        print(f"   ├─ AI 分析略過 (未啟用)")
                
                else:
                    print(f"   ├─ 評級為 REJECT，跳過深度分析")
                    news_summary_str = "⛔ 基本面未達標，暫不進行 AI 新聞分析。"
                
                # Attach summary
                card.news_summary_str = news_summary_str
                results.append(card)
                
                # Database Snapshot
                if self.db:
                    report_detailed = format_stock_report(card, news_summary_str)
                    self.db.save_daily_snapshot(card, report_detailed)
                    print(f"   └─ ✅ 完成 (DB Saved)")
                
                # Personalization
                if self.pm and card.overall_status in [OverallStatus.PASS.value, OverallStatus.WATCHLIST.value]:
                    self._check_personalization(card)
                
                time.sleep(1) # Rate limiting
                
            except Exception as e:
                print(f"   └─ ❌ 錯誤: {e}")
                import traceback
                traceback.print_exc()
        
        return results

    def _run_ai_analysis(self, symbol: str, card: StockHealthCard) -> Optional[str]:
        """Run Google News Search + AI Analysis"""
        print(f"   ├─ 搜尋新聞 (Google Facts)...")
        try:
            news_list = self.searcher.search_news(symbol, days=3)
            
            if news_list:
                print(f"      📄 找到 {len(news_list)} 則新聞，AI 分析中...")
                
                # Prepare Valuation Data
                dcf_val = card.valuation_check.get('dcf', {}).get('intrinsic_value')
                mos_val = card.valuation_check.get('margin_of_safety_dcf')
                
                val_data = {
                    "price": card.price,
                    "intrinsic_value": dcf_val,
                    "mos": mos_val,
                    "rating": card.overall_status,
                    "monte_carlo_min": card.monte_carlo_min,
                    "monte_carlo_max": card.monte_carlo_max
                }
                
                analysis_result = self.news_agent.analyze_news(symbol, news_list, valuation_data=val_data)
            
                if analysis_result:
                    sentiment_emoji = "😃" if analysis_result['sentiment'] == "Positive" else ("😞" if analysis_result['sentiment'] == "Negative" else "😐")
                    return f"💡 AI: {sentiment_emoji} {analysis_result['sentiment']}\n💬 {analysis_result['summary_reason']}"
                else:
                    return self.searcher.format_news_summary(news_list, max_articles=2)
            else:
                print("      ⚠️ 無近期新聞")
                return "📰 近期無新聞"
        except Exception as ne:
            print(f"      ⚠️ 新聞模組錯誤: {ne}")
            return "⚠️ 無法取得新聞"

    def _check_personalization(self, card: StockHealthCard):
        """Check portfolio concentration and correlation"""
        try:
            sector = getattr(card, 'sector', 'Unknown')
            warning_conc = self.pm.check_concentration(card.symbol, sector)
            warning_corr = self.pm.check_correlation(card.symbol)
            
            if warning_conc: card.private_notes.extend(warning_conc)
            if warning_corr: card.private_notes.extend(warning_corr)
            
            if warning_conc or warning_corr:
                print(f"      🕵️‍♂️ 私人警示: {len(warning_conc)+len(warning_corr)} 則")
        except Exception as pme:
            logger.error(f"      ❌ Personalization Check Error: {pme}")
