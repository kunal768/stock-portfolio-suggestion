# Stock Portfolio Suggestion Engine

A FastAPI backend with Streamlit UI for generating stock portfolio suggestions based on investment strategies.

![Home Screen](public/home_screen.png)

## Features

- **FastAPI Backend**: RESTful API for portfolio calculations
- **Streamlit UI**: Beautiful, interactive web interface with real-time updates
- **Multiple Strategies**: Tech, Dividend, Growth, and Value investment strategies
- **Real-time Data**: Fetches live stock prices using yfinance
- **Auto-refresh**: Automatically updates portfolio values at configurable intervals
- **Interactive Charts**: Plotly charts showing portfolio value trends

## Project Structure

```
stock-portfolio-suggestion/
├── stock_portfolio_api/          # FastAPI backend
│   ├── main.py                   # API endpoints
│   ├── constants.py              # Strategy definitions
│   ├── schemas.py                # Pydantic models
│   ├── data_fetcher.py           # yfinance integration
│   ├── portfolio_logic.py        # Financial calculations
│   └── requirements.txt          # Backend dependencies
├── ui/                           # Streamlit frontend
│   ├── app.py                    # Main UI application
│   └── requirements.txt          # UI dependencies
└── README.md                     # This file
```

## Installation

### Backend Setup

1. Navigate to the project directory:
```bash
cd stock-portfolio-suggestion
```

2. Install backend dependencies:
```bash
pip install -r stock_portfolio_api/requirements.txt
```

### UI Setup

1. Install UI dependencies:
```bash
pip install -r ui/requirements.txt
```

## Running the Application

### Step 1: Start the FastAPI Backend

In one terminal window:
```bash
uvicorn stock_portfolio_api.main:app --reload
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Step 2: Start the Streamlit UI

In another terminal window:
```bash
streamlit run ui/app.py
```

The UI will automatically open in your browser at `http://localhost:8501`

## Usage

### Using the Streamlit UI

1. **Configure Investment**:
   - Enter investment amount (minimum $5,000)
   - Select 1-2 investment strategies:
     - **Tech**: Technology stocks (AAPL, MSFT, GOOGL, AMZN, META)
     - **Dividend**: Dividend-paying stocks (JNJ, PG, KO, PEP, WMT)
     - **Growth**: Growth stocks (TSLA, NVDA, AMD, NFLX, DIS)
     - **Value**: Value stocks (BRK.B, JPM, V, MA, HD)

2. **Generate Portfolio**: Click "Generate Portfolio" button

![Investment Suggestions](public/investment_suggestions.png)

3. **View Results**:
   - Summary metrics (Total Investment, Current Value, Leftover Cash)
   - Portfolio holdings table
   - Interactive portfolio value trend chart

![Portfolio Value Trend](public/portfolio_value_trend_last_5day.png)

![Individual Stock Description](public/individual_stock_description_realtime.png)

4. **Auto-Refresh**: Enable auto-refresh to see real-time portfolio value updates

### Using the API Directly

**Endpoint**: `POST /api/v1/suggest_portfolio`

**Request Body**:
```json
{
  "investment_amount": 10000,
  "strategies": ["tech", "dividend"]
}
```

**Response**:
```json
{
  "suggested_holdings": [
    {
      "ticker": "AAPL",
      "allocated_usd": 1000.0,
      "shares_purchased": 5
    }
  ],
  "current_total_value_usd": 10050.0,
  "weekly_value_trend": [
    {
      "date": "2024-01-15",
      "portfolio_value_usd": 10000.0
    }
  ],
  "leftover_cash_usd": 50.0
}
```

## Investment Strategies

- **Tech**: Focus on technology companies
- **Dividend**: Focus on dividend-paying stocks
- **Growth**: Focus on high-growth companies
- **Value**: Focus on undervalued stocks

## Requirements

### Backend
- Python 3.8+
- fastapi
- uvicorn[standard]
- yfinance
- pandas
- numpy<2.0
- pydantic

### UI
- streamlit
- requests
- plotly
- pandas

## Notes

- The API uses yfinance to fetch real-time stock data
- Portfolio allocation uses equal dollar distribution per ticker
- Shares are calculated using floor division (no fractional shares)
- Historical data covers the last 7 days to ensure ~5 trading days
- Auto-refresh interval is configurable (default: 30 seconds)

## Troubleshooting

**API Connection Error**: Make sure the FastAPI backend is running on port 8000

**NumPy Compatibility**: If you encounter NumPy 2.x compatibility issues, ensure numpy<2.0 is installed

**Port Already in Use**: Change the port using:
- Backend: `uvicorn stock_portfolio_api.main:app --port 8001`
- UI: `streamlit run ui/app.py --server.port 8502`
