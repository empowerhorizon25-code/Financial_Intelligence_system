<<<<<<< HEAD
# Financial Intelligence System

A multi-agent financial analysis system that provides real-time stock analysis and trading recommendations for NYSE-listed stocks. The system uses LangGraph to orchestrate a pipeline of specialized agents that perform data ingestion, technical analysis, risk assessment, and AI-powered synthesis.

## Features

- **Data Ingestion**: Fetches 5 years of historical stock data using yfinance
- **Technical Analysis**: Calculates RSI (Relative Strength Index) and MACD (Moving Average Convergence Divergence) indicators
- **Fundamental Analysis**: Retrieves key metrics including P/E ratio, market cap, and sector information
- **Risk Assessment**: Computes volatility, Sharpe ratio, maximum drawdown, and current drawdown
- **AI-Powered Recommendations**: Uses Google Gemini AI to synthesize analysis and generate BUY/SELL/HOLD recommendations with detailed reasoning

## Prerequisites

- Python 3.8 or higher
- Google Gemini API key (for AI synthesis)

## Installation

1. Clone the repository:
```bash
cd financial_intellligence_system
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root directory:
```bash
# .env
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

**Note**: You can obtain a Google Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

## How to Run

### Command-Line Interface (CLI)

Run the analysis for any NYSE ticker symbol:

```bash
python test.py
```

When prompted, enter a ticker symbol (e.g., `AMZN`, `GOOG`, `TSLA`, `AAPL`, `ORCL`, `MSFT`, `NVDA`).

The system will:
1. Fetch historical data for the ticker
2. Perform technical and fundamental analysis
3. Calculate risk metrics
4. Generate an AI-powered recommendation with reasoning (using Gemini if available, otherwise offline analytics)

**Note**: If you enter an invalid ticker, the system will display a friendly error message instead of crashing.

### API/UI Server

Start the FastAPI server with UI:

```bash
python -m uvicorn financial_intellligence_system.ui_server:app --reload --port 8000
```

The server will be available at:
- **Web UI**: `http://127.0.0.1:8000`
- **API Endpoint**: `http://127.0.0.1:8000/api/analyze`
- **API Documentation**: 
  - Swagger UI: `http://127.0.0.1:8000/api/docs`
  - ReDoc: `http://127.0.0.1:8000/api/redoc`

**Important**: Make sure you have a `.env` file in the project root with:
```
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

The system will work without the API key (using offline analytics), but Gemini AI recommendations require a valid key.

### Troubleshooting: Import Issues

If you encounter import errors or "module not found" issues, it may be due to stale Python bytecode. Clean the cache:

```bash
python tools/clean_cache.py
```

This removes all `__pycache__` folders and `.pyc` files recursively from the project.

#### API Endpoint

**POST** `/analyze`

Analyzes a stock ticker and returns comprehensive financial analysis.

**Request Body:**
```json
{
  "ticker": "AAPL"
}
```

**Response (200 OK):**
```json
{
  "ticker": "AAPL",
  "success": true,
  "llm_used": true,
  "analysis_date": "2024-01-15 14:30:00",
  "data_range": {
    "start": "2019-01-15",
    "end": "2024-01-15"
  },
  "fundamental_metrics": {
    "market_cap": 3000000000000,
    "pe_ratio": 28.5,
    "forward_pe": 25.2,
    "sector": "Technology"
  },
  "technical_indicators": {
    "current_price": 185.50,
    "rsi_14": 65.3,
    "macd_line": 2.15,
    "signal_line": 1.89,
    "trend": "Bullish"
  },
  "risk_metrics": {
    "max_drawdown": -0.25,
    "current_drawdown": -0.02,
    "volatility": 0.18,
    "sharpe_ratio": 1.45
  },
  "recommendation": "BUY",
  "risk_level": "Medium",
  "reasoning": "Strong technical indicators with bullish MACD trend and reasonable valuation...",
  "key_drivers": [
    "Bullish MACD trend",
    "RSI of 65.3 indicating healthy momentum",
    "Current drawdown of -2% showing recent recovery",
    "Sharpe ratio of 1.45 indicating good risk-adjusted returns"
  ],
  "final_report": "Full detailed report text..."
}
```

**Note**: The `llm_used` field indicates whether Gemini AI was used (`true`) or if the system fell back to offline analytics (`false`). The system gracefully falls back to analytics-based recommendations if the Gemini API is unavailable.

**Error Responses:**

- **400 Bad Request**: Invalid or empty ticker symbol
  ```json
  {
    "detail": "Ticker symbol cannot be empty"
  }
  ```

- **404 Not Found**: No data found for the ticker
  ```json
  {
    "detail": "No data found for ticker 'INVALID'"
  }
  ```

- **500 Internal Server Error**: Server-side error during analysis
  ```json
  {
    "detail": "Error message"
  }
  ```

#### Example API Usage

Using `curl`:
```bash
curl -X POST "http://127.0.0.1:8000/api/analyze" \
     -H "Content-Type: application/json" \
     -d '{"ticker": "AAPL"}'
```

Using Python `requests`:
```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/api/analyze",
    json={"ticker": "AAPL"}
)
result = response.json()
print(result["recommendation"])
```

## System Features

### Robust Error Handling

- **Invalid Tickers**: The system gracefully handles invalid ticker symbols and returns clear error messages instead of crashing.
- **Missing Data**: If yfinance returns no data, the system sets `success=false` and provides an error message.
- **Gemini API Failures**: If the Gemini API is unavailable (404, auth error, network error), the system automatically falls back to offline analytics-based recommendations using the same decision framework.

### LLM Fallback

The system uses Google Gemini AI (`gemini-2.0-flash` with fallback to `gemini-1.5-pro`) when available, but works completely offline using computed analytics if:
- `GOOGLE_API_KEY` is not set in `.env`
- The Gemini API returns errors
- Network connectivity issues occur

The `llm_used` field in the response indicates whether AI was used or offline analytics were applied.
=======
# Financial_Intelligence_system
>>>>>>> adcd1558683cd89cac00b11579ab839d86744ee9
