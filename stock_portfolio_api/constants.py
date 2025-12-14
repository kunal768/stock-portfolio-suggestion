"""
Constants for the Stock Portfolio API.
"""

MIN_INVESTMENT_USD = 5000

ALLOWED_STRATEGIES = {
    "Ethical Investing", 
    "Growth Investing", 
    "Index Investing", 
    "Quality Investing", 
    "Value Investing"
}

# A pool of candidate tickers to screen against for dynamic strategies
CANDIDATE_TICKERS = [
    # --- The Index ETFs ---
    "VOO", "QQQ", "VTI", "BND", "IVV", "SPY",

    # --- High Growth Candidates ---
    "NVDA", "TSLA", "AMD", "SHOP", "SNOW", 
    
    # --- Ethical / Quality / Value Candidates ---
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "JPM", "JNJ", 
    "V", "PG", "MA", "HD", "CVX", "MRK", "ABBV", "PEP", "KO", "BAC", "COST", "ADBE", "CRM"
]