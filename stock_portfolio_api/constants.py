"""
Constants for the Stock Portfolio API.
"""

MIN_INVESTMENT_USD = 5000

ALLOWED_STRATEGIES = {"tech", "dividend", "growth", "value"}

STRATEGIES_MAP = {
    "tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "META"],
    "dividend": ["JNJ", "PG", "KO", "PEP", "WMT"],
    "growth": ["TSLA", "NVDA", "AMD", "NFLX", "DIS"],
    "value": ["BRK.B", "JPM", "V", "MA", "HD"],
}

