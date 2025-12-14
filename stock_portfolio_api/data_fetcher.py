"""
Data fetching module using yfinance for live and historical stock data.
All functions are synchronous as yfinance is synchronous.
"""

import yfinance as yf
import pandas as pd
from typing import Dict, List, Any


def get_live_prices(tickers: List[str]) -> Dict[str, float]:
    """
    Fetch current live prices for given tickers.
    """
    if not tickers:
        return {}
        
    try:
        # Use string join for single API call
        tickers_obj = yf.Tickers(" ".join(tickers))
        prices = {}
        
        for ticker in tickers:
            try:
                # Optimized: Access fast_info first if available (faster than .info)
                t_obj = tickers_obj.tickers[ticker]
                
                # fast_info is a newer yfinance feature for real-time data
                if hasattr(t_obj, 'fast_info'):
                     current_price = t_obj.fast_info.get('last_price')
                else:
                     info = t_obj.info
                     current_price = info.get('currentPrice') or info.get('regularMarketPrice')

                if current_price:
                    prices[ticker] = float(current_price)
                else:
                    # Fallback to history
                    hist = t_obj.history(period="1d")
                    if not hist.empty:
                        prices[ticker] = float(hist['Close'].iloc[-1])
                    else:
                        print(f"Warning: Could not fetch price for {ticker}")
            except Exception as e:
                print(f"Error fetching price for {ticker}: {str(e)}")
        
        return prices
    except Exception as e:
        raise RuntimeError(f"Failed to fetch live prices: {str(e)}")


def get_historical_data(tickers: List[str]) -> pd.DataFrame:
    """
    Fetch historical stock data.
    CHANGED: Increased period from '7d' to '3mo' to allow for 
    moving average calculation (trend analysis).
    """
    if not tickers:
        return pd.DataFrame()

    try:
        # Fetch 3 months to ensure we have enough data for 20-day or 50-day MA
        data = yf.download(" ".join(tickers), period="3mo", progress=False)
        
        if data.empty:
            raise ValueError("No historical data retrieved")
        
        # Handle the yfinance structure
        # yfinance returns a MultiIndex (Price, Ticker) if multiple tickers
        if isinstance(data.columns, pd.MultiIndex):
            # Return just the Close prices. Columns will be the Tickers.
            return data['Close']
        else:
            # Single ticker case: Columns are just 'Open', 'Close', etc.
            # We wrap it to match the structure of the multi-ticker return
            df = pd.DataFrame(data['Close'])
            df.columns = tickers if len(tickers) == 1 else df.columns
            return df
    except Exception as e:
        raise RuntimeError(f"Failed to fetch historical data: {str(e)}")


def get_ticker_details(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetch detailed info (P/E, Growth, Sector) for screening.
    """
    details = {}
    # Note: Fetching .info is slow. In production, cache this or use a database.
    try:
        ytickers = yf.Tickers(" ".join(tickers))
        for ticker in tickers:
            try:
                details[ticker] = ytickers.tickers[ticker].info
            except Exception:
                continue
    except Exception as e:
        print(f"Error fetching details: {e}")
    return details