import yfinance as yf
import pandas as pd
from datetime import datetime
from state import FinancialState
import numpy as np
import os
import joblib

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List

from dotenv import load_dotenv
load_dotenv()

def data_ingestion_node(state: FinancialState):
    """
    Agent 1: Data Ingestion
    Fetches 5 years of historical data using yfinance.
    """
    ticker = state["ticker"]
    print(f"--- [Agent 1] Fetching data for {ticker}... ---")
    
    # Fetch 5 years of history
    # We use 'auto_adjust=True' to handle stock splits/dividends automatically
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5y", auto_adjust=True)
        
        # Basic validation
        if hist.empty or hist is None:
            error_msg = f"No data found for ticker '{ticker}'. Please verify the ticker symbol is correct."
            print(f"--- [Agent 1] ⚠️  {error_msg} ---")
            return {
                "historical_data": None,
                "error": error_msg,
                "success": False
            }
        
        # Store dates for reference
        start_date = hist.index.min().strftime('%Y-%m-%d')
        end_date = hist.index.max().strftime('%Y-%m-%d')
        
        print(f"--- [Agent 1] Success! Retrieved {len(hist)} rows from {start_date} to {end_date} ---")
        
        # Return the update to the state
        return {
            "historical_data": hist,
            "start_date": start_date,
            "end_date": end_date,
            "success": True
        }
    except Exception as e:
        error_msg = f"Error fetching data for ticker '{ticker}': {str(e)}"
        print(f"--- [Agent 1] ⚠️  {error_msg} ---")
        return {
            "historical_data": None,
            "error": error_msg,
            "success": False
        }


def analysis_node(state: FinancialState):
    """
    Agent 2: Technical & Fundamental Analysis
    Calculates RSI, MACD, and fetches basic fundamentals (P/E, Market Cap).
    """
    ticker = state["ticker"]
    
    # Check for errors from data ingestion
    if state.get("error") or state.get("historical_data") is None:
        error_msg = state.get("error", "No historical data available")
        print(f"--- [Agent 2] ⚠️  Skipping analysis due to error: {error_msg} ---")
        return {
            "fundamental_metrics": {},
            "technical_indicators": {},
            "error": error_msg,
            "success": False
        }
    
    data = state["historical_data"]
    print(f"--- [Agent 2] Analyzing {ticker}... ---")

    # 1. Fundamental Analysis (Basic)
    stock = yf.Ticker(ticker)
    info = stock.info
    
    # diverse keys often appear in yfinance info; we use .get() for safety
    fundamentals = {
        "market_cap": info.get("marketCap", "N/A"),
        "pe_ratio": info.get("trailingPE", "N/A"),
        "forward_pe": info.get("forwardPE", "N/A"),
        "sector": info.get("sector", "Unknown")
    }
    
    # 2. Technical Analysis (Manual Calculation)
    # We work on a copy to avoid SettingWithCopy warnings
    df = data.copy()
    
    # --- RSI (Relative Strength Index) Calculation ---
    # Formula: 100 - (100 / (1 + RS))
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    
    # --- MACD (Moving Average Convergence Divergence) ---
    # Formula: 12-day EMA - 26-day EMA
    ema_12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema_26 = df["Close"].ewm(span=26, adjust=False).mean()
    
    df["MACD_Line"] = ema_12 - ema_26
    df["Signal_Line"] = df["MACD_Line"].ewm(span=9, adjust=False).mean()
    
    # Get the most recent values
    latest = df.iloc[-1]
    
    technicals = {
        "current_price": latest["Close"],
        "rsi_14": round(latest["RSI"], 2),
        "macd_line": round(latest["MACD_Line"], 2),
        "signal_line": round(latest["Signal_Line"], 2),
        "trend": "Bullish" if latest["MACD_Line"] > latest["Signal_Line"] else "Bearish"
    }

    print(f"--- [Agent 2] Analysis Complete. RSI: {technicals['rsi_14']} | Trend: {technicals['trend']} ---")

    return {
        "fundamental_metrics": fundamentals,
        "technical_indicators": technicals
    }

def risk_node(state: FinancialState):
    """
    Agent 3: Risk Management
    Calculates Volatility, Max Drawdown, Sharpe Ratio, AND Current Drawdown.
    """
    ticker = state["ticker"]
    
    # Check for errors from previous nodes
    if state.get("error") or state.get("historical_data") is None:
        error_msg = state.get("error", "No historical data available")
        print(f"--- [Agent 3] ⚠️  Skipping risk analysis due to error: {error_msg} ---")
        return {
            "risk_metrics": {},
            "error": error_msg,
            "success": False
        }
    
    data = state["historical_data"]
    print(f"--- [Agent 3] Assessing Risk for {ticker}... ---")
    
    # Calculate Daily Returns
    df = data.copy()
    df["Returns"] = df["Close"].pct_change().dropna()
    
    # 1. Max Drawdown (Historical - 5 Years)
    cumulative_returns = (1 + df["Returns"]).cumprod()
    running_max = cumulative_returns.cummax()
    drawdown = (cumulative_returns - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # 2. Current Drawdown (Right Now)
    # The last value in the drawdown series is the current drawdown
    current_drawdown = drawdown.iloc[-1]
    
    # 3. Sharpe Ratio
    risk_free_rate = 0.04
    mean_return = df["Returns"].mean() * 252
    std_dev = df["Returns"].std() * (252 ** 0.5)
    
    sharpe_ratio = (mean_return - risk_free_rate) / std_dev if std_dev != 0 else 0
    
    risk_metrics = {
        "max_drawdown": round(max_drawdown, 4),      # Historical worst case
        "current_drawdown": round(current_drawdown, 4), # Relevant for today's decision
        "volatility": round(std_dev, 4),
        "sharpe_ratio": round(sharpe_ratio, 2)
    }
    
    print(f"--- [Agent 3] Risk Analysis Complete. Curr DD: {risk_metrics['current_drawdown']:.2%} | Max DD: {risk_metrics['max_drawdown']:.2%} ---")
    
    return {"risk_metrics": risk_metrics}


class FinancialReport(BaseModel):
    recommendation: str = Field(description="The final trading recommendation: 'BUY', 'SELL', or 'HOLD'")
    reasoning: str = Field(description="A concise explanation (under 100 words) justifying the recommendation")
    key_drivers: list[str] = Field(description="A list of 3-5 specific data points that influenced the decision (e.g. 'High RSI', 'Low Sharpe Ratio')")
    risk_level: str = Field(description="The assessed risk level: 'Low', 'Medium', 'High', or 'Extreme'")

# --- Offline Fallback Report Generator ---
def generate_offline_summary(state: FinancialState) -> dict:
    """
    Generates a structured executive summary based solely on computed analytics
    when Gemini API is unavailable. Uses the same decision framework as the AI prompt.
    
    Returns the same schema as Gemini-generated reports for UI compatibility.
    """
    ticker = state.get("ticker", "UNKNOWN")
    fundamentals = state.get("fundamental_metrics", {})
    technicals = state.get("technical_indicators", {})
    risk_metrics = state.get("risk_metrics", {})
    
    # Extract key metrics with safe defaults
    trend = technicals.get("trend", "Unknown")
    rsi = technicals.get("rsi_14", 50.0)
    current_price = technicals.get("current_price", 0)
    pe_ratio = fundamentals.get("pe_ratio", "N/A")
    
    current_drawdown = risk_metrics.get("current_drawdown", 0.0)
    volatility = risk_metrics.get("volatility", 0.0)
    sharpe_ratio = risk_metrics.get("sharpe_ratio", 0.0)
    max_drawdown = risk_metrics.get("max_drawdown", 0.0)
    
    # Convert P/E to numeric if possible
    pe_numeric = None
    if pe_ratio != "N/A" and isinstance(pe_ratio, (int, float)):
        pe_numeric = float(pe_ratio)
    
    # Decision Framework (matching the AI prompt logic)
    recommendation = "HOLD"
    risk_level = "Medium"
    
    # Determine recommendation based on analytics
    is_bullish = trend.lower() == "bullish"
    rsi_ok = isinstance(rsi, (int, float)) and rsi < 70
    rsi_oversold = isinstance(rsi, (int, float)) and rsi < 30
    rsi_overbought = isinstance(rsi, (int, float)) and rsi > 70
    
    sharpe_positive = isinstance(sharpe_ratio, (int, float)) and sharpe_ratio >= 0.5
    drawdown_severe = isinstance(current_drawdown, (int, float)) and current_drawdown < -0.15
    pe_reasonable = pe_numeric is None or pe_numeric < 30
    
    # BUY: Strong technicals (Bullish trend, RSI < 70) AND reasonable valuation OR strong growth momentum
    if is_bullish and rsi_ok and (pe_reasonable or sharpe_positive):
        recommendation = "BUY"
    # SELL: Weak technicals (Bearish trend) AND (High P/E OR High Current Drawdown)
    elif not is_bullish and (not pe_reasonable or drawdown_severe):
        recommendation = "SELL"
    # HOLD: Default for conflicting signals
    
    # Risk Level Assessment
    if isinstance(volatility, (int, float)) and volatility >= 0.35:
        risk_level = "High"
    elif isinstance(current_drawdown, (int, float)) and current_drawdown < -0.30:
        risk_level = "Extreme"
    elif isinstance(volatility, (int, float)) and volatility < 0.20 and isinstance(sharpe_ratio, (int, float)) and sharpe_ratio >= 0.7:
        risk_level = "Low"
    elif isinstance(volatility, (int, float)) and volatility < 0.25:
        risk_level = "Medium"
    else:
        risk_level = "Medium"
    
    # Build reasoning
    reasoning_parts = []
    reasoning_parts.append(f"Technical analysis shows a {trend.lower()} trend with RSI at {rsi:.2f}.")
    
    if pe_numeric is not None:
        reasoning_parts.append(f"P/E ratio of {pe_numeric:.2f} indicates {'reasonable' if pe_reasonable else 'elevated'} valuation.")
    else:
        reasoning_parts.append("Valuation metrics are not available.")
    
    if isinstance(volatility, (int, float)):
        reasoning_parts.append(f"Volatility is {volatility:.2%} with a Sharpe ratio of {sharpe_ratio:.2f}.")
    
    if isinstance(current_drawdown, (int, float)):
        reasoning_parts.append(f"Current drawdown is {current_drawdown:.2%}.")
    
    reasoning = " ".join(reasoning_parts)
    
    # Key Drivers
    key_drivers = []
    key_drivers.append(f"Trend signal: {trend}")
    key_drivers.append(f"RSI (14): {rsi:.2f}")
    if pe_numeric is not None:
        key_drivers.append(f"P/E ratio: {pe_numeric:.2f}")
    if isinstance(sharpe_ratio, (int, float)):
        key_drivers.append(f"Sharpe ratio: {sharpe_ratio:.2f}")
    if isinstance(volatility, (int, float)):
        key_drivers.append(f"Volatility: {volatility:.2%}")
    if isinstance(current_drawdown, (int, float)):
        key_drivers.append(f"Current drawdown: {current_drawdown:.2%}")
    
    # Build final report (same format as Gemini output)
    final_report = (
        f"**Recommendation:** {recommendation}\n"
        f"**Risk Level:** {risk_level}\n\n"
        f"**Reasoning:**\n{reasoning}\n\n"
        f"**Key Drivers:**\n- " + "\n- ".join(key_drivers)
    )
    
    return {
        "recommendation": recommendation,
        "risk_level": risk_level,
        "reasoning": reasoning,
        "key_drivers": key_drivers,
        "final_report": final_report,
        "llm_used": False  # Offline summary, LLM not used
    }


# --- The Synthesis Node ---
def synthesis_node(state: FinancialState):
    """
    Agent 4: Insight Synthesis
    Uses Gemini to aggregate all data and generate a structured JSON report.
    Falls back to offline analytics-based summary if Gemini API fails.
    """
    ticker = state.get("ticker", "UNKNOWN")
    
    # Check for errors from previous nodes
    if state.get("error") or state.get("historical_data") is None:
        error_msg = state.get("error", "No historical data available")
        print(f"--- [Agent 4] ⚠️  Cannot generate report due to error: {error_msg} ---")
        
        # Return error response with same schema structure
        return {
            "recommendation": "ERROR",
            "risk_level": "Unknown",
            "reasoning": f"Analysis could not be completed: {error_msg}",
            "key_drivers": [error_msg],
            "final_report": f"**Error:** {error_msg}\n\nAnalysis could not be completed for ticker '{ticker}'. Please verify the ticker symbol is correct and try again.",
            "error": error_msg,
            "success": False
        }
    
    print(f"--- [Agent 4] Synthesizing Report... ---")
    
    # 1. Get API key from environment
    google_api_key = os.getenv("GOOGLE_API_KEY")
    llm_used = False
    
    # 2. Initialize Gemini with fallback model support
    # Try gemini-2.0-flash first, fallback to gemini-1.5-pro if needed
    model_name = "gemini-2.0-flash"
    fallback_model = "gemini-1.5-pro"
    llm = None
    
    # 2. Setup the Parser
    parser = PydanticOutputParser(pydantic_object=FinancialReport)
    
    # 3. Prepare the Prompt with Format Instructions
    template = """You are a Senior Investment Strategist at a top-tier hedge fund.
    
    ### DATA INPUTS:
    1. Fundamental Data:
    {fundamentals}
    
    2. Technical Indicators:
    {technicals}
    
    3. Risk Metrics:
    {risk}
    
    ### DECISION FRAMEWORK:
    - **BUY**: Strong technicals (Bullish trend, RSI < 70) AND reasonable valuation OR strong growth momentum.
    - **HOLD**: Conflicting signals (e.g., Good technicals but High P/E).
    - **SELL**: Weak technicals (Bearish trend) AND (High P/E OR High Current Drawdown).
    
    ### IMPORTANT RISK CONTEXT:
    - "Max Drawdown" is historical (5-year window). Do not penalize a stock solely for a crash that happened years ago (e.g., 2022) if it has since recovered.
    - Focus on "Current Drawdown" and "Volatility" for immediate risk.
    - A high P/E ratio is acceptable for high-growth tech stocks if momentum is strong.
    
    ### OUTPUT FORMAT INSTRUCTIONS:
    You must strictly output a single valid JSON object. Do not include Markdown formatting. 
    Follow this exact schema:
    
    {{
        "recommendation": "BUY, SELL, or HOLD",
        "risk_level": "Low, Medium, High, or Extreme",
        "reasoning": "A concise explanation (under 100 words). Focus on the balance between current momentum and valuation.",
        "key_drivers": [
            "List 3-5 specific data points",
            "e.g. 'Current Drawdown of -5%'",
            "e.g. 'RSI of 65'"
        ]
    }}
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # 4. Format the input
    messages = prompt.format_messages(
        ticker=state["ticker"],
        fundamentals=state["fundamental_metrics"],
        technicals=state["technical_indicators"],
        risk=state["risk_metrics"],
        format_instructions=parser.get_format_instructions()
    )
    
    # 5. Try Gemini API with model fallback and graceful error handling
    # Check if API key is available
    if not google_api_key:
        print(f"--- [Agent 4] ⚠️  GOOGLE_API_KEY not found in environment. Using offline analytics-based summary. ---")
        offline_result = generate_offline_summary(state)
        offline_result["llm_used"] = False
        return offline_result
    
    try:
        # Try primary model first
        try:
            llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=google_api_key)
            response = llm.invoke(messages)
            llm_used = True
            print(f"--- [Agent 4] Using model: {model_name} ---")
        except Exception as model_error:
            # Fallback to secondary model if primary fails
            error_str = str(model_error).lower()
            if "404" in error_str or "not found" in error_str or "v1beta" in error_str or "gemini-1.5-flash" in error_str:
                print(f"--- [Agent 4] Primary model {model_name} not available, trying fallback: {fallback_model} ---")
                try:
                    llm = ChatGoogleGenerativeAI(model=fallback_model, google_api_key=google_api_key)
                    response = llm.invoke(messages)
                    llm_used = True
                    print(f"--- [Agent 4] Using fallback model: {fallback_model} ---")
                except Exception as fallback_error:
                    # Both models failed, switch to offline mode
                    print(f"--- [Agent 4] ⚠️  Gemini API unavailable (both models failed). Switching to offline analytics-based summary. ---")
                    print(f"--- [Agent 4] Error details: {str(fallback_error)} ---")
                    offline_result = generate_offline_summary(state)
                    offline_result["llm_used"] = False
                    return offline_result
            else:
                # Non-404 error, try fallback anyway
                print(f"--- [Agent 4] Primary model error, trying fallback: {fallback_model} ---")
                try:
                    llm = ChatGoogleGenerativeAI(model=fallback_model, google_api_key=google_api_key)
                    response = llm.invoke(messages)
                    llm_used = True
                    print(f"--- [Agent 4] Using fallback model: {fallback_model} ---")
                except Exception as fallback_error:
                    print(f"--- [Agent 4] ⚠️  Gemini API unavailable. Switching to offline analytics-based summary. ---")
                    print(f"--- [Agent 4] Error details: {str(fallback_error)} ---")
                    offline_result = generate_offline_summary(state)
                    offline_result["llm_used"] = False
                    return offline_result
        
        # Parse the response
        parsed_report = parser.parse(response.content)
        
        # Convert back to dict for state storage
        report_dict = parsed_report.dict()
        
        final_report = (
            f"**Recommendation:** {report_dict['recommendation']}\n"
            f"**Risk Level:** {report_dict['risk_level']}\n\n"
            f"**Reasoning:**\n{report_dict['reasoning']}\n\n"
            f"**Key Drivers:**\n- " + "\n- ".join(report_dict['key_drivers'])
        )

        print(f"--- [Agent 4] Structured Report Generated via Gemini! ---")
        
        report_dict["final_report"] = final_report
        report_dict["llm_used"] = True

        return report_dict

    except Exception as e:
        # Catch-all for parsing errors, network errors, auth errors, etc.
        error_str = str(e).lower()
        print(f"--- [Agent 4] ⚠️  Gemini API call failed. Switching to offline analytics-based summary. ---")
        print(f"--- [Agent 4] Error type: {type(e).__name__}, Details: {str(e)} ---")
        
        # Return offline summary that matches the same schema
        offline_result = generate_offline_summary(state)
        offline_result["llm_used"] = False
        return offline_result
