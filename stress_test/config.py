import datetime

# 回測設定
START_DATE = "2014-01-01"
END_DATE = datetime.datetime.now().strftime("%Y-%m-%d")
BENCHMARK_SYMBOL = "SPY"
VIX_SYMBOL = "^VIX"

# 壓力測試區間 (Flash Crash, Trade War, COVID, Inflation)
STRESS_PERIODS = {
    "2015_Flash_Crash": ("2015-08-15", "2015-09-15"),
    "2018_Trade_War": ("2018-09-20", "2018-12-30"),
    "2020_COVID_Crash": ("2020-02-15", "2020-03-30"),
    "2022_Bear_Market": ("2022-01-01", "2022-10-15")
}

# 資金設定
INITIAL_CAPITAL = 100000  # 模擬總資金
