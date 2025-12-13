"""
Streamlit UI for Stock Portfolio Suggestion Engine.
"""

import streamlit as st
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import time
from typing import Optional, Dict, List
import yfinance as yf

# Page configuration
st.set_page_config(
    page_title="Stock Portfolio Suggestion",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{API_BASE_URL}/api/v1/suggest_portfolio"

# Initialize session state
if 'portfolio_data' not in st.session_state:
    st.session_state.portfolio_data = None
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = 30
if 'next_refresh_time' not in st.session_state:
    st.session_state.next_refresh_time = None
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None


def format_currency(amount: float) -> str:
    """Format amount as USD currency."""
    return f"${amount:,.2f}"


def calculate_gain_loss(current_value: float, investment_amount: float) -> tuple[float, str]:
    """Calculate gain/loss percentage and color."""
    change = current_value - investment_amount
    percent_change = (change / investment_amount) * 100 if investment_amount > 0 else 0
    color = "green" if change >= 0 else "red"
    sign = "+" if change >= 0 else ""
    return percent_change, f"{sign}{percent_change:.2f}%", color


@st.cache_data(ttl=5)
def get_portfolio_suggestion(investment_amount: float, strategies: List[str]) -> Optional[Dict]:
    """
    Call FastAPI backend to get portfolio suggestion.
    
    Args:
        investment_amount: Investment amount in USD
        strategies: List of strategy names (1-2 strategies)
        
    Returns:
        Portfolio suggestion dictionary or None if error
    """
    try:
        payload = {
            "investment_amount": investment_amount,
            "strategies": strategies
        }
        response = requests.post(API_ENDPOINT, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API. Make sure the FastAPI backend is running on http://localhost:8000")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Please try again.")
        return None
    except requests.exceptions.HTTPError as e:
        error_msg = "Unknown error"
        try:
            error_data = response.json()
            error_msg = error_data.get("detail", str(e))
        except:
            error_msg = str(e)
        st.error(f"❌ API Error: {error_msg}")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None


def create_trend_chart(weekly_trend: List[Dict]) -> go.Figure:
    """Create interactive line chart for portfolio value trend."""
    if not weekly_trend:
        return None
    
    dates = [item['date'] for item in weekly_trend]
    values = [item['portfolio_value_usd'] for item in weekly_trend]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines+markers',
        name='Portfolio Value',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8, color='#1f77b4'),
        hovertemplate='<b>Date:</b> %{x}<br><b>Value:</b> $%{y:,.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title={
            'text': 'Portfolio Value Trend (Last 5 Trading Days)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title='Date',
        yaxis_title='Portfolio Value (USD)',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig


@st.cache_data(ttl=60)
def get_stock_details(ticker: str) -> Optional[Dict]:
    """
    Fetch stock details using yfinance.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with stock details or None if error
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get current price
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('regularMarketPreviousClose')
        
        # Get historical data for day change
        hist = stock.history(period="2d")
        day_change = None
        day_change_percent = None
        if not hist.empty and len(hist) >= 2:
            prev_close = hist['Close'].iloc[-2]
            if current_price:
                day_change = current_price - prev_close
                day_change_percent = (day_change / prev_close) * 100 if prev_close > 0 else 0
        
        return {
            'ticker': ticker,
            'name': info.get('longName') or info.get('shortName', ticker),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'current_price': current_price,
            'day_change': day_change,
            'day_change_percent': day_change_percent,
            'market_cap': info.get('marketCap'),
            'volume': info.get('volume') or info.get('averageVolume'),
            '52_week_high': info.get('fiftyTwoWeekHigh'),
            '52_week_low': info.get('fiftyTwoWeekLow'),
            'pe_ratio': info.get('trailingPE'),
            'dividend_yield': info.get('dividendYield'),
            'description': info.get('longBusinessSummary', 'No description available.'),
            'website': info.get('website', 'N/A'),
            'employees': info.get('fullTimeEmployees'),
        }
    except Exception as e:
        st.error(f"❌ Error fetching details for {ticker}: {str(e)}")
        return None


def display_stock_details(ticker: str):
    """Display detailed stock information in an expandable section."""
    with st.spinner(f"Loading details for {ticker}..."):
        details = get_stock_details(ticker)
    
    if not details:
        return
    
    st.markdown("---")
    st.subheader(f"📊 Stock Details: {details['ticker']}")
    
    # Header with name and price
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"### {details['name']}")
        st.caption(f"{details['sector']} • {details['industry']}")
    
    with col2:
        if details['current_price']:
            price_str = format_currency(details['current_price'])
            if details['day_change'] is not None:
                change_color = "normal" if details['day_change'] >= 0 else "inverse"
                change_str = f"{'+' if details['day_change'] >= 0 else ''}{format_currency(details['day_change'])} ({'+' if details['day_change_percent'] >= 0 else ''}{details['day_change_percent']:.2f}%)"
                st.metric("Current Price", price_str, delta=change_str, delta_color=change_color)
            else:
                st.metric("Current Price", price_str)
    
    # Key metrics in columns
    st.markdown("#### Key Metrics")
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        if details['market_cap']:
            market_cap_billions = details['market_cap'] / 1e9
            st.metric("Market Cap", f"${market_cap_billions:.2f}B")
        if details['pe_ratio']:
            st.metric("P/E Ratio", f"{details['pe_ratio']:.2f}")
    
    with metric_col2:
        if details['52_week_high']:
            st.metric("52W High", format_currency(details['52_week_high']))
        if details['52_week_low']:
            st.metric("52W Low", format_currency(details['52_week_low']))
    
    with metric_col3:
        if details['volume']:
            volume_millions = details['volume'] / 1e6
            st.metric("Volume", f"{volume_millions:.2f}M")
        if details['dividend_yield']:
            st.metric("Dividend Yield", f"{details['dividend_yield'] * 100:.2f}%")
    
    with metric_col4:
        if details['employees']:
            employees_thousands = details['employees'] / 1000
            st.metric("Employees", f"{employees_thousands:.1f}K")
        if details['website'] and details['website'] != 'N/A':
            st.markdown(f"[🌐 Website]({details['website']})")
    
    # Company description
    if details['description'] and details['description'] != 'No description available.':
        with st.expander("📝 Company Description"):
            st.write(details['description'])


def main():
    """Main Streamlit application."""
    
    # Custom CSS for styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stMetric {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<p class="main-header">📈 Stock Portfolio Suggestion Engine</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Investment amount input
        investment_amount = st.number_input(
            "Investment Amount (USD)",
            min_value=5000.0,
            value=10000.0,
            step=1000.0,
            help="Minimum investment: $5,000"
        )
        
        # Strategy selection
        available_strategies = ["tech", "dividend", "growth", "value"]
        selected_strategies = st.multiselect(
            "Select Investment Strategies",
            options=available_strategies,
            default=["tech"],
            max_selections=2,
            help="Select 1-2 investment strategies"
        )
        
        # Submit button
        submit_button = st.button("🚀 Generate Portfolio", type="primary", use_container_width=True)
        
        st.divider()
        
        # Auto-refresh settings
        st.subheader("🔄 Auto-Refresh")
        auto_refresh_enabled = st.checkbox(
            "Enable Auto-Refresh",
            value=st.session_state.auto_refresh,
            help="Automatically refresh portfolio values"
        )
        st.session_state.auto_refresh = auto_refresh_enabled
        
        if auto_refresh_enabled:
            refresh_interval = st.slider(
                "Refresh Interval (seconds)",
                min_value=10,
                max_value=120,
                value=st.session_state.refresh_interval,
                step=10
            )
            st.session_state.refresh_interval = refresh_interval
        
        # API status
        st.divider()
        st.subheader("🔌 API Status")
        try:
            health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if health_response.status_code == 200:
                st.success("✅ API Connected")
            else:
                st.warning("⚠️ API Status Unknown")
        except:
            st.error("❌ API Disconnected")
    
    # Main content area
    if submit_button or st.session_state.portfolio_data is not None:
        if submit_button:
            # Validate inputs
            if not selected_strategies:
                st.error("⚠️ Please select at least one investment strategy.")
                return
            
            if len(selected_strategies) > 2:
                st.error("⚠️ Please select a maximum of 2 strategies.")
                return
            
            # Show loading spinner
            with st.spinner("🔄 Fetching portfolio data..."):
                portfolio_data = get_portfolio_suggestion(investment_amount, selected_strategies)
                
                if portfolio_data:
                    st.session_state.portfolio_data = portfolio_data
                    st.session_state.last_update = datetime.now()
                    st.session_state.next_refresh_time = datetime.now()
                    st.success("✅ Portfolio generated successfully!")
        
        # Display portfolio data if available
        if st.session_state.portfolio_data:
            portfolio = st.session_state.portfolio_data
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Investment",
                    format_currency(investment_amount),
                    delta=None
                )
            
            with col2:
                current_value = portfolio['current_total_value_usd']
                percent_change, change_str, color = calculate_gain_loss(current_value, investment_amount)
                st.metric(
                    "Current Value",
                    format_currency(current_value),
                    delta=change_str,
                    delta_color="normal" if percent_change >= 0 else "inverse"
                )
            
            with col3:
                leftover_cash = portfolio['leftover_cash_usd']
                st.metric(
                    "Leftover Cash",
                    format_currency(leftover_cash),
                    delta=None
                )
            
            with col4:
                total_allocated = investment_amount - leftover_cash
                allocation_percent = (total_allocated / investment_amount) * 100 if investment_amount > 0 else 0
                st.metric(
                    "Allocation Rate",
                    f"{allocation_percent:.1f}%",
                    delta=None
                )
            
            st.divider()
            
            # Portfolio holdings table
            st.subheader("📊 Portfolio Holdings")
            st.caption("💡 Select a ticker from the dropdown or click a button below to view detailed stock information")
            
            holdings_data = []
            ticker_list = []
            for holding in portfolio['suggested_holdings']:
                holdings_data.append({
                    'Ticker': holding['ticker'],
                    'Allocated USD': holding['allocated_usd'],
                    'Shares': holding['shares_purchased']
                })
                ticker_list.append(holding['ticker'])
            
            holdings_df = pd.DataFrame(holdings_data)
            holdings_df['Allocated USD'] = holdings_df['Allocated USD'].apply(lambda x: format_currency(x))
            
            # Display table
            st.dataframe(
                holdings_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Ticker selection section
            st.markdown("#### 🔍 View Stock Details")
            
            # Dropdown for ticker selection
            selected_ticker = st.selectbox(
                "Select a ticker to view details:",
                options=["Select a ticker..."] + ticker_list,
                index=0 if st.session_state.selected_ticker is None else (ticker_list.index(st.session_state.selected_ticker) + 1 if st.session_state.selected_ticker in ticker_list else 0),
                key="ticker_selectbox"
            )
            
            # Quick access buttons for each ticker
            st.markdown("**Quick Access:**")
            button_cols = st.columns(min(len(ticker_list), 5))
            for idx, ticker in enumerate(ticker_list):
                with button_cols[idx % len(button_cols)]:
                    if st.button(f"📈 {ticker}", key=f"btn_{ticker}", use_container_width=True):
                        st.session_state.selected_ticker = ticker
                        st.rerun()
            
            # Update selected ticker from dropdown
            if selected_ticker and selected_ticker != "Select a ticker...":
                st.session_state.selected_ticker = selected_ticker
            elif selected_ticker == "Select a ticker...":
                st.session_state.selected_ticker = None
            
            # Display stock details if a ticker is selected
            if st.session_state.selected_ticker:
                display_stock_details(st.session_state.selected_ticker)
            
            st.divider()
            
            # Portfolio value trend chart
            st.subheader("📈 Portfolio Value Trend")
            if portfolio['weekly_value_trend']:
                fig = create_trend_chart(portfolio['weekly_value_trend'])
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No trend data available.")
            
            # Refresh controls
            refresh_col1, refresh_col2 = st.columns([3, 1])
            
            with refresh_col1:
                if st.session_state.last_update:
                    st.caption(f"Last updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
                    if st.session_state.auto_refresh:
                        current_time = datetime.now()
                        if st.session_state.last_update:
                            time_since_last_update = (current_time - st.session_state.last_update).total_seconds()
                            time_until_refresh = max(0, st.session_state.refresh_interval - time_since_last_update)
                            st.caption(f"⏱️ Next auto-refresh in {int(time_until_refresh)} seconds")
            
            with refresh_col2:
                if st.button("🔄 Refresh Now", use_container_width=True):
                    with st.spinner("Refreshing..."):
                        portfolio_data = get_portfolio_suggestion(
                            investment_amount,
                            selected_strategies
                        )
                        if portfolio_data:
                            st.session_state.portfolio_data = portfolio_data
                            st.session_state.last_update = datetime.now()
                            st.rerun()
            
            # Auto-refresh logic (only triggers when interval has passed)
            if st.session_state.auto_refresh and st.session_state.portfolio_data and st.session_state.last_update:
                current_time = datetime.now()
                time_since_last_update = (current_time - st.session_state.last_update).total_seconds()
                
                if time_since_last_update >= st.session_state.refresh_interval:
                    # Time to refresh - do it silently in background
                    portfolio_data = get_portfolio_suggestion(
                        investment_amount,
                        selected_strategies
                    )
                    if portfolio_data:
                        st.session_state.portfolio_data = portfolio_data
                        st.session_state.last_update = datetime.now()
                        st.rerun()
        
    else:
        # Welcome message
        st.info("👈 Use the sidebar to configure your investment parameters and generate a portfolio suggestion.")
        
        # Instructions
        with st.expander("ℹ️ How to use"):
            st.markdown("""
            1. **Enter Investment Amount**: Minimum $5,000 USD
            2. **Select Strategies**: Choose 1-2 investment strategies:
               - **Tech**: Technology stocks (AAPL, MSFT, GOOGL, AMZN, META)
               - **Dividend**: Dividend-paying stocks (JNJ, PG, KO, PEP, WMT)
               - **Growth**: Growth stocks (TSLA, NVDA, AMD, NFLX, DIS)
               - **Value**: Value stocks (BRK.B, JPM, V, MA, HD)
            3. **Generate Portfolio**: Click the button to get your portfolio suggestion
            4. **Auto-Refresh**: Enable auto-refresh to see real-time portfolio value updates
            """)


if __name__ == "__main__":
    main()

