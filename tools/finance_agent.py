"""
Finance Agent tools for Code Forge AI.
Fetches genuine market data for Indian (NSE/BSE) and Global (US/International) markets.
Supports live quotes, multi-period candlestick charts, indices, company profiles,
financial news, stock comparisons, and AI market explanations with disclaimers.
"""

from typing import List, Dict, Any, Optional
import json
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from tools.base import BaseTool, ToolResult

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


# Canonical market index mappings
MARKET_INDICES = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANK NIFTY": "^NSEBANK",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DOW JONES": "^DJI"
}

POPULAR_STOCKS = {
    "Indian Market (NSE)": [
        ("RELIANCE.NS", "Reliance Industries"),
        ("TCS.NS", "Tata Consultancy Services"),
        ("HDFCBANK.NS", "HDFC Bank"),
        ("INFY.NS", "Infosys"),
        ("ICICIBANK.NS", "ICICI Bank"),
        ("TATAMOTORS.NS", "Tata Motors")
    ],
    "International Market (US)": [
        ("NVDA", "NVIDIA Corp."),
        ("AAPL", "Apple Inc."),
        ("MSFT", "Microsoft Corp."),
        ("GOOGL", "Alphabet (Google)"),
        ("AMZN", "Amazon.com"),
        ("TSLA", "Tesla Inc.")
    ]
}


class GetStockQuoteTool(BaseTool):
    """Fetches genuine market quotes and key metrics for any stock, ETF, crypto, or index."""
    name = "get_stock_quote"
    description = (
        "Fetches current live/latest market quote for any ticker symbol "
        "(e.g., 'AAPL', 'NVDA', 'RELIANCE.NS', '^NSEI', '^GSPC', 'BTC-USD'). "
        "Returns price, change, day high/low, volume, 52-week range, and market cap."
    )
    agent_name = "Finance Agent"
    parameters = {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "Stock symbol or index (e.g. 'NVDA', 'RELIANCE.NS', '^NSEI', 'TSLA')"
            }
        },
        "required": ["symbol"]
    }

    def execute(self, symbol: str, **kwargs) -> ToolResult:
        symbol = symbol.strip().upper()
        # Handle friendly names
        if symbol in MARKET_INDICES:
            symbol = MARKET_INDICES[symbol]

        data = {}

        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(symbol)
                info = getattr(ticker, "fast_info", None)

                price = getattr(info, "last_price", None) if info else None
                prev_close = getattr(info, "previous_close", None) if info else None
                open_price = getattr(info, "open", None) if info else None
                day_high = getattr(info, "day_high", None) if info else None
                day_low = getattr(info, "day_low", None) if info else None
                fifty_two_high = getattr(info, "year_high", None) if info else None
                fifty_two_low = getattr(info, "year_low", None) if info else None
                market_cap = getattr(info, "market_cap", None) if info else None
                currency = getattr(info, "currency", "USD") if info else "USD"

                # Fallback to history if fast_info missing last_price
                if price is None:
                    hist = ticker.history(period="2d")
                    if not hist.empty:
                        price = float(hist["Close"].iloc[-1])
                        if len(hist) > 1:
                            prev_close = float(hist["Close"].iloc[-2])
                        open_price = float(hist["Open"].iloc[-1])
                        day_high = float(hist["High"].iloc[-1])
                        day_low = float(hist["Low"].iloc[-1])

                change = (price - prev_close) if (price and prev_close) else 0.0
                change_pct = (change / prev_close * 100) if prev_close else 0.0

                data = {
                    "symbol": symbol,
                    "price": price,
                    "change": change,
                    "change_pct": change_pct,
                    "currency": currency,
                    "open": open_price,
                    "day_high": day_high,
                    "day_low": day_low,
                    "year_high": fifty_two_high,
                    "year_low": fifty_two_low,
                    "market_cap": market_cap
                }
            except Exception:
                pass

        # Fallback to direct Yahoo Finance chart API endpoint via requests
        if not data.get("price"):
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
                resp = requests.get(url, headers=headers, timeout=8)
                if resp.status_code == 200:
                    json_data = resp.json()
                    meta = json_data["chart"]["result"][0]["meta"]
                    price = meta.get("regularMarketPrice")
                    prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")
                    change = (price - prev_close) if (price and prev_close) else 0.0
                    change_pct = (change / prev_close * 100) if prev_close else 0.0
                    data = {
                        "symbol": symbol,
                        "price": price,
                        "change": change,
                        "change_pct": change_pct,
                        "currency": meta.get("currency", "USD"),
                        "day_high": meta.get("regularMarketDayHigh"),
                        "day_low": meta.get("regularMarketDayLow"),
                        "year_high": meta.get("fiftyTwoWeekHigh"),
                        "year_low": meta.get("fiftyTwoWeekLow")
                    }
            except Exception:
                pass

        if not data.get("price"):
            return ToolResult(
                success=False,
                output=f"Could not retrieve live quote for ticker '{symbol}'. Please check the symbol.",
                error=f"Symbol '{symbol}' not found",
                agent_name=self.agent_name
            )

        price = data.get("price", 0.0)
        chg = data.get("change", 0.0)
        chg_pct = data.get("change_pct", 0.0)
        sign = "+" if chg >= 0 else ""
        cur = data.get("currency", "USD")

        cap_str = "N/A"
        if data.get("market_cap"):
            cap = data["market_cap"]
            if cap >= 1e12:
                cap_str = f"{cap / 1e12:.2f}T {cur}"
            elif cap >= 1e9:
                cap_str = f"{cap / 1e9:.2f}B {cur}"
            elif cap >= 1e6:
                cap_str = f"{cap / 1e6:.2f}M {cur}"

        summary = (
            f"📈 Market Quote for {symbol} ({cur}):\n"
            f"• Current Price: {price:,.2f} {sign}{chg:,.2f} ({sign}{chg_pct:.2f}%)\n"
            f"• Day Range: {data.get('day_low', 0) or 0:,.2f} - {data.get('day_high', 0) or 0:,.2f}\n"
            f"• 52-Week Range: {data.get('year_low', 0) or 0:,.2f} - {data.get('year_high', 0) or 0:,.2f}\n"
            f"• Market Cap: {cap_str}\n"
            f"• Notice: Genuine market data provided via Yahoo Finance."
        )

        return ToolResult(
            success=True,
            output=summary,
            data=data,
            agent_name=self.agent_name
        )


class GetHistoricalDataTool(BaseTool):
    """Fetches historical price series and indicators across 1D, 1W, 1M, 3M, 6M, 1Y, 5Y."""
    name = "get_historical_data"
    description = (
        "Fetches historical OHLCV data for a ticker over periods (1d, 5d, 1mo, 3mo, 6mo, 1y, 5y). "
        "Computes statistics and provides data for Plotly charting."
    )
    agent_name = "Finance Agent"
    parameters = {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "Stock symbol (e.g. 'NVDA', 'RELIANCE.NS', '^NSEI')"
            },
            "period": {
                "type": "string",
                "description": "Timeframe: '1d', '5d', '1mo', '3mo', '6mo', '1y', '5y'",
                "default": "1mo"
            }
        },
        "required": ["symbol"]
    }

    def execute(self, symbol: str, period: str = "1mo", **kwargs) -> ToolResult:
        symbol = symbol.strip().upper()
        if symbol in MARKET_INDICES:
            symbol = MARKET_INDICES[symbol]

        interval_map = {
            "1d": "5m",
            "5d": "15m",
            "1mo": "1d",
            "3mo": "1d",
            "6mo": "1d",
            "1y": "1wk",
            "5y": "1wk"
        }
        interval = interval_map.get(period.lower(), "1d")

        df = None
        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval)
            except Exception:
                pass

        if df is None or df.empty:
            # Fallback with daily interval
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period)
            except Exception:
                pass

        if df is None or df.empty:
            return ToolResult(
                success=False,
                output=f"Historical data for '{symbol}' with period '{period}' is currently unavailable.",
                error="Historical data unavailable",
                agent_name=self.agent_name
            )

        df["Return"] = df["Close"].pct_change()
        total_return = ((df["Close"].iloc[-1] / df["Close"].iloc[0]) - 1) * 100
        min_price = float(df["Low"].min())
        max_price = float(df["High"].max())
        latest_price = float(df["Close"].iloc[-1])
        volatility = float(df["Return"].std() * np.sqrt(252) * 100) if len(df) > 5 else 0.0

        summary = (
            f"Historical Analysis for {symbol} ({period.upper()} timeframe):\n"
            f"• Period Return: {total_return:+.2f}%\n"
            f"• Period High: ${max_price:,.2f} | Period Low: ${min_price:,.2f}\n"
            f"• Latest Close: ${latest_price:,.2f}\n"
            f"• Annualized Volatility: {volatility:.2f}%\n"
            f"• Total Candlesticks: {len(df)}"
        )

        return ToolResult(
            success=True,
            output=summary,
            data={
                "symbol": symbol,
                "df": df,
                "period": period,
                "total_return": total_return,
                "latest_price": latest_price
            },
            agent_name=self.agent_name
        )


class GetCompanyOverviewTool(BaseTool):
    """Fetches fundamental profile, valuation ratios, sector, and analyst targets."""
    name = "get_company_overview"
    description = "Provides company business summary, sector, industry, P/E ratio, profit margins, and analyst targets."
    agent_name = "Finance Agent"
    parameters = {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "Stock ticker (e.g. 'MSFT', 'TCS.NS', 'AAPL')"
            }
        },
        "required": ["symbol"]
    }

    def execute(self, symbol: str, **kwargs) -> ToolResult:
        symbol = symbol.strip().upper()
        if not YFINANCE_AVAILABLE:
            return ToolResult(success=False, output="yfinance is not available.", agent_name=self.agent_name)

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}

            name = info.get("longName") or info.get("shortName") or symbol
            sector = info.get("sector", "N/A")
            industry = info.get("industry", "N/A")
            summary = info.get("longBusinessSummary", "No description available.")
            if len(summary) > 400:
                summary = summary[:400] + "..."

            trailing_pe = info.get("trailingPE", "N/A")
            forward_pe = info.get("forwardPE", "N/A")
            peg = info.get("pegRatio", "N/A")
            profit_margins = info.get("profitMargins")
            margin_str = f"{profit_margins * 100:.1f}%" if profit_margins is not None else "N/A"
            target_price = info.get("targetMeanPrice", "N/A")

            res_text = (
                f"🏢 Company Profile: {name} ({symbol})\n"
                f"• Sector: {sector} | Industry: {industry}\n"
                f"• Valuation: Trailing P/E: {trailing_pe} | Forward P/E: {forward_pe} | PEG: {peg}\n"
                f"• Profit Margin: {margin_str}\n"
                f"• Analyst Target Mean: ${target_price if target_price != 'N/A' else 'N/A'}\n\n"
                f"Business Summary:\n{summary}"
            )

            return ToolResult(
                success=True,
                output=res_text,
                data=info,
                agent_name=self.agent_name
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Error retrieving company overview for {symbol}: {str(e)}",
                error=str(e),
                agent_name=self.agent_name
            )


class CompareTickersTool(BaseTool):
    """Compares key performance metrics and valuation across multiple stocks."""
    name = "compare_tickers"
    description = "Compares multiple stock tickers (e.g., ['NVDA', 'AMD', 'INTC'] or ['TCS.NS', 'INFY.NS'])."
    agent_name = "Finance Agent"
    parameters = {
        "type": "object",
        "properties": {
            "symbols": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of ticker symbols to compare"
            }
        },
        "required": ["symbols"]
    }

    def execute(self, symbols: List[str], **kwargs) -> ToolResult:
        if not symbols:
            return ToolResult(success=False, output="No symbols provided for comparison.", agent_name=self.agent_name)

        rows = []
        quote_tool = GetStockQuoteTool()

        for s in symbols[:6]:
            sym = s.strip().upper()
            res = quote_tool.execute(symbol=sym)
            if res.success and res.data:
                d = res.data
                rows.append({
                    "Symbol": sym,
                    "Price": f"${d.get('price', 0):,.2f}",
                    "Day Change": f"{d.get('change_pct', 0):+.2f}%",
                    "52W High": f"${d.get('year_high', 0) or 0:,.2f}",
                    "52W Low": f"${d.get('year_low', 0) or 0:,.2f}"
                })

        if not rows:
            return ToolResult(success=False, output="Unable to retrieve data for the requested tickers.", agent_name=self.agent_name)

        df_compare = pd.DataFrame(rows)
        return ToolResult(
            success=True,
            output=f"📊 Stock Comparison Table:\n\n{df_compare.to_markdown(index=False)}",
            data=df_compare,
            agent_name=self.agent_name
        )


def fetch_market_indices_snapshot() -> List[Dict[str, Any]]:
    """Fetches real-time price & change for Indian and Global market indices."""
    results = []
    quote_tool = GetStockQuoteTool()
    for name, sym in MARKET_INDICES.items():
        res = quote_tool.execute(symbol=sym)
        if res.success and res.data:
            d = res.data
            results.append({
                "name": name,
                "symbol": sym,
                "price": d.get("price", 0),
                "change": d.get("change", 0),
                "change_pct": d.get("change_pct", 0),
                "currency": d.get("currency", "USD")
            })
    return results


def fetch_stock_news(symbol: str) -> List[Dict[str, str]]:
    """Fetches genuine recent financial news related to the given ticker."""
    news_items = []
    if YFINANCE_AVAILABLE:
        try:
            ticker = yf.Ticker(symbol.strip().upper())
            raw_news = getattr(ticker, "news", []) or []
            for item in raw_news[:5]:
                title = item.get("title") or item.get("headline", "")
                link = item.get("link") or item.get("url", "")
                publisher = item.get("publisher") or item.get("source", "Financial News")
                if title:
                    news_items.append({
                        "title": title,
                        "link": link,
                        "publisher": publisher
                    })
        except Exception:
            pass
    return news_items


def explain_stock_movement(symbol: str) -> str:
    """Provides technical AI movement context with required financial disclaimer."""
    q_tool = GetStockQuoteTool()
    h_tool = GetHistoricalDataTool()

    q_res = q_tool.execute(symbol=symbol)
    h_res = h_tool.execute(symbol=symbol, period="1mo")

    if not q_res.success:
        return f"Unable to analyze {symbol} at this moment."

    d = q_res.data
    price = d.get("price", 0)
    chg_pct = d.get("change_pct", 0)
    trend = "bullish momentum" if chg_pct > 0 else "bearish consolidation"

    analysis = (
        f"### 🤖 AI Technical Movement Analysis for **{symbol}**\n\n"
        f"• **Current Market Status**: Trading at **${price:,.2f}** ({chg_pct:+.2f}% today).\n"
        f"• **Technical Sentiment**: Short-term indicators signal **{trend}**.\n"
        f"• **52-Week Context**: The stock is currently trading at {((price - d.get('year_low', price)) / (d.get('year_high', price) - d.get('year_low', 1) or 1) * 100):.1f}% of its 52-week range (${d.get('year_low', 0):,.2f} - ${d.get('year_high', 0):,.2f}).\n\n"
        f"> ⚠️ **Important Disclaimer**: This analysis is generated for informational and educational purposes only. "
        f"It does not constitute financial, investment, or trading advice. Always conduct independent research before making investment decisions."
    )
    return analysis


def build_plotly_candlestick(df: pd.DataFrame, symbol: str, is_dark: bool = True) -> go.Figure:
    """Builds an interactive candlestick + volume chart matching the dashboard theme."""
    bg_color = "#0e131b" if is_dark else "#ffffff"
    text_color = "#e2e8f0" if is_dark else "#1e293b"
    grid_color = "rgba(255, 255, 255, 0.06)" if is_dark else "rgba(0, 0, 0, 0.06)"

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.75, 0.25],
        subplot_titles=(f"{symbol.upper()} Price Action", "Volume")
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="OHLC",
            increasing_line_color="#00e676",
            decreasing_line_color="#ff5252"
        ),
        row=1, col=1
    )

    # 20 SMA
    if len(df) >= 20:
        sma = df["Close"].rolling(20).mean()
        fig.add_trace(
            go.Scatter(x=df.index, y=sma, line=dict(color="#00e5ff", width=1.8), name="SMA 20"),
            row=1, col=1
        )

    # Volume
    colors = ['#00e676' if c >= o else '#ff5252' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(
        go.Bar(x=df.index, y=df["Volume"], marker_color=colors, name="Volume", opacity=0.6),
        row=2, col=1
    )

    fig.update_layout(
        template="plotly_dark" if is_dark else "plotly_white",
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font=dict(color=text_color),
        xaxis_rangeslider_visible=False,
        height=480,
        margin=dict(l=30, r=30, t=35, b=25),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_xaxes(showgrid=True, gridcolor=grid_color)
    fig.update_yaxes(showgrid=True, gridcolor=grid_color)
    return fig


class FinanceAgent:
    """High-level autonomous finance agent interface."""
    def __init__(self):
        self.quote_tool = GetStockQuoteTool()
        self.history_tool = GetHistoricalDataTool()
        self.overview_tool = GetCompanyOverviewTool()
        self.compare_tool = CompareTickersTool()

    def get_tools(self) -> List[BaseTool]:
        return [self.quote_tool, self.history_tool, self.overview_tool, self.compare_tool]
