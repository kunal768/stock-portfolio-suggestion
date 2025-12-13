"""
Core financial calculation logic for portfolio allocation and value tracking.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from .constants import STRATEGIES_MAP


def process_tickers(strategies: List[str]) -> List[str]:
    """
    Process strategies and return deduplicated list of tickers.
    
    Args:
        strategies: List of strategy names
        
    Returns:
        Deduplicated list of ticker symbols
    """
    all_tickers = []
    
    for strategy in strategies:
        if strategy not in STRATEGIES_MAP:
            raise ValueError(f"Unknown strategy: {strategy}")
        all_tickers.extend(STRATEGIES_MAP[strategy])
    
    # Return deduplicated list while preserving order
    seen = set()
    unique_tickers = []
    for ticker in all_tickers:
        if ticker not in seen:
            seen.add(ticker)
            unique_tickers.append(ticker)
    
    return unique_tickers


def calculate_allocation(amount: float, tickers: List[str], live_prices: Dict[str, float]) -> Tuple[pd.DataFrame, float]:
    """
    Calculate equal dollar allocation per ticker and shares purchased.
    
    Args:
        amount: Total investment amount in USD
        tickers: List of ticker symbols
        live_prices: Dictionary mapping ticker to current price
        
    Returns:
        Tuple of (allocation DataFrame, leftover cash)
        DataFrame has columns: ticker, allocated_usd, shares_purchased
    """
    if not tickers:
        raise ValueError("Tickers list cannot be empty")
    
    # Equal dollar allocation per ticker
    allocation_per_ticker = amount / len(tickers)
    
    allocations = []
    total_used = 0.0
    
    for ticker in tickers:
        if ticker not in live_prices:
            raise ValueError(f"Price not found for ticker: {ticker}")
        
        price = live_prices[ticker]
        if price <= 0:
            raise ValueError(f"Invalid price for {ticker}: {price}")
        
        # Calculate shares using floor division (no fractional shares)
        shares = int(np.floor(allocation_per_ticker / price))
        allocated_usd = shares * price
        total_used += allocated_usd
        
        allocations.append({
            'ticker': ticker,
            'allocated_usd': allocated_usd,
            'shares_purchased': shares
        })
    
    allocation_df = pd.DataFrame(allocations)
    leftover_cash = amount - total_used
    
    return allocation_df, leftover_cash


def calculate_current_value(allocation_df: pd.DataFrame, live_prices: Dict[str, float]) -> float:
    """
    Calculate current total portfolio value.
    
    Args:
        allocation_df: DataFrame with columns: ticker, allocated_usd, shares_purchased
        live_prices: Dictionary mapping ticker to current price
        
    Returns:
        Current total portfolio value in USD
    """
    total_value = 0.0
    
    for _, row in allocation_df.iterrows():
        ticker = row['ticker']
        shares = row['shares_purchased']
        
        if ticker not in live_prices:
            raise ValueError(f"Price not found for ticker: {ticker}")
        
        current_price = live_prices[ticker]
        total_value += shares * current_price
    
    return total_value


def calculate_weekly_trend(allocation_df: pd.DataFrame, historical_df: pd.DataFrame) -> List[Dict[str, float]]:
    """
    Calculate portfolio value for each of the last 5 trading days.
    
    Args:
        allocation_df: DataFrame with columns: ticker, allocated_usd, shares_purchased
        historical_df: DataFrame with Date index and Close price columns for each ticker
        
    Returns:
        List of dictionaries with 'date' and 'portfolio_value_usd' keys
    """
    # Get the last 5 trading days (or fewer if less data available)
    num_days = min(5, len(historical_df))
    recent_data = historical_df.tail(num_days)
    
    weekly_trend = []
    
    for date, row in recent_data.iterrows():
        portfolio_value = 0.0
        
        for _, allocation_row in allocation_df.iterrows():
            ticker = allocation_row['ticker']
            shares = allocation_row['shares_purchased']
            
            # Handle MultiIndex columns
            if ticker in row.index:
                close_price = row[ticker]
            elif isinstance(row.index, pd.MultiIndex):
                # Try to find the ticker in the MultiIndex
                close_price = None
                for col in row.index:
                    if col[1] == ticker or col == ticker:
                        close_price = row[col]
                        break
                if close_price is None:
                    continue
            else:
                # Single ticker case
                close_price = row.iloc[0] if len(row) == 1 else None
            
            if close_price is not None and not pd.isna(close_price):
                portfolio_value += shares * float(close_price)
        
        # Format date as string (YYYY-MM-DD)
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
        
        weekly_trend.append({
            'date': date_str,
            'portfolio_value_usd': round(portfolio_value, 2)
        })
    
    return weekly_trend

