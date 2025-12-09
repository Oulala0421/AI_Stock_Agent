import yfinance as yf
import sys

def dump_keys(symbol: str, filename: str):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"--- Analysis for {symbol} ---\n")
        ticker = yf.Ticker(symbol)
        
        # Balance Sheet
        f.write("\n=== BALANCE SHEET KEYS ===\n")
        try:
            bs = ticker.balance_sheet
            if not bs.empty:
                for k in sorted(bs.index):
                    f.write(f"{k}\n")
            else:
                f.write("EMPTY\n")
        except Exception as e:
            f.write(f"ERROR: {e}\n")

        # Financials
        f.write("\n=== FINANCIALS (INCOME STATEMENT) KEYS ===\n")
        try:
            inc = ticker.financials
            if not inc.empty:
                for k in sorted(inc.index):
                    f.write(f"{k}\n")
            else:
                f.write("EMPTY\n")
        except Exception as e:
            f.write(f"ERROR: {e}\n")

        # Cash Flow
        f.write("\n=== CASH FLOW KEYS ===\n")
        try:
            cf = ticker.cashflow
            if not cf.empty:
                for k in sorted(cf.index):
                    f.write(f"{k}\n")
            else:
                f.write("EMPTY\n")
        except Exception as e:
            f.write(f"ERROR: {e}\n")

if __name__ == "__main__":
    dump_keys("AAPL", "data_structure_debug.txt")
