import json
import numpy as np
import pandas as pd
from datetime import datetime
from langgraph.graph import StateGraph, END
from state import FinancialState
from nodes import data_ingestion_node, analysis_node, risk_node, synthesis_node

# --- Helper to make data JSON serializable ---
class FinancialEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return obj.strftime("%Y-%m-%d")
        return super(FinancialEncoder, self).default(obj)

# --- Main Workflow Definition ---
def build_workflow():
    workflow = StateGraph(FinancialState)

    # Add Nodes
    workflow.add_node("data_agent", data_ingestion_node)
    workflow.add_node("analysis_agent", analysis_node)
    workflow.add_node("risk_agent", risk_node)
    workflow.add_node("synthesis_agent", synthesis_node)

    # Define Edges
    workflow.set_entry_point("data_agent")
    workflow.add_edge("data_agent", "analysis_agent")
    workflow.add_edge("analysis_agent", "risk_agent")
    workflow.add_edge("risk_agent", "synthesis_agent")
    workflow.add_edge("synthesis_agent", END)

    return workflow.compile()

# --- Confidence and trade guidance ---

def _resolve_numeric(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def compute_confidence(final_state: dict) -> float:
    tech = final_state.get("technical_indicators", {}) or {}
    risk = final_state.get("risk_metrics", {}) or {}
    rec = str(final_state.get("recommendation", "") or "").lower()

    score = 52.0
    rsi = _resolve_numeric(tech.get("rsi_14"))
    vol = _resolve_numeric(risk.get("volatility"))
    sharpe = _resolve_numeric(risk.get("sharpe_ratio"))
    drawdown = _resolve_numeric(risk.get("current_drawdown"))

    if rec == "buy":
        score += 16
    elif rec == "sell":
        score -= 8

    if 40 <= rsi <= 60:
        score += 12
    elif rsi < 30 or rsi > 70:
        score -= 4

    if sharpe >= 0.7:
        score += 10
    elif sharpe <= 0.0:
        score -= 8

    if vol < 0.25:
        score += 7
    elif vol > 0.40:
        score -= 6

    if drawdown < -0.20:
        score -= 5

    score += min(len(final_state.get("key_drivers", [])), 3) * 2
    return max(0.0, min(100.0, round(score, 1)))


def build_trade_plan(final_state: dict):
    tech = final_state.get("technical_indicators", {}) or {}
    rec = str(final_state.get("recommendation", "HOLD") or "HOLD").upper()
    current_price = _resolve_numeric(tech.get("current_price"))

    if not current_price or current_price <= 0:
        return None, "Current price isn't available."

    if rec == "BUY":
        return round(current_price, 2), "Entry at current price, target +8–12%, stop-loss -3–5%."
    if rec == "SELL":
        return round(current_price, 2), "Exit now or use a tight trailing stop. Avoid deeper losses."
    return round(current_price, 2), "Hold and watch if momentum improves or risk rises."


def build_simple_explanation(final_state: dict):
    rec = str(final_state.get("recommendation", "HOLD") or "HOLD").upper()
    trend = final_state.get("technical_indicators", {}).get("trend", "neutral")
    risk_level = final_state.get("risk_level", "medium")
    return (
        final_state.get("reasoning")
        or f"The stock has {trend} momentum and {risk_level} risk. The model recommends {rec.lower()} based on the latest indicators."
    )

# --- Execution Function ---
def run_financial_analysis(ticker: str):
    print(f"\n🚀 Starting Analysis for: {ticker}")
    print("=" * 50)

    app = build_workflow()
    final_state = app.invoke({"ticker": ticker})

    success = final_state.get("success", True)
    error = final_state.get("error")
    confidence_score = compute_confidence(final_state)
    entry_price, exit_strategy = build_trade_plan(final_state)
    simple_explanation = build_simple_explanation(final_state)

    output_data = {
        "ticker": final_state["ticker"],
        "success": success,
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_range": {
            "start": final_state.get("start_date"),
            "end": final_state.get("end_date")
        },
        "fundamental_metrics": final_state.get("fundamental_metrics") or {},
        "technical_indicators": final_state.get("technical_indicators") or {},
        "risk_metrics": final_state.get("risk_metrics") or {},
        "recommendation": final_state.get("recommendation"),
        "risk_level": final_state.get("risk_level"),
        "confidence_score": confidence_score,
        "entry_price": entry_price,
        "exit_strategy": exit_strategy,
        "simple_explanation": simple_explanation,
        "reasoning": final_state.get("reasoning"),
        "key_drivers": final_state.get("key_drivers") or [],
        "final_report": final_state.get("final_report"),
        "llm_used": final_state.get("llm_used", False)
    }

    if error:
        output_data["error"] = error

    if success:
        print("✅ Analysis Complete!")
    else:
        print(f"⚠️  Analysis completed with errors: {error}")
    print("=" * 50)
    return output_data
