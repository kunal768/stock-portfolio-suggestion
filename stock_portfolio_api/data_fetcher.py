"""
Data fetching module using yfinance for live and historical stock data.
All functions are synchronous as yfinance is synchronous.
"""

import yfinance as yf
import pandas as pd
from typing import Dict, List


def get_live_prices(tickers: List[str]) -> Dict[str, float]:
    """
    Fetch current live prices for given tickers.
    
    Args:
        tickers: List of stock ticker symbols
        
    Returns:
        Dictionary mapping ticker to current price
        
    Raises:
        Exception: If yfinance API call fails
    """
    try:
        tickers_obj = yf.Tickers(" ".join(tickers))
        prices = {}
        
        for ticker in tickers:
            try:
                info = tickers_obj.tickers[ticker].info
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                if current_price:
                    prices[ticker] = float(current_price)
                else:
                    # Fallback: try to get last close price
                    hist = tickers_obj.tickers[ticker].history(period="1d")
                    if not hist.empty:
                        prices[ticker] = float(hist['Close'].iloc[-1])
                    else:
                        raise ValueError(f"Could not fetch price for {ticker}")
            except Exception as e:
                raise ValueError(f"Error fetching price for {ticker}: {str(e)}")
        
        return prices
    except Exception as e:
        raise RuntimeError(f"Failed to fetch live prices: {str(e)}")


def get_historical_data(tickers: List[str]) -> pd.DataFrame:
    """
    Fetch historical stock data for the last 7 days.
    
    Args:
        tickers: List of stock ticker symbols
        
    Returns:
        DataFrame with Date index and Close price columns for each ticker
        
    Raises:
        Exception: If yfinance API call fails
    """
    try:
        # Download 7-day period to ensure we get ~5 trading days
        data = yf.download(" ".join(tickers), period="7d", progress=False)
        
        if data.empty:
            raise ValueError("No historical data retrieved")
        
        # Handle MultiIndex columns (when multiple tickers)
        if isinstance(data.columns, pd.MultiIndex):
            # Extract Close prices only
            close_data = data['Close']
        else:
            # Single ticker case
            close_data = pd.DataFrame(data['Close'])
            close_data.columns = [tickers[0]]
        
        return close_data
    except Exception as e:
        raise RuntimeError(f"Failed to fetch historical data: {str(e)}")

