"""
FastAPI application for stock portfolio suggestions.
"""

from fastapi import FastAPI, HTTPException
from starlette.concurrency import run_in_threadpool
from .schemas import PortfolioInput, PortfolioSuggestion, Holding, WeeklyValue
from .portfolio_logic import (
    process_tickers,
    calculate_allocation,
    calculate_current_value,
    calculate_weekly_trend
)
from .data_fetcher import get_live_prices, get_historical_data

app = FastAPI(
    title="Stock Portfolio API",
    description="API for generating stock portfolio suggestions based on investment strategies",
    version="1.0.0"
)


@app.post("/api/v1/suggest_portfolio", response_model=PortfolioSuggestion)
async def suggest_portfolio(input_data: PortfolioInput) -> PortfolioSuggestion:
    """
    Generate a portfolio suggestion based on investment amount and strategies.
    
    Args:
        input_data: PortfolioInput containing investment_amount and strategies
        
    Returns:
        PortfolioSuggestion with holdings, current value, weekly trend, and leftover cash
        
    Raises:
        HTTPException: If data fetching or calculation fails
    """
    try:
        # Step 1: Process strategies and get tickers
        tickers = process_tickers(input_data.strategies)
        
        if not tickers:
            raise HTTPException(
                status_code=400,
                detail="No valid tickers found for the given strategies"
            )
        
        # Step 2: Fetch data using thread pool (yfinance is synchronous)
        try:
            live_prices = await run_in_threadpool(get_live_prices, tickers)
            historical_df = await run_in_threadpool(get_historical_data, tickers)
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to fetch stock data: {str(e)}"
            )
        
        # Step 3: Calculate allocation
        try:
            allocation_df, leftover_cash = calculate_allocation(
                input_data.investment_amount,
                tickers,
                live_prices
            )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to calculate allocation: {str(e)}"
            )
        
        # Step 4: Calculate current value
        try:
            current_total_value = calculate_current_value(allocation_df, live_prices)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to calculate current value: {str(e)}"
            )
        
        # Step 5: Calculate weekly trend
        try:
            weekly_trend_data = calculate_weekly_trend(allocation_df, historical_df)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to calculate weekly trend: {str(e)}"
            )
        
        # Step 6: Construct response
        holdings = [
            Holding(
                ticker=row['ticker'],
                allocated_usd=round(row['allocated_usd'], 2),
                shares_purchased=int(row['shares_purchased'])
            )
            for _, row in allocation_df.iterrows()
        ]
        
        weekly_value_trend = [
            WeeklyValue(
                date=item['date'],
                portfolio_value_usd=item['portfolio_value_usd']
            )
            for item in weekly_trend_data
        ]
        
        return PortfolioSuggestion(
            suggested_holdings=holdings,
            current_total_value_usd=round(current_total_value, 2),
            weekly_value_trend=weekly_value_trend,
            leftover_cash_usd=round(leftover_cash, 2)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Stock Portfolio API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

