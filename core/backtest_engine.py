import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

import ml_pipeline
import logging

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stock_signal_model.pkl')
SCALER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'feature_scaler.pkl')
FEATURES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'feature_columns.pkl')

_cached_model: Optional[Any] = None
_cached_scaler: Optional[Any] = None
_cached_feature_cols: Optional[List[str]] = None


def load_backtest_assets() -> Tuple[Optional[Any], Optional[Any], Optional[List[str]]]:
    global _cached_model, _cached_scaler, _cached_feature_cols
    if _cached_model is not None and _cached_scaler is not None and _cached_feature_cols is not None:
        return _cached_model, _cached_scaler, _cached_feature_cols

    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH) and os.path.exists(FEATURES_PATH):
        try:
            _cached_model = joblib.load(MODEL_PATH)
            _cached_scaler = joblib.load(SCALER_PATH)
            _cached_feature_cols = joblib.load(FEATURES_PATH)
            logger.info('Loaded backtest model assets')
            return _cached_model, _cached_scaler, _cached_feature_cols
        except Exception as e:
            logger.error(f'Failed to load model assets: {e}')
            return None, None, None

    logger.warning('Backtest model assets not found; falling back to simple trend rule')
    return None, None, None


def _build_signals(data: pd.DataFrame, model: Optional[Any], scaler: Optional[Any], feature_cols: Optional[List[str]]) -> np.ndarray:
    if model is not None and scaler is not None and feature_cols is not None:
        features = data[feature_cols].fillna(0)
        try:
            transformed = scaler.transform(features)
            return model.predict(transformed)
        except Exception as e:
            logger.error(f'Backtest model prediction failed: {e}')

    # Fallback: simple momentum rule using 20-day moving average
    signals = np.zeros(len(data), dtype=int)
    if 'Close' in data.columns:
        sma20 = data['Close'].rolling(20).mean().fillna(method='bfill')
        signals = (data['Close'] > sma20).astype(int).to_numpy()
    return signals


def _annualized_return(total_return: float, trading_days: int) -> float:
    if trading_days <= 0:
        return 0.0
    years = trading_days / 252.0
    if years <= 0:
        return 0.0
    return (1 + total_return) ** (1 / years) - 1


def _compute_drawdown(equity_values: np.ndarray) -> float:
    peaks = np.maximum.accumulate(equity_values)
    drawdowns = (equity_values - peaks) / peaks
    return float(np.min(drawdowns)) if len(drawdowns) else 0.0


def _compute_sharpe(returns: np.ndarray) -> float:
    if len(returns) < 2:
        return 0.0
    mean = np.mean(returns)
    std = np.std(returns, ddof=1)
    if std == 0:
        return 0.0
    return float((mean / std) * np.sqrt(252))


def run_backtest(symbol: str,
                 start_date: str,
                 end_date: str,
                 initial_equity: float = 10000.0,
                 position_size_pct: float = 0.02) -> Dict[str, Any]:
    symbol = symbol.upper().strip()
    if not symbol:
        raise ValueError('Ticker symbol is required')

    if not start_date:
        start_date = '2019-01-01'
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')

    df = ml_pipeline.download_stock_data(symbol, start_date=start_date, end_date=end_date)
    if df is None or df.empty:
        raise ValueError(f'No historical data available for {symbol}')

    df = ml_pipeline.compute_features(df)
    model, scaler, feature_cols = load_backtest_assets()
    signals = _build_signals(df, model, scaler, feature_cols)

    cash = initial_equity
    shares = 0
    entry_price = 0.0
    trades: List[Dict[str, Any]] = []
    equity_curve: List[Dict[str, Any]] = []

    dates = df.index.to_list()
    closes = df['Close'].to_numpy(dtype=float)
    opens = df['Open'].to_numpy(dtype=float)
    equity = float(cash)

    for i in range(len(df) - 1):
        current_date = dates[i]
        current_close = closes[i]
        signal = int(signals[i])

        if shares > 0:
            equity = cash + shares * current_close
        else:
            equity = cash

        equity_curve.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'equity': round(equity, 2)
        })

        if shares == 0 and signal == 1:
            next_open = float(opens[i + 1])
            if next_open > 0:
                shares = int((cash * position_size_pct) / next_open)
                if shares > 0:
                    entry_price = next_open
                    entry_date = dates[i + 1].strftime('%Y-%m-%d')
                    cash -= shares * entry_price
                    trades.append({
                        'ticker': symbol,
                        'entry_date': entry_date,
                        'entry_price': round(entry_price, 2),
                        'shares': shares,
                        'exit_date': None,
                        'exit_price': None,
                        'pnl': None,
                        'return_pct': None
                    })

        if shares > 0 and signal == 0:
            next_open = float(opens[i + 1])
            if next_open > 0:
                exit_price = next_open
                cash += shares * exit_price
                pnl = shares * (exit_price - entry_price)
                trade = trades[-1]
                trade.update({
                    'exit_date': dates[i + 1].strftime('%Y-%m-%d'),
                    'exit_price': round(exit_price, 2),
                    'pnl': round(pnl, 2),
                    'return_pct': round((pnl / (entry_price * shares)) * 100, 2) if entry_price else None
                })
                shares = 0
                entry_price = 0.0

    # Final mark-to-market / exit any open position on last close
    final_date = dates[-1]
    final_close = closes[-1]
    if shares > 0:
        equity = cash + shares * final_close
        exit_price = final_close
        cash += shares * exit_price
        pnl = shares * (exit_price - entry_price)
        trade = trades[-1]
        trade.update({
            'exit_date': final_date.strftime('%Y-%m-%d'),
            'exit_price': round(exit_price, 2),
            'pnl': round(pnl, 2),
            'return_pct': round((pnl / (entry_price * shares)) * 100, 2) if entry_price else None
        })
        shares = 0
        entry_price = 0.0

    final_equity = float(cash)
    equity_curve.append({
        'date': final_date.strftime('%Y-%m-%d'),
        'equity': round(final_equity, 2)
    })

    equity_values = np.array([point['equity'] for point in equity_curve], dtype=float)
    daily_returns = np.diff(equity_values) / equity_values[:-1] if len(equity_values) > 1 else np.array([])
    total_return = (final_equity - initial_equity) / initial_equity
    annual_return = _annualized_return(total_return, len(equity_values))
    sharpe = _compute_sharpe(daily_returns)
    max_drawdown = _compute_drawdown(equity_values)

    wins = [t for t in trades if t.get('pnl') is not None and t['pnl'] > 0]
    losses = [t for t in trades if t.get('pnl') is not None and t['pnl'] <= 0]

    return {
        'symbol': symbol,
        'start_date': start_date,
        'end_date': end_date,
        'initial_equity': initial_equity,
        'final_equity': round(final_equity, 2),
        'total_return_pct': round(total_return * 100, 2),
        'annual_return_pct': round(annual_return * 100, 2),
        'sharpe_ratio': round(sharpe, 2),
        'max_drawdown_pct': round(max_drawdown * 100, 2),
        'win_rate_pct': round((len(wins) / len(trades)) * 100, 2) if trades else 0.0,
        'trade_count': len(trades),
        'winning_trades': len(wins),
        'losing_trades': len(losses),
        'equity_curve': equity_curve,
        'trades': trades,
        'strategy': 'model' if model is not None else 'momentum_fallback',
        'signal_count': int(np.sum(signals))
    }
