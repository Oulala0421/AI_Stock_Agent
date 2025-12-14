import pandas as pd
import yfinance as yf
from logger import logger
from typing import Dict, Any

class AdvancedFinancials:
    """
    Calculates advanced financial metrics including Piotroski F-Score and Altman Z-Score
    using raw financial statements to ensure authenticity.
    """
    
    def __init__(self, ticker: yf.Ticker):
        self.ticker = ticker
        self.bs = ticker.balance_sheet
        self.inc = ticker.financials
        self.cf = ticker.cashflow
        
        # Helper to check if dataframes are empty
        self.has_data = not (self.bs.empty or self.inc.empty or self.cf.empty)
        if not self.has_data:
            logger.warning(f"⚠️ Missing financial statements for {ticker.ticker}")

    def calculate_piotroski_f_score(self) -> Dict[str, Any]:
        """
        Calculates the Piotroski F-Score (0-9) based on 9 criteria.
        Returns a dictionary with the score and details.
        """
        if not self.has_data or self.bs.shape[1] < 2 or self.inc.shape[1] < 2 or self.cf.shape[1] < 2:
            return {"score": None, "details": "Insufficient historical data (need 2 years)"}

        score = 0
        details = []
        
        # Columns: [Recent, Prior, ...] (yfinance usually sorts descending date)
        # Ensure sorted just in case
        try:
            # Helper to get value
            def get_val(df, row_name, col_idx):
                if row_name in df.index:
                    return df.loc[row_name].iloc[col_idx]
                return 0.0 # Treat missing as 0 for safety, but log?

            # 1. Profitability
            # Net Income > 0
            ni_curr = get_val(self.inc, 'Net Income', 0)
            if ni_curr > 0:
                score += 1
                details.append("✅ Positive Net Income")
            else:
                details.append("❌ Negative Net Income")

            # Operating Cash Flow > 0
            cfo_curr = get_val(self.cf, 'Operating Cash Flow', 0)
            if cfo_curr > 0:
                score += 1
                details.append("✅ Positive Operating Cash Flow")
            else:
                details.append("❌ Negative Operating Cash Flow")
                
            # ROA > PY ROA
            ta_curr = get_val(self.bs, 'Total Assets', 0)
            ta_py = get_val(self.bs, 'Total Assets', 1)
            ni_py = get_val(self.inc, 'Net Income', 1)
            
            roa_curr = ni_curr / ta_curr if ta_curr else 0
            roa_py = ni_py / ta_py if ta_py else 0
            
            if roa_curr > roa_py:
                score += 1
                details.append("✅ ROA Improved")
            else:
                details.append("❌ ROA Declined")

            # CFO > Net Income (Quality of Earnings)
            if cfo_curr > ni_curr:
                score += 1
                details.append("✅ CFO > Net Income")
            else:
                details.append("❌ CFO < Net Income")

            # 2. Leverage, Liquidity, Source of Funds
            # Long Term Debt < PY (Decreased Leverage)
            # Use 'Long Term Debt' or fallback 'Total Non Current Liabilities Net Minority Interest'
            ltd_curr = get_val(self.bs, 'Long Term Debt', 0)
            ltd_py = get_val(self.bs, 'Long Term Debt', 1)
            
            if ltd_curr <= ltd_py: # Less debt is good, or equal (0)
                score += 1
                details.append("✅ Lower/Stable Leverage")
            else:
                details.append("❌ Increased Leverage")

            # Current Ratio > PY (Improved Liquidity)
            ca_curr = get_val(self.bs, 'Current Assets', 0)
            cl_curr = get_val(self.bs, 'Current Liabilities', 0)
            ca_py = get_val(self.bs, 'Current Assets', 1)
            cl_py = get_val(self.bs, 'Current Liabilities', 1)
            
            cr_curr = ca_curr / cl_curr if cl_curr else 0
            cr_py = ca_py / cl_py if cl_py else 0
            
            if cr_curr > cr_py:
                score += 1
                details.append("✅ Current Ratio Improved")
            else:
                details.append("❌ Current Ratio Declined")

            # No Dilution (Shares <= PY)
            shares_curr = get_val(self.bs, 'Ordinary Shares Number', 0)
            shares_py = get_val(self.bs, 'Ordinary Shares Number', 1)
            
            # If Ordinary Shares missing, try Share Issued
            if shares_curr == 0:
                shares_curr = get_val(self.bs, 'Share Issued', 0)
                shares_py = get_val(self.bs, 'Share Issued', 1)
            
            # If still 0, maybe skip? Assuming no dilution if unknown is risky, let's assume fail to be safe or 0 change
            if shares_curr <= shares_py:
                score += 1
                details.append("✅ No Dilution")
            else:
                details.append("❌ Shares Diluted")

            # 3. Operating Efficiency
            # Gross Margin > PY
            rev_curr = get_val(self.inc, 'Total Revenue', 0)
            gp_curr = get_val(self.inc, 'Gross Profit', 0)
            rev_py = get_val(self.inc, 'Total Revenue', 1)
            gp_py = get_val(self.inc, 'Gross Profit', 1)
            
            gm_curr = gp_curr / rev_curr if rev_curr else 0
            gm_py = gp_py / rev_py if rev_py else 0
            
            if gm_curr > gm_py:
                score += 1
                details.append("✅ Gross Margin Improved")
            else:
                details.append("❌ Gross Margin Declined")

            # Asset Turnover > PY
            at_curr = rev_curr / ta_curr if ta_curr else 0
            at_py = rev_py / ta_py if ta_py else 0
            
            if at_curr > at_py:
                score += 1
                details.append("✅ Asset Turnover Improved")
            else:
                details.append("❌ Asset Turnover Declined")
                
            return {
                "score": score,
                "details": details,
                "max_score": 9
            }
            
        except Exception as e:
            logger.error(f"Error calculating Piotroski Check for {self.ticker.ticker}: {e}")
            return {"score": None, "details": f"Error: {e}"}

    def calculate_altman_z_score(self, current_price: float) -> Dict[str, Any]:
        """
        Calculates the Altman Z-Score for non-manufacturing firms (or general approximation).
        Z = 1.2A + 1.4B + 3.3C + 0.6D + 1.0E
        """
        if not self.has_data:
             return {"score": None, "details": "No Data"}

        try:
             # Helper
            def get_val(df, row_name):
                if row_name in df.index:
                    return df.loc[row_name].iloc[0] # Most recent
                return 0.0

            ta = get_val(self.bs, 'Total Assets')
            tl = get_val(self.bs, 'Total Liabilities Net Minority Interest')
            if tl == 0: tl = get_val(self.bs, 'Total Debt') # Fallback

            if ta == 0:
                return {"score": None, "details": "Total Assets is 0"}

            # A: Working Capital / Total Assets
            wc = get_val(self.bs, 'Working Capital')
            # Fallback calc
            if wc == 0:
                wc = get_val(self.bs, 'Current Assets') - get_val(self.bs, 'Current Liabilities')
            
            A = wc / ta

            # B: Retained Earnings / Total Assets
            re = get_val(self.bs, 'Retained Earnings')
            B = re / ta

            # C: EBIT / Total Assets
            ebit = get_val(self.inc, 'EBIT')
            C = ebit / ta

            # D: Market Value of Equity / Total Liabilities
            # Need shares count
            shares = get_val(self.bs, 'Ordinary Shares Number')
            if shares == 0: shares = get_val(self.bs, 'Share Issued')
            
            market_cap = current_price * shares
            if tl == 0: 
                D = 0 # Avoid div by zero, huge risk if no liabilities? unlikely.
            else:
                D = market_cap / tl

            # E: Sales / Total Assets
            sales = get_val(self.inc, 'Total Revenue')
            E = sales / ta
            
            # Formula (Original Z-Score for Public Manufacturing)
            # Z = 1.2A + 1.4B + 3.3C + 0.6D + 1.0E
            z_score = 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E
            
            status = "Distress"
            if z_score > 3.0:
                status = "Safe"
            elif z_score > 1.8:
                status = "Grey Zone"
            
            return {
                "score": z_score,
                "status": status,
                "components": {
                    "A_Liquidity": A,
                    "B_AccumulatedEarnings": B,
                    "C_EarningsPower": C,
                    "D_MarketLeverage": D,
                    "E_AssetTurnover": E
                }
            }

        except Exception as e:
            logger.error(f"Error calculating Z-Score for {self.ticker.ticker}: {e}")
            return {"score": None, "details": f"Error: {e}"}

    def calculate_fcf_yield(self, current_price: float) -> Dict[str, Any]:
        """
        Calculates Free Cash Flow Yield = FCF / Market Cap
        """
        if not self.has_data:
             return {"yield": None, "details": "No Data"}
             
        try:
             # FCF
            fcf = 0
            if 'Free Cash Flow' in self.cf.index:
                fcf = self.cf.loc['Free Cash Flow'].iloc[0]
            else:
                # Calc manually: OCF - CapEx
                ocf = self.cf.loc['Operating Cash Flow'].iloc[0] if 'Operating Cash Flow' in self.cf.index else 0
                capex = abs(self.cf.loc['Capital Expenditure'].iloc[0]) if 'Capital Expenditure' in self.cf.index else 0
                fcf = ocf - capex
            
            # Market Cap
            shares = 0
            if 'Ordinary Shares Number' in self.bs.index:
                shares = self.bs.loc['Ordinary Shares Number'].iloc[0]
            elif 'Share Issued' in self.bs.index:
                shares = self.bs.loc['Share Issued'].iloc[0]
            
            if shares == 0 or current_price == 0:
                return {"yield": None, "details": "Cannot determine Market Cap"}
                
            market_cap = shares * current_price
            fcf_yield = fcf / market_cap
            
            return {
                "yield": fcf_yield,
                "fcf_raw": fcf,
                "market_cap": market_cap
            }
            
        except Exception as e:
            logger.error(f"Error calculating FCF Yield for {self.ticker.ticker}: {e}")
            return {"yield": None, "details": f"Error: {e}"}

    def calculate_sentiment_adjusted_dcf(self, sentiment_z_score: float) -> Dict[str, Any]:
        """
        Calculates Intrinsic Value using a 2-Stage DCF model adjusted for market sentiment.
        
        Logic:
        - Base Discount Rate: 9.0%
        - Adjustment: If Market Z-Score > 0 (Overheated), add penalty rate.
                      Penalty = 2.0% * tanh(Z-Score)
        - Growth: Revenue Growth from Info (Capped at 15%)
        - Terminal Growth: 3.0%
        """
        import math
        
        if not self.has_data:
             return {"intrinsic_value": None, "details": "No Data"}

        try:
             # 1. Free Cash Flow (TTM/Recent)
            fcf = 0
            if 'Free Cash Flow' in self.cf.index:
                fcf = self.cf.loc['Free Cash Flow'].iloc[0]
            else:
                # Manual Calc
                ocf_idx = 'Operating Cash Flow' if 'Operating Cash Flow' in self.cf.index else 'Total Cash From Operating Activities'
                cfe_idx = 'Capital Expenditure' if 'Capital Expenditure' in self.cf.index else 'Capital Expenditures'
                
                if ocf_idx in self.cf.index:
                    ocf = self.cf.loc[ocf_idx].iloc[0]
                    capex = self.cf.loc[cfe_idx].iloc[0] if cfe_idx in self.cf.index else 0
                    fcf = ocf - abs(capex)
                else:
                    return {"intrinsic_value": None, "details": "Cannot calc FCF"}
            
            # 2. Shares Outstanding
            shares = self.ticker.info.get('sharesOutstanding')
            if not shares:
                # Try balance sheet
                 if 'Ordinary Shares Number' in self.bs.index:
                    shares = self.bs.loc['Ordinary Shares Number'].iloc[0]
                 elif 'Share Issued' in self.bs.index:
                    shares = self.bs.loc['Share Issued'].iloc[0]
            
            if not shares:
                 return {"intrinsic_value": None, "details": "No Share Count"}

            # 3. Growth Rate
            # Try 'revenueGrowth' from info, else default conservatively
            growth_input = self.ticker.info.get('revenueGrowth', 0.05)
            if growth_input is None: growth_input = 0.05
            
            # Cap at 15% (Conservative)
            growth_rate = min(growth_input, 0.15)
            # Floor at 2% 
            growth_rate = max(growth_rate, 0.02)

            # 4. Discount Rate (Sentiment Adjusted)
            base_rate = 0.09
            sentiment_penalty = 0.0
            
            if sentiment_z_score > 0:
                # Tanh ranges 0 to 1 for positive inputs
                # Max penalty = 3% (Slightly increased to be more responsive? User said 0.02 * ... let's stick to user 0.02)
                sentiment_penalty = 0.02 * math.tanh(sentiment_z_score)
            
            discount_rate = base_rate + sentiment_penalty
            
            # 5. Projection (5 Years)
            future_fcf = []
            current_fcf = fcf
            
            # If FCF is negative, DCF breaks.
            # If FCF is negative, DCF breaks. Use Graham Number fallback.
            if fcf < 0:
                 try:
                     # Graham Number Fallback: Sqrt(22.5 * EPS * BVPS)
                     net_income = self.inc.loc['Net Income'].iloc[0] if 'Net Income' in self.inc.index else 0
                     stockholders_equity = self.bs.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in self.bs.index else \
                                           (self.bs.loc['Total Assets'].iloc[0] - self.bs.loc['Total Liabilities Net Minority Interest'].iloc[0])
                     
                     if net_income > 0 and stockholders_equity > 0:
                         eps = net_income / shares
                         bvps = stockholders_equity / shares
                         graham_number = math.sqrt(22.5 * eps * bvps)
                         logger.info(f"🧮 FCF Negative ({fcf}), using Graham Number: ${graham_number:.2f}")
                         return {
                             "intrinsic_value": graham_number,
                             "details": "Graham Number (Negative FCF Fallback)",
                             "discount_rate": 0.0, # Not applicable
                             "growth_rate": 0.0, # Not applicable
                             "sentiment_penalty": 0.0
                         }
                 except Exception as e_fallback:
                     logger.warning(f"Graham Number fallback failed: {e_fallback}")
                     
                 return {"intrinsic_value": None, "details": "Negative FCF & Graham Failed"}

            for i in range(1, 6):
                current_fcf = current_fcf * (1 + growth_rate)
                future_fcf.append(current_fcf)
                
            # 6. Terminal Value
            # Perpetuity Growth Method
            terminal_growth = 0.03
            # Safety: Discount rate must be > terminal growth
            if discount_rate <= terminal_growth:
                discount_rate = terminal_growth + 0.01 
                
            terminal_val = (future_fcf[-1] * (1 + terminal_growth)) / (discount_rate - terminal_growth)
            
            # 7. Discounting to Present Value
            dcf_value = 0
            for i, cash in enumerate(future_fcf):
                dcf_value += cash / ((1 + discount_rate) ** (i + 1))
                
            pv_terminal = terminal_val / ((1 + discount_rate) ** 5)
            
            total_equity_value = dcf_value + pv_terminal
            
            intrinsic_value = total_equity_value / shares
            
            return {
                "intrinsic_value": intrinsic_value,
                "discount_rate": discount_rate,
                "growth_rate": growth_rate,
                "sentiment_penalty": sentiment_penalty,
                "details": f"DCF (g={growth_rate:.1%}, r={discount_rate:.1%})"
            }

        except Exception as e:
            logger.error(f"DCF Calc failed for {self.ticker.ticker}: {e}")
            return {"intrinsic_value": None, "details": str(e)}
