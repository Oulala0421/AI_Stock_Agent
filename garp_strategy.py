import yfinance as yf
from data_models import StockHealthCard, OverallStatus
from market_data import fetch_and_analyze
from config import Config
from logger import logger

class GARPStrategy:
    def __init__(self):
        self.strategy_type = "GARP"
        self.params = Config.get('GARP', {})
        # Defaults if config missing, mapped to config.yaml structure
        solvency_config = self.params.get('solvency', {})
        quality_config = self.params.get('quality', {})
        valuation_config = self.params.get('valuation', {})
        
        self.thresholds = {
            'max_debt': solvency_config.get('max_debt_to_equity', 200),
            'min_current': solvency_config.get('min_current_ratio', 1.0),
            'min_roe': quality_config.get('min_roe', 0.15),
            'max_peg': valuation_config.get('max_peg', 1.5),
            'max_pe': valuation_config.get('max_pe', 40)
        }

    def analyze(self, symbol: str) -> StockHealthCard:
        """
        Analyze a stock using the GARP strategy and return a StockHealthCard.
        """
        logger.info(f"🔍 Analyzing {symbol} with GARP Strategy...")
        
        # 1. Fetch Data
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            market_data = fetch_and_analyze(symbol)
            
            if not market_data:
                logger.warning(f"⚠️ No market data found for {symbol}")
                return self._create_empty_card(symbol)
                
            price = market_data.get('price', 0.0)
        except Exception as e:
            logger.error(f"❌ Error fetching data for {symbol}: {e}")
            return self._create_empty_card(symbol)

        # Initialize Card
        card = StockHealthCard(symbol=symbol, price=price, strategy_type=self.strategy_type)

        # 2. Solvency Check
        self._check_solvency(card, info)

        # 3. Quality Check
        self._check_quality(card, info)

        # 4. Valuation Check
        self._check_valuation(card, info, price)

        # 5. Technical Setup
        self._check_technical(card, market_data)

        # 6. Determine Overall Status
        self._determine_overall_status(card)

        return card

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

    def _check_valuation(self, card: StockHealthCard, info: dict, current_price: float):
        """
        Valuation Check:
        - PEG < Threshold (default 1.5)
        - Margin of Safety > 10%
        """
        pe_ratio = info.get('trailingPE')
        peg_ratio = info.get('pegRatio')
        target_price = info.get('targetMeanPrice')
        
        card.valuation_check['pe_ratio'] = pe_ratio
        card.valuation_check['peg_ratio'] = peg_ratio
        card.valuation_check['fair_value'] = target_price
        
        is_passing = True
        
        # PEG Check
        threshold_peg = self.thresholds['max_peg']
        if peg_ratio is not None:
            if peg_ratio < 1.0: # Hardcoded "super cheap" check kept for tagging nuance
                card.valuation_check['tags'].append("💎 Undervalued (PEG < 1)")
            elif peg_ratio < threshold_peg:
                card.valuation_check['tags'].append(f"🟢 Reasonable Price (PEG < {threshold_peg})")
            else:
                card.valuation_check['tags'].append(f"🔴 Overvalued (PEG > {threshold_peg})")
                is_passing = False
        else:
            # If PEG is missing, check PE
            threshold_pe = self.thresholds['max_pe']
            if pe_ratio is not None and pe_ratio > threshold_pe:
                card.valuation_check['tags'].append(f"🔴 High PE (>{threshold_pe})")
                is_passing = False
            else:
                card.valuation_check['tags'].append("⚪ No Valuation Data")

        # Margin of Safety Check
        if target_price is not None and current_price > 0:
            upside = (target_price - current_price) / current_price
            card.valuation_check['margin_of_safety'] = upside
            
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

    def _determine_overall_status(self, card: StockHealthCard):
        """
        Final Decision Logic:
        - Must pass Solvency, Quality, and Valuation checks to be 'PASS'.
        - If any check fails, it goes to 'REJECT' or 'WATCHLIST' depending on severity.
        """
        
        passed_solvency = card.solvency_check['is_passing']
        passed_quality = card.quality_check['is_passing']
        passed_valuation = card.valuation_check['is_passing']
        passed_technical = card.technical_setup['is_passing']
        
        # Logic:
        # PASS: Solvency + Quality + Valuation all Pass
        # WATCHLIST: Solvency + Quality Pass, but Valuation Fail OR Technical Fail
        # REJECT: Solvency Fail OR Quality Fail
        
        if passed_solvency and passed_quality and passed_valuation:
             # Even if technicals are "Overbought", fundamental GARP strategy says it's a good stock, maybe wait for entry.
             # But strictly, if technical is failed (overbought), maybe separate?
             # For now, stick to core logic.
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
