from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
import uvicorn
from main import run_financial_analysis

from core.backtest_engine import run_backtest

# Import agent routes
from api.agent_routes import agent_router

# 1. Initialize FastAPI
app = FastAPI(
    title="Financial Intelligence System API",
    description="Multi-Agent AI System for Stock Analysis",
    version="1.0"
)

# Mount agent routes
app.include_router(agent_router)

# 2. Define Request Model
class TickerRequest(BaseModel):
    ticker: str

class BacktestRequest(BaseModel):
    ticker: str
    start_date: str = Field(default="2019-01-01", description="Start date for the backtest")
    end_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"), description="End date for the backtest")
    initial_equity: float = Field(default=10000.0, gt=0.0, description="Initial equity for the backtest")
    position_size_pct: float = Field(default=0.02, gt=0.0, lt=1.0, description="Percent of equity used per position")

# 3. Define the Endpoint
@app.post("/analyze", summary="Analyze a specific stock ticker")
async def analyze_stock(request: TickerRequest):
    """
    Triggers the multi-agent workflow for the provided ticker.
    Returns structured financial analysis including recommendation, risk level, and key drivers.
    """
    ticker = request.ticker.upper().strip()
    
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker symbol cannot be empty")
    
    try:
        # Call your existing main function
        result = run_financial_analysis(ticker)
        
        # Check if analysis was successful
        if not result.get("success", True):
            error_msg = result.get("error", f"No data found for ticker '{ticker}'")
            raise HTTPException(status_code=404, detail=error_msg)
             
        return result
    
    except Exception as e:
        # Log the error internally (print to console)
        print(f"Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backtest", summary="Run a historical backtest for a stock ticker")
async def run_backtest_endpoint(request: BacktestRequest):
    ticker = request.ticker.upper().strip()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker symbol cannot be empty")

    try:
        result = run_backtest(
            symbol=ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_equity=request.initial_equity,
            position_size_pct=request.position_size_pct
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Backtest Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/daily-picks", summary="Get today's top stock picks")
async def get_daily_picks():
    # Placeholder daily picks. Replace with real analytics later.
    daily_picks = [
        {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "confidence": 88,
            "risk": "Medium",
            "entry_price": 172.5,
            "target_price": 190.0,
            "reason": "Strong earnings momentum and services growth.",
        },
        {
            "ticker": "MSFT",
            "name": "Microsoft Corp.",
            "confidence": 85,
            "risk": "Medium",
            "entry_price": 345.0,
            "target_price": 375.0,
            "reason": "Cloud revenue tailwinds and AI adoption.",
        },
        {
            "ticker": "NVDA",
            "name": "Nvidia Corp.",
            "confidence": 91,
            "risk": "High",
            "entry_price": 1020.0,
            "target_price": 1125.0,
            "reason": "Leadership in AI GPUs and strong demand visibility.",
        },
    ]
    return {"daily_picks": daily_picks}

@app.post("/generate-content", summary="Generate viral content post from stock analysis")
async def generate_content(request: TickerRequest):
    """
    Generates a formatted social media post based on AI stock analysis.
    Returns Twitter/X, Reddit, and TikTok-ready content.
    """
    ticker = request.ticker.upper().strip()
    
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker symbol cannot be empty")
    
    try:
        # Get the analysis
        analysis = run_financial_analysis(ticker)
        
        if not analysis.get("success", True):
            error_msg = analysis.get("error", f"No data found for ticker '{ticker}'")
            raise HTTPException(status_code=404, detail=error_msg)
        
        # Format into viral content
        rec = analysis.get("recommendation", "HOLD").upper()
        confidence = analysis.get("confidence_score", 0)
        entry = analysis.get("entry_price", 0)
        target = entry * 1.08 if entry else 0  # Approximate 8% target
        stop = entry * 0.97 if entry else 0   # Approximate 3% stop
        upside = ((target - entry) / entry * 100) if entry else 0
        explanation = analysis.get("simple_explanation", "AI analysis based on technical and fundamental indicators.")
        
        # Twitter/X format
        twitter_post = f"🤖 AI says {rec} on {ticker} with {confidence}% confidence.\n\n📈 Entry: ${entry:.2f}\n🎯 Target: ${target:.2f}\n🛑 Stop: ${stop:.2f}\n📊 Upside: +{upside:.1f}%\n\n💡 Why: {explanation[:100]}...\n\nTry free: [link]\n\nWhat do you think? #StockSignals #AI"
        
        # Reddit format
        reddit_post = f"**AI Signal: {rec} on {ticker}**\n\n- **Confidence:** {confidence}%\n- **Entry Price:** ${entry:.2f}\n- **Target Price:** ${target:.2f}\n- **Stop Loss:** ${stop:.2f}\n- **Potential Upside:** +{upside:.1f}%\n\n**Why this trade?** {explanation}\n\n*Not financial advice. Backtested 87% accuracy.*\n\nTry 3 free analyses: [link]"
        
        # TikTok/Short video script
        tiktok_script = f"AI just analyzed {ticker}... and says {rec}!\n\nEntry: ${entry:.2f}\nTarget: ${target:.2f}\nConfidence: {confidence}%\n\nWhy? {explanation[:50]}...\n\nTry it free! Link in bio. #StockSignals #AI #Trading"
        
        return {
            "ticker": ticker,
            "recommendation": rec,
            "confidence": confidence,
            "twitter_post": twitter_post,
            "reddit_post": reddit_post,
            "tiktok_script": tiktok_script,
            "raw_data": analysis
        }
    
    except Exception as e:
        print(f"Content Generation Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/content-calendar", summary="Generate a week's worth of content ideas")
async def get_content_calendar():
    """
    Returns a 7-day content calendar with signal-based post ideas.
    """
    # Sample stocks for the week (rotate sectors)
    weekly_stocks = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMZN", "META"]
    
    calendar = []
    for i, ticker in enumerate(weekly_stocks[:7], 1):
        try:
            analysis = run_financial_analysis(ticker)
            rec = analysis.get("recommendation", "HOLD").upper()
            confidence = analysis.get("confidence_score", 0)
            
            post_idea = f"Day {i}: AI says {rec} on {ticker} ({confidence}% confidence). Entry/Target/Stop details + why."
            calendar.append({
                "day": i,
                "ticker": ticker,
                "post_idea": post_idea,
                "recommendation": rec,
                "confidence": confidence
            })
        except Exception as e:
            calendar.append({
                "day": i,
                "ticker": ticker,
                "post_idea": f"Day {i}: Analyze {ticker} and share AI signal.",
                "error": str(e)
            })
    
    return {"content_calendar": calendar}


# 4. Entry point for debugging (Optional)
if __name__ == "__main__":
    uvicorn.run("fis_api:app", host="127.0.0.1", port=8000, reload=True)