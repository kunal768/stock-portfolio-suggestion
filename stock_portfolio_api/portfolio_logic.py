"""
Core financial calculation logic for portfolio allocation and value tracking.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from .constants import CANDIDATE_TICKERS

# We need a reference to the data fetcher to get info for screening
from .data_fetcher import get_ticker_details 


def process_tickers(strategies: List[str]) -> List[str]:
    """
    Process strategies and return deduplicated list of tickers based on dynamic filtering.
    """
    selected_tickers = []
    
    # Pre-fetch details for candidates once to avoid repeated calls
    # Optimization: Only fetch if we are NOT doing Index Investing (which uses fixed ETFs)
    needs_screening = any(s != "Index Investing" for s in strategies)
    candidate_details = get_ticker_details(CANDIDATE_TICKERS) if needs_screening else {}

    for strategy in strategies:
        if strategy == "Index Investing":
            # Hardcoded ETFs for Index strategy
            selected_tickers.extend(["VOO", "QQQ", "VTI", "BND", "IVV", "SPY"])
            continue

        # Filter candidates based on strategy logic
        for ticker, info in candidate_details.items():
            if not info: continue

            if ticker in ["VOO", "QQQ", "VTI", "SPY", "IVV", "BND"]:
                continue  # Skip index ETFs for other strategies
            
            try:
                match strategy:
                    case "Ethical Investing":
                        # Exclude 'sin' sectors
                        sector = info.get('sector', '')
                        if sector not in ['Energy', 'Utilities', 'Basic Materials']:
                            selected_tickers.append(ticker)
                            
                    case "Growth Investing":
                        # Revenue growth > 15%
                        growth = info.get('revenueGrowth', 0)
                        if growth and growth > 0.15:
                            selected_tickers.append(ticker)
                            
                    case "Quality Investing":
                        # ROE > 15% and Debt/Equity < 50
                        roe = info.get('returnOnEquity', 0)
                        debt_equity = info.get('debtToEquity', 100)
                        if roe and roe > 0.15 and debt_equity < 50:
                            selected_tickers.append(ticker)
                            
                    case "Value Investing":
                        # P/E Ratio < 25 (Generic value threshold)
                        pe = info.get('trailingPE')
                        if pe and 0 < pe < 25:
                            selected_tickers.append(ticker)
            except Exception:
                continue

    # De-duplicate while preserving order
    seen = set()
    unique_tickers = []
    # If no stocks passed the filter, fallback to a safe default (e.g. MSFT) to prevent crashes
    if not selected_tickers and strategies:
        unique_tickers = ["MSFT"] 
    else:
        for ticker in selected_tickers:
            if ticker not in seen:
                seen.add(ticker)
                unique_tickers.append(ticker)
    
    # Limit portfolio size to avoid spreading too thin (e.g. max 10 stocks)
    return unique_tickers[:10]

def calculate_allocation(
    amount: float, 
    tickers: List[str], 
    live_prices: Dict[str, float], 
    historical_df: pd.DataFrame = None
) -> Tuple[pd.DataFrame, float]:
    
    if not tickers:
        raise ValueError("Tickers list cannot be empty")

    weights = {ticker: 1.0 for ticker in tickers}
    
    if historical_df is not None and not historical_df.empty:
        # Calculate 20-day Simple Moving Average (SMA) for trend analysis
        # We use min_periods=5 so we get a result even if the stock is somewhat new
        sma_20 = historical_df.rolling(window=20, min_periods=5).mean().iloc[-1]
        
        for ticker in tickers:
            if ticker not in live_prices: 
                continue
            
            current_price = live_prices[ticker]
            
            # Check if we have a valid MA for this ticker in the history
            if ticker in sma_20.index and not pd.isna(sma_20[ticker]):
                avg_price = sma_20[ticker]
                
                if avg_price > 0:
                    # Score = Price / MA
                    # If Price > MA, Score > 1.0 (allocate more)
                    # If Price < MA, Score < 1.0 (allocate less)
                    trend_score = current_price / avg_price
                    
                    # Square the score to amplify the difference
                    weights[ticker] = trend_score ** 2

    total_weight = sum(weights.values())
    
    if total_weight == 0:
        normalized_weights = {t: 1.0 / len(tickers) for t in tickers}
    else:
        normalized_weights = {t: w / total_weight for t, w in weights.items()}

    allocations = []
    total_used = 0.0
    
    for ticker in tickers:
        if ticker not in live_prices: 
            continue
        
        price = live_prices[ticker]
        if price <= 0: 
            continue
        
        target_allocation = amount * normalized_weights.get(ticker, 0)
        
        shares = int(np.floor(target_allocation / price))
        allocated_usd = shares * price
        
        if shares > 0:
            total_used += allocated_usd
            allocations.append({
                'ticker': ticker,
                'allocated_usd': allocated_usd,
                'shares_purchased': shares,
                'weight_pct': round(normalized_weights[ticker] * 100, 2)
            })
    
    allocation_df = pd.DataFrame(allocations)
    leftover_cash = amount - total_used
    
    return allocation_df, leftover_cash

def calculate_current_value(allocation_df: pd.DataFrame, live_prices: Dict[str, float]) -> float:
    """
    Calculate current total portfolio value.
    """
    if allocation_df.empty:
        return 0.0
        
    total_value = 0.0
    
    for _, row in allocation_df.iterrows():
        ticker = row['ticker']
        shares = row['shares_purchased']
        
        if ticker in live_prices:
            total_value += shares * live_prices[ticker]
    
    return total_value


def calculate_weekly_trend(allocation_df: pd.DataFrame, historical_df: pd.DataFrame) -> List[Dict[str, float]]:
    """
    Calculate portfolio value for each of the last 5 trading days.
    """
    if allocation_df.empty or historical_df.empty:
        return []

    # Get the last 5 trading days
    num_days = min(5, len(historical_df))
    recent_data = historical_df.tail(num_days)
    
    weekly_trend = []
    
    for date, row in recent_data.iterrows():
        portfolio_value = 0.0
        
        for _, allocation_row in allocation_df.iterrows():
            ticker = allocation_row['ticker']
            shares = allocation_row['shares_purchased']
            
            # Robust logic for extracting price from history
            close_price = None
            
            # 1. Direct column access (common in single-level columns)
            if ticker in row.index:
                close_price = row[ticker]
            # 2. Multi-index handling (common in yfinance bulk download)
            elif isinstance(historical_df.columns, pd.MultiIndex):
                try:
                     # Access directly if the column structure is (Ticker, 'Close') or similar
                     if (ticker, 'Close') in historical_df.columns:
                         close_price = row[(ticker, 'Close')]
                     # Or sometimes it's reversed or just Ticker at level 0
                     else:
                         # Fallback search
                         val = row.xs(ticker, level=0, drop_level=False)
                         if not val.empty:
                             close_price = val.iloc[0]
                except:
                    pass
            
            # 3. Fallback for single ticker dataframe where column is just 'Close'
            elif len(allocation_df) == 1 and 'Close' in row.index:
                 close_price = row['Close']

            if close_price is not None and not pd.isna(close_price):
                portfolio_value += shares * float(close_price)
        
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
        
        weekly_trend.append({
            'date': date_str,
            'portfolio_value_usd': round(portfolio_value, 2)
        })
    
    return weekly_trend