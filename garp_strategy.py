import yfinance as yf
from data_models import StockHealthCard, OverallStatus
from market_data import fetch_and_analyze

class GARPStrategy:
    def __init__(self):
        self.strategy_type = "GARP"

    def analyze(self, symbol: str) -> StockHealthCard:
        """
        Analyze a stock using the GARP strategy and return a StockHealthCard.
        """
        print(f"🔍 Analyzing {symbol} with GARP Strategy...")
        
        # 1. Fetch Data
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            market_data = fetch_and_analyze(symbol)
            
            if not market_data:
                print(f"⚠️ No market data found for {symbol}")
                return self._create_empty_card(symbol)
                
            price = market_data.get('price', 0.0)
        except Exception as e:
            print(f"❌ Error fetching data for {symbol}: {e}")
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
        - Debt/Equity < 200% (or sector adjusted) -> Pass
        - Current Ratio > 1.0 -> Pass
        """
        debt_to_equity = info.get('debtToEquity')
        current_ratio = info.get('currentRatio')
        
        card.solvency_check['debt_to_equity'] = debt_to_equity
        card.solvency_check['current_ratio'] = current_ratio
        
        is_passing = True
        
        # Debt to Equity Check (Threshold: 200)
        if debt_to_equity is not None:
            if debt_to_equity > 200:
                card.solvency_check['tags'].append("🔴 High Debt")
                is_passing = False
            else:
                card.solvency_check['tags'].append("🟢 Healthy Debt")
        else:
             card.solvency_check['tags'].append("⚪ No Debt Data")

        # Current Ratio Check (Threshold: 1.0)
        if current_ratio is not None:
            if current_ratio < 1.0:
                card.solvency_check['tags'].append("🔴 Low Liquidity")
                is_passing = False
            else:
                card.solvency_check['tags'].append("🟢 Good Liquidity")
        else:
            card.solvency_check['tags'].append("⚪ No Liquidity Data")
            
        card.solvency_check['is_passing'] = is_passing

    def _check_quality(self, card: StockHealthCard, info: dict):
        """
        Quality Check:
        - ROE > 15% -> Pass
        - Gross Margin > 0 (positive) -> Pass
        """
        roe = info.get('returnOnEquity')
        gross_margins = info.get('grossMargins')
        
        card.quality_check['roe'] = roe
        card.quality_check['gross_margin'] = gross_margins
        
        is_passing = True
        
        # ROE Check (Threshold: 0.15)
        if roe is not None:
            if roe > 0.15:
                card.quality_check['tags'].append("💎 High ROE")
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
        - PEG < 1.5 -> Pass (Growth at Reasonable Price)
        - Margin of Safety (based on Target Price vs Current Price) > 10% -> Pass
        """
        pe_ratio = info.get('trailingPE')
        peg_ratio = info.get('pegRatio')
        target_price = info.get('targetMeanPrice')
        
        card.valuation_check['pe_ratio'] = pe_ratio
        card.valuation_check['peg_ratio'] = peg_ratio
        card.valuation_check['fair_value'] = target_price
        
        is_passing = True
        
        # PEG Check (Threshold: 1.5)
        if peg_ratio is not None:
            if peg_ratio < 1.0:
                card.valuation_check['tags'].append("💎 Undervalued (PEG < 1)")
            elif peg_ratio < 1.5:
                card.valuation_check['tags'].append("🟢 Reasonable Price (PEG < 1.5)")
            else:
                card.valuation_check['tags'].append("🔴 Overvalued (PEG > 1.5)")
                is_passing = False # Strict on PEG for GARP
        else:
             card.valuation_check['tags'].append("⚪ No PEG Data")

        # Margin of Safety
        margin_of_safety = 0.0
        if target_price and current_price > 0:
            margin_of_safety = (target_price - current_price) / target_price
            card.valuation_check['margin_of_safety'] = margin_of_safety
            
            if margin_of_safety > 0.2:
                card.valuation_check['tags'].append("💎 Deep Value (>20% Upside)")
            elif margin_of_safety > 0.1:
                card.valuation_check['tags'].append("🟢 Good Value (>10% Upside)")
            elif margin_of_safety < -0.1:
                card.valuation_check['tags'].append("🔴 Overpriced")
                # Don't fail solely on price if PEG is good, but it's a warning
        
        card.valuation_check['is_passing'] = is_passing

    def _check_technical(self, card: StockHealthCard, market_data: dict):
        """
        Technical Setup:
        - RSI < 70 (Not overbought)
        - Trend (MA50 > MA200) -> Bullish
        """
        if not market_data:
            return

        momentum = market_data.get('momentum', {})
        trend = market_data.get('trend', {})
        
        rsi = momentum.get('rsi')
        ma50_above_ma200 = trend.get('ma50_above_ma200')
        
        card.technical_setup['rsi'] = rsi
        card.technical_setup['trend_status'] = "Bullish" if ma50_above_ma200 else "Bearish"
        
        # RSI Check
        if rsi is not None:
            if rsi > 70:
                card.technical_setup['tags'].append("🔴 Overbought")
            elif rsi < 30:
                card.technical_setup['tags'].append("💎 Oversold")
            else:
                card.technical_setup['tags'].append("🟢 Neutral RSI")
        
        # Trend Check
        if ma50_above_ma200:
            card.technical_setup['tags'].append("🟢 Golden Cross Trend")
        else:
            card.technical_setup['tags'].append("🔴 Death Cross Trend")

    def _determine_overall_status(self, card: StockHealthCard):
        """
        Overall Status:
        - PASS: Solvency, Quality, Valuation passing.
        - WATCHLIST: One failure allowed (except Solvency).
        - REJECT: Critical failures.
        """
        solvency_pass = card.solvency_check['is_passing']
        quality_pass = card.quality_check['is_passing']
        valuation_pass = card.valuation_check['is_passing']
        
        # Collect Red Flags
        for check in [card.solvency_check, card.quality_check, card.valuation_check, card.technical_setup]:
            for tag in check.get('tags', []):
                if "🔴" in tag:
                    card.red_flags.append(tag)

        if solvency_pass and quality_pass and valuation_pass:
            card.overall_status = OverallStatus.PASS.value
        elif not solvency_pass:
            card.overall_status = OverallStatus.REJECT.value
        elif quality_pass or valuation_pass: # At least one of Quality or Valuation is good, but not both
             card.overall_status = OverallStatus.WATCHLIST.value
        else:
            card.overall_status = OverallStatus.REJECT.value
