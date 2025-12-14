import yfinance as yf
from data_models import StockHealthCard, OverallStatus
from market_data import fetch_and_analyze
from config import Config
from logger import logger
from advanced_metrics import AdvancedFinancials
from news_agent import NewsAgent
from database_manager import DatabaseManager
from stress_test.monte_carlo import run_monte_carlo_simulation
from google_news_searcher import GoogleNewsSearcher
from constants import Emojis

class GARPStrategy:
    def __init__(self):
        self.strategy_type = "GARP"
        self.params = Config.get('GARP', {})
        # Defaults if config missing, mapped to config.yaml structure
        solvency_config = self.params.get('solvency', {})
        quality_config = self.params.get('quality', {})
        valuation_config = self.params.get('valuation', {})
        advanced_config = self.params.get('advanced', {})
        
        self.thresholds = {
            'max_debt': solvency_config.get('max_debt_to_equity', 200),
            'min_current': solvency_config.get('min_current_ratio', 1.0),
            'min_roe': quality_config.get('min_roe', 0.15),
            'max_peg': valuation_config.get('max_peg', 1.5),
            'max_pe': valuation_config.get('max_pe', 40),
            # Advanced Metrics
            'min_z_safe': advanced_config.get('min_z_score_safe', 2.99),
            'min_z_distress': advanced_config.get('min_z_score_distress', 1.81),
            'min_f_high': advanced_config.get('min_f_score_high', 7),
            'max_f_low': advanced_config.get('max_f_score_low', 3)
        }
        
        # Initialize News Agents
        self.news_searcher = GoogleNewsSearcher()
        self.news_agent = NewsAgent()

    def analyze(self, symbol: str, market_data: dict = None, ticker_obj = None) -> StockHealthCard:
        """
        Analyze a stock using the GARP strategy and return a StockHealthCard.
        Args:
            symbol: Stock ticker
            market_data: Optional pre-fetched market data (to avoid redundant calls)
            ticker_obj: Optional pre-initialized yf.Ticker object
        """
        logger.info(f"🔍 Analyzing {symbol} with GARP Strategy...")
        
        # 1. Fetch Data
        try:
            # Reuse or Create Ticker
            if ticker_obj:
                ticker = ticker_obj
            else:
                ticker = yf.Ticker(symbol)
            
            info = ticker.info
            
            # Reuse or Fetch Market Data
            if market_data is None:
                market_data = fetch_and_analyze(symbol)
            
            if not market_data:
                logger.warning(f"⚠️ No market data found for {symbol}, checking cache...")
                # Fallback: Check Database for cached snapshot
                db = DatabaseManager()
                cached = db.get_latest_stock_data(symbol)
                
                if cached and 'raw_data' in cached:
                    logger.info(f"✅ Loaded cached data for {symbol}")
                    # Reconstruct Card from Cache
                    raw = cached['raw_data']
                    card = StockHealthCard(
                        symbol=raw.get('symbol', symbol),
                        price=raw.get('price', 0.0),
                        strategy_type=self.strategy_type
                    )
                    # Manually populate distinct checks from raw dict
                    # This is a simplified reconstruction for display purposes
                    card.overall_status = raw.get('overall_status', 'UNKNOWN')
                    card.overall_reason = f"Cached Data (Last Updated: {cached.get('date')})"
                    
                    # Populate tags list from raw data if available, else mark as cached
                    card.advanced_metrics['tags'].append(f"⚠️ Offline Mode (Cached: {cached.get('date')})")
                    
                    return card
                else:
                    return self._create_empty_card(symbol)
                
            price = market_data.get('price', 0.0)
        except Exception as e:
            logger.error(f"❌ Error fetching data for {symbol}: {e}")
            return self._create_empty_card(symbol)

        # Initialize Card
        card = StockHealthCard(
            symbol=symbol, 
            price=price, 
            strategy_type=self.strategy_type,
            sector=info.get('sector', 'Unknown'), # [Fix] Populate sector
            sparkline=market_data.get('sparkline', []) # [New]
        )

        # 2. Solvency Check
        self._check_solvency(card, info)

        # 3. Quality Check
        self._check_quality(card, info)

        # 4. News Sentiment Analysis (Moved before Valuation)
        try:
            if self.news_agent.enabled:
                news_list = self.news_searcher.search_news(symbol, days=3) # Past 3 days
                analysis = self.news_agent.analyze_news(symbol, news_list)
                
                if analysis:
                    card.advanced_metrics['news_analysis'] = analysis
                    sentiment = analysis.get('sentiment', 'Neutral')
                    confidence = analysis.get('confidence', 0.5)
                    
                    if sentiment == 'Positive':
                        card.advanced_metrics['tags'].append(f"📰 News: Positive ({confidence:.0%})")
                    elif sentiment == 'Negative':
                        card.advanced_metrics['tags'].append(f"📰 News: Negative ({confidence:.0%})")
                    
        except Exception as e:
            logger.error(f"News Analysis failed for {symbol}: {e}")

        # Initialize AdvancedFinancials (Early)
        try:
            adv = AdvancedFinancials(ticker)
        except Exception as e:
            logger.error(f"Failed to init AdvancedFinancials for {symbol}: {e}")
            adv = None

        # 5. Valuation Check (Now uses Sentiment + DCF)
        self._check_valuation(card, info, price, adv)

        # 5. Technical Setup
        self._check_technical(card, market_data)

        # 5.5 Advanced Metrics (Academic Standard)
        if adv:
            try:
                # Piotroski F-Score
                f_score_res = adv.calculate_piotroski_f_score()
                card.advanced_metrics['piotroski_score'] = f_score_res.get('score')
                if f_score_res.get('score') is not None:
                    if f_score_res['score'] >= self.thresholds['min_f_high']:
                        card.advanced_metrics['tags'].append(f"{Emojis.GEM} High F-Score ({f_score_res['score']})")
                    elif f_score_res['score'] <= self.thresholds['max_f_low']:
                         card.advanced_metrics['tags'].append(f"{Emojis.WARN} Low F-Score ({f_score_res['score']})")
                    else:
                         card.advanced_metrics['tags'].append(f"Average F-Score ({f_score_res['score']})")
    
                # Altman Z-Score
                z_score_res = adv.calculate_altman_z_score(price)
                card.advanced_metrics['altman_z_score'] = z_score_res.get('score')
                if z_score_res.get('score') is not None:
                    status = z_score_res.get('status', 'Unknown')
                    if status == 'Safe':
                         card.advanced_metrics['tags'].append(f"{Emojis.SHIELD} Z-Score Safe ({z_score_res['score']:.2f})")
                    elif status == 'Distress':
                         card.advanced_metrics['tags'].append(f"{Emojis.SKULL} Z-Score Distress ({z_score_res['score']:.2f})")
                         card.red_flags.append(f"Bankruptcy Risk (Z-Score {z_score_res['score']:.2f})")
                    else:
                         card.advanced_metrics['tags'].append(f"{Emojis.FAIR} Z-Score Grey ({z_score_res['score']:.2f})")
    
                # FCF Yield
                fcf_res = adv.calculate_fcf_yield(price)
                card.advanced_metrics['fcf_yield'] = fcf_res.get('yield')
                if fcf_res.get('yield') is not None:
                    yld = fcf_res['yield']
                    card.advanced_metrics['tags'].append(f"💰 FCF Yield: {yld:.1%}")
    
            except Exception as e:
                logger.error(f"Failed to calc advanced metrics for {symbol}: {e}")
                card.advanced_metrics['tags'].append("⚠️ Advanced Metrics Failed")

        # 5.6 Quantitative Risk Analysis (Vol Range, not Prediction)
        try:
            # We need historical returns for Monte Carlo
            # Reuse ticker from earlier if possible, or fetch history
            # hist = ticker.history(period="1y") # Already have ticker
            hist = ticker.history(period="1y")
            
            if len(hist) > 30:
                returns = hist['Close'].pct_change().dropna()
                
                # Run Simulation (Using modified Monte Carlo - Financial Logic Correction)
                # 1 Week (5 days) Risk Range
                sim_result = run_monte_carlo_simulation(price, returns, num_simulations=5000, days=5)
                
                # Extract Risk Metrics
                # New Keys from Step 3: volatility_range_low, volatility_range_high, risk_downside_5pct
                range_low = sim_result.get('volatility_range_low', price)
                range_high = sim_result.get('volatility_range_high', price)
                var_pct = sim_result.get('risk_downside_5pct', 0.0)
                
                # Store in card (using monte_carlo_min/max fields for range)
                card.monte_carlo_min = float(range_low)
                card.monte_carlo_max = float(range_high)
                
                # Add Tags (No "Predicted Return")
                card.advanced_metrics['tags'].append(f"📉 Risk Range (1W): ${range_low:.2f} - ${range_high:.2f}")
                card.advanced_metrics['tags'].append(f"🛡️ 95% VaR: -{var_pct:.1%}")
                
            else:
                card.advanced_metrics['tags'].append("⚪ Risk Calc: Insufficient Data")

        except Exception as e:
             logger.error(f"Risk Analysis failed for {symbol}: {e}")



        # 6. Determine Overall Status
        self._determine_overall_status(card, market_data) # Pass market_data for Trend check

        return card

    # Modified to accept market_data
    def _determine_overall_status(self, card: StockHealthCard, market_data: dict):
        """
        Final Decision Logic:
        - Passthrough checks
        - Advanced Metrics Overrides
        - SMA200 Trend Filter
        """
        
        passed_solvency = card.solvency_check['is_passing']
        passed_quality = card.quality_check['is_passing']
        passed_valuation = card.valuation_check['is_passing']
        passed_technical = card.technical_setup['is_passing']
        
        # Base Logic
        if passed_solvency and passed_quality and passed_valuation:
             if not passed_technical:
                 card.overall_status = OverallStatus.WATCHLIST.value
                 card.overall_reason = "Fundamentals Great, but Technicals Overheated"
             else:
                 card.overall_status = OverallStatus.PASS.value
                 card.overall_reason = "All Systems Go (GARP Approved)"
        
        elif passed_solvency and passed_quality and not passed_valuation:
            card.overall_status = OverallStatus.WATCHLIST.value
            card.overall_reason = "Great Company, Expensive Price"
            
        else:
            card.overall_status = OverallStatus.REJECT.value
            card.overall_reason = "Fundamental Red Flags"

        # === Advanced Metrics Overrides (Safety First) ===
        z_score = card.advanced_metrics.get('altman_z_score')
        f_score = card.advanced_metrics.get('piotroski_score')

        # 1. Bankruptcy Veto
        if z_score is not None and z_score < (self.thresholds['min_z_distress'] - 0.01): # < 1.8
            card.overall_status = OverallStatus.REJECT.value
            card.overall_reason = f"⛔ Rejected: High Bankruptcy Risk (Z-Score {z_score:.2f})"

        # 2. Weak Financials Veto
        if f_score is not None and f_score <= self.thresholds['max_f_low']:
            if card.overall_status == OverallStatus.PASS.value:
                card.overall_status = OverallStatus.WATCHLIST.value
                card.overall_reason = f"Downgraded: Financials Deteriorating (F-Score {f_score})"

        # 3. Quality Rescue (Strong F-Score + Safe Z-Score)
        if card.overall_status == OverallStatus.REJECT.value:
            if f_score is not None and f_score >= self.thresholds['min_f_high'] and z_score is not None and z_score > self.thresholds['min_z_safe']:
                 card.overall_status = OverallStatus.WATCHLIST.value
                 card.overall_reason = f"Saved by Quality: High F-Score ({f_score}) & Safe Z-Score"

        # === SMA200 Trend Filter (Don't Fight the Fed/Market) ===
        # Downgrade PASS to WATCHLIST if below SMA200 (Long Term Downtrend)
        # But if it's already REJECT, keep REJECT.
        is_above_ma200 = market_data.get('trend', {}).get('is_above_ma200', True)
        
        if not is_above_ma200:
            card.technical_setup['tags'].append("📉 Below SMA200 (Downtrend)")
            
            if card.overall_status == OverallStatus.PASS.value:
                card.overall_status = OverallStatus.WATCHLIST.value
                card.overall_reason = "Downgraded: Long-Term Downtrend (Below SMA200)"
            elif card.overall_status == OverallStatus.WATCHLIST.value:
                if "Downtrend" not in card.overall_reason:
                     card.overall_reason += " & Below SMA200"

        # === News Sentiment Veto (Behavioral Safety) ===
        # Avoid "catching falling knives" if news is overwhelmingly negative
        news_analysis = card.advanced_metrics.get('news_analysis')
        if news_analysis:
            sentiment = news_analysis.get('sentiment')
            confidence = news_analysis.get('confidence', 0.0)
            
            if sentiment == 'Negative' and confidence > 0.7:
                 if card.overall_status == OverallStatus.PASS.value:
                     card.overall_status = OverallStatus.WATCHLIST.value
                     card.overall_reason = f"Downgraded: Negative News Sentiment (Conf: {confidence:.0%})"


    def _create_empty_card(self, symbol: str) -> StockHealthCard:
        card = StockHealthCard(symbol=symbol, price=0.0, strategy_type=self.strategy_type)
        card.red_flags.append("Data Fetch Failed")
        return card

    def _check_solvency(self, card: StockHealthCard, info: dict):
        """
        Solvency Check:
        - Debt/Equity < Threshold (default 200%)
        - Current Ratio > Threshold (default 1.0)
        """
        debt_to_equity = info.get('debtToEquity')
        current_ratio = info.get('currentRatio')
        
        card.solvency_check['debt_to_equity'] = debt_to_equity
        card.solvency_check['current_ratio'] = current_ratio
        
        is_passing = True
        
        # Debt to Equity Check
        threshold_debt = self.thresholds['max_debt']
        if debt_to_equity is not None:
            if debt_to_equity > threshold_debt:
                card.solvency_check['tags'].append(f"🔴 High Debt (>{threshold_debt}%)")
                is_passing = False
            else:
                card.solvency_check['tags'].append("🟢 Healthy Debt")
        else:
             card.solvency_check['tags'].append("⚪ No Debt Data")

        # Current Ratio Check
        threshold_current = self.thresholds['min_current']
        if current_ratio is not None:
            if current_ratio < threshold_current:
                card.solvency_check['tags'].append(f"🔴 Low Liquidity (<{threshold_current})")
                is_passing = False
            else:
                card.solvency_check['tags'].append("🟢 Good Liquidity")
        else:
            card.solvency_check['tags'].append("⚪ No Liquidity Data")
            
        card.solvency_check['is_passing'] = is_passing

    def _check_quality(self, card: StockHealthCard, info: dict):
        """
        Quality Check:
        - ROE > Threshold (default 15%)
        - Gross Margin > 0 (positive)
        """
        roe = info.get('returnOnEquity')
        gross_margins = info.get('grossMargins')
        
        card.quality_check['roe'] = roe
        card.quality_check['gross_margin'] = gross_margins
        
        is_passing = True
        
        # ROE Check
        threshold_roe = self.thresholds['min_roe']
        if roe is not None:
            if roe > threshold_roe:
                 card.quality_check['tags'].append(f"💎 High ROE (>{threshold_roe:.0%})")
            elif roe < 0:
                card.quality_check['tags'].append("🔴 Negative ROE")
                is_passing = False
            else:
                card.quality_check['tags'].append("🟡 Moderate ROE")
        else:
             card.quality_check['tags'].append("⚪ No ROE Data")

        # Gross Margin Check
        if gross_margins is not None:
            if gross_margins > 0.4:
                 card.quality_check['tags'].append("💎 High Margins")
            elif gross_margins < 0:
                 card.quality_check['tags'].append("🔴 Negative Margins")
                 is_passing = False
        
        card.quality_check['is_passing'] = is_passing

    def get_market_sentiment(self) -> float:
        """
        Get SPY sentiment score (-100 to 100) to gauge market temperature.
        Cached for 1 hour to avoid excessive API calls.
        """
        # In a real implementation with DB, we would cache this. 
        # For now, we fetch it live but could simple-cache in instance.
        if hasattr(self, '_market_sentiment_cache'):
             return self._market_sentiment_cache
             
        try:
            logger.info("📊 Checking Market Sentiment (SPY)...")
            spy_news = self.news_searcher.search_news("SPY", days=2)
            if not spy_news:
                return 0.0
            
            analysis = self.news_agent.analyze_news("SPY", spy_news)
            if analysis:
                score = analysis.get('sentiment_score', 0)
                self._market_sentiment_cache = score
                logger.info(f"📊 Market Sentiment: {score}/100")
                return score
        except Exception as e:
            logger.warning(f"⚠️ Failed to get market sentiment: {e}")
            
        return 0.0

    def _calculate_dynamic_peg(self, market_z_score: float) -> float:
        """
        Calculate Dynamic PEG Threshold based on Market Sentiment Z-Score.
        Formula: Base_PEG + (Sensitivity * Z_Score)
        """
        base_peg = self.thresholds['max_peg'] # 1.5, or 1.0 per new user request? User said: "base_peg = 1.0" in request example.
        # User request said: "base_peg = 1.0"
        # Let's check self.thresholds['max_peg']. It defaults to 1.5. 
        # The user's example code said "base_peg = 1.0". 
        # But if I use 1.0, it's stricter than before. 
        # Wait, the user said: "base_peg = 1.0 ... dynamic_threshold = base_peg + (0.2 * market_z_score)"
        # And "將原本寫死的 1.5 替換為 dynamic_threshold"
        # So I should use 1.0 as the base for the formula.
        
        base_peg_formula = 1.0
        sensitivity = 0.2
        
        adjustment = sensitivity * market_z_score
        dynamic_peg = base_peg_formula + adjustment
        
        # Clamp to reasonable limits (0.8 to 2.0)
        return max(0.8, min(2.0, dynamic_peg))

    def _calculate_sentiment_adjusted_target(self, original_target: float, sentiment_score: float) -> float:
        """
        Adjust Analyst Target Price based on quantitative sentiment.
        Formula: Target * (1 + Sensitivity * (Score / 100))
        Sensitivity = 0.05 (Sentiment can sway valuation by +/- 5%)
        """
        if original_target is None:
            return None
            
        sensitivity = 0.05
        # Normalize score -100 to 100 -> -1.0 to 1.0
        normalized_score = max(-1.0, min(1.0, sentiment_score / 100.0))
        
        adjustment = 1 + (sensitivity * normalized_score)
        return original_target * adjustment

    def _check_valuation(self, card: StockHealthCard, info: dict, current_price: float, adv: AdvancedFinancials = None):
        """
        Valuation Check:
        - PEG < Dynamic Threshold (Adaptive to Market)
        - Margin of Safety > 10% (Using Sentiment-Adjusted Target)
        """
        pe_ratio = info.get('trailingPE')
        peg_ratio = info.get('pegRatio')
        target_price = info.get('targetMeanPrice')
        
        # Get Stock-Specific Sentiment (from earlier News Analysis)
        stock_sentiment_score = 0
        if 'news_analysis' in card.advanced_metrics and card.advanced_metrics['news_analysis']:
            stock_sentiment_score = card.advanced_metrics['news_analysis'].get('sentiment_score', 0)
            
        # Adjust Target Price
        adjusted_target = self._calculate_sentiment_adjusted_target(target_price, stock_sentiment_score)
        
        card.valuation_check['pe_ratio'] = pe_ratio
        card.valuation_check['peg_ratio'] = peg_ratio
        card.valuation_check['fair_value'] = target_price
        card.valuation_check['adjusted_fair_value'] = adjusted_target # Store for transparency
        
        is_passing = True
        
        # Dynamic PEG Limit
        market_score = self.get_market_sentiment()
        
        # Calculate Z-Score
        try:
            db = DatabaseManager()
            stats = db.get_sentiment_stats("SPY", days=30)
            mean = stats.get('mean', 0.0)
            std = stats.get('std_dev', 1.0)
            
            z_score = (market_score - mean) / std
        except Exception as e:
            logger.warning(f"⚠️ Failed to calc Z-Score: {e}")
            z_score = 0.0

        dynamic_max_peg = self._calculate_dynamic_peg(z_score)
        
        if abs(z_score) > 0.5: 
             direction = "Bullish" if z_score > 0 else "Bearish"
             card.valuation_check['tags'].append(f"⚖️ Dynamic PEG: {dynamic_max_peg:.2f} ({direction} Market, Z={z_score:.2f})")
        else:
             card.valuation_check['tags'].append(f"⚖️ PEG Limit: {dynamic_max_peg:.2f} (Neutral Market, Z={z_score:.2f})")

        # === 1. Deep Value Check (AI DCF) ===
        # If available, this takes precedence or supplements analyst targets
        if adv:
            dcf_res = adv.calculate_sentiment_adjusted_dcf(z_score)
            intrinsic_val = dcf_res.get('intrinsic_value')
            
            if intrinsic_val and intrinsic_val > 0:
                logger.info(f"🧮 DCF Calc: ${intrinsic_val:.2f} (Z={z_score:.2f}, Disc={dcf_res.get('discount_rate', 0):.1%})")
                card.valuation_check['dcf'] = dcf_res
                mos_dcf = (intrinsic_val - current_price) / current_price
                card.valuation_check['margin_of_safety_dcf'] = mos_dcf
                
                if mos_dcf > 0.15: # 15% Safety Margin
                     card.valuation_check['tags'].append(f"✅ Deep Value Buy (MoS: {mos_dcf:.0%})")
                elif mos_dcf < -0.10: # 10% Overvalued
                     card.valuation_check['tags'].append(f"⚠️ DCF Overvalued (Premium: {-mos_dcf:.0%})")
            else:
                 card.valuation_check['dcf_error'] = dcf_res.get('details')

        # PEG Check
        if peg_ratio is not None:
            if peg_ratio < 1.0: 
                card.valuation_check['tags'].append("💎 Undervalued (PEG < 1)")
            elif peg_ratio < dynamic_max_peg:
                card.valuation_check['tags'].append(f"🟢 Reasonable Price (PEG < {dynamic_max_peg:.2f})")
            else:
                card.valuation_check['tags'].append(f"🔴 Overvalued (PEG > {dynamic_max_peg:.2f})")
                is_passing = False
        else:
            threshold_pe = self.thresholds['max_pe']
            if pe_ratio is not None and pe_ratio > threshold_pe:
                card.valuation_check['tags'].append(f"🔴 High PE (>{threshold_pe})")
                is_passing = False
            else:
                card.valuation_check['tags'].append("⚪ No Valuation Data")

        # Margin of Safety Check (Using Adjusted Target)
        if adjusted_target is not None and current_price > 0:
            upside = (adjusted_target - current_price) / current_price
            card.valuation_check['margin_of_safety'] = upside
            
            # Show adjustment tag if significant
            if abs(stock_sentiment_score) > 20:
                diff = adjusted_target - target_price
                sign = "+" if diff > 0 else ""
                card.valuation_check['tags'].append(f"🧠 Sentiment Adj: {sign}{diff:.2f}")
            
            if upside > 0.3:
                card.valuation_check['tags'].append(f"🟢 High Upside (+{upside:.0%})")
            elif upside < 0:
                card.valuation_check['tags'].append("🔴 Over Analyst Target")
        else:
             card.valuation_check['tags'].append("⚪ No Analyst Targets")

        card.valuation_check['is_passing'] = is_passing

    def _check_technical(self, card: StockHealthCard, market_data: dict):
        """
        Technical Setup:
        - RSI (14) between 30 and 70 (Not overbought/oversold)
        - SMA200 > Current Price (Long term Trend) - *Wait, GARP usually likes Uptrend*
        - Let's stick to simple RSI for now effectively.
        """
        rsi = market_data.get('rsi')
        
        card.technical_setup['rsi'] = rsi
        
        is_passing = True
        
        if rsi is not None:
            if rsi > 70:
                card.technical_setup['tags'].append(f"🔴 Overbought (RSI {rsi:.0f})")
                is_passing = False
            elif rsi < 30:
                card.technical_setup['tags'].append(f"🟢 Oversold (RSI {rsi:.0f})")
            else:
                card.technical_setup['tags'].append("🟡 Neutral Technicals")
        else:
            card.technical_setup['tags'].append("⚪ No Technical Data")
            
        card.technical_setup['is_passing'] = is_passing


