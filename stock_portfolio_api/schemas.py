"""
Pydantic schemas for API request and response models.
"""

from typing import List
from pydantic import BaseModel, Field, field_validator


class PortfolioInput(BaseModel):
    """Input schema for portfolio suggestion request."""
    
    investment_amount: float = Field(..., ge=5000, description="Investment amount in USD (minimum $5000)")
    strategies: List[str] = Field(..., min_length=1, max_length=2, description="List of investment strategies (1-2 strategies)")
    
    @field_validator('strategies')
    @classmethod
    def validate_strategies(cls, v):
        """Validate that all strategies are in the allowed set."""
        from .constants import ALLOWED_STRATEGIES
        invalid_strategies = set(v) - ALLOWED_STRATEGIES
        if invalid_strategies:
            raise ValueError(f"Invalid strategies: {invalid_strategies}. Allowed strategies: {ALLOWED_STRATEGIES}")
        return v


class Holding(BaseModel):
    """Schema for a single stock holding."""
    
    ticker: str
    allocated_usd: float
    shares_purchased: int


class WeeklyValue(BaseModel):
    """Schema for weekly portfolio value data point."""
    
    date: str
    portfolio_value_usd: float


class PortfolioSuggestion(BaseModel):
    """Response schema for portfolio suggestion."""
    
    suggested_holdings: List[Holding]
    current_total_value_usd: float
    weekly_value_trend: List[WeeklyValue]
    leftover_cash_usd: float

