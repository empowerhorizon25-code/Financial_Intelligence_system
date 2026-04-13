import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, classification_report
from sklearn.ensemble import RandomForestClassifier
import joblib
import warnings
warnings.filterwarnings('ignore')

def download_stock_data(ticker, start_date='2020-01-01', end_date='2024-01-01'):
    """Download historical data for a ticker."""
    data = yf.download(ticker, start=start_date, end=end_date)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
    data = data.dropna()
    return data

def compute_features(data):
    """Compute technical indicators and features."""
    data = data.copy()

    # Basic price features
    data['returns'] = data['Close'].pct_change()
    data['log_returns'] = np.log(data['Close'] / data['Close'].shift(1))
    data['volume_change'] = data['Volume'].pct_change()

    # Moving averages
    data['price_ma_10'] = data['Close'].rolling(10).mean()
    data['price_ma_20'] = data['Close'].rolling(20).mean()
    data['price_ma_50'] = data['Close'].rolling(50).mean()
    data['volume_ma_20'] = data['Volume'].rolling(20).mean()

    # Volatility
    data['volatility_20'] = data['returns'].rolling(20).std()

    # RSI calculation (simplified)
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['rsi'] = 100 - (100 / (1 + rs))

    # MACD (simplified)
    ema12 = data['Close'].ewm(span=12).mean()
    ema26 = data['Close'].ewm(span=26).mean()
    data['macd'] = ema12 - ema26
    data['macd_signal'] = data['macd'].ewm(span=9).mean()
    data['macd_diff'] = data['macd'] - data['macd_signal']

    # Bollinger Bands
    sma20 = data['Close'].rolling(20).mean()
    std20 = data['Close'].rolling(20).std()
    data['bb_middle'] = sma20
    data['bb_high'] = sma20 + (std20 * 2)
    data['bb_low'] = sma20 - (std20 * 2)

    # Fill NaN values with 0 for features, but keep Close intact
    feature_cols = ['returns', 'log_returns', 'volume_change', 'volatility_20', 'volume_ma_20',
                    'price_ma_10', 'price_ma_20', 'price_ma_50', 'rsi', 'macd', 'macd_signal',
                    'macd_diff', 'bb_high', 'bb_low', 'bb_middle']
    data[feature_cols] = data[feature_cols].fillna(0)

    return data

def create_labels(data, look_forward_days=5, up_threshold=0.05, down_threshold=-0.03):
    """Create target labels."""
    labels = []
    for i in range(len(data) - look_forward_days):
        current_price = float(data.iloc[i]['Close'])
        future_price = float(data.iloc[i + look_forward_days]['Close'])
        if np.isnan(current_price) or np.isnan(future_price) or current_price <= 0 or future_price <= 0:
            labels.append(np.nan)
            continue
        pct_change = (future_price - current_price) / current_price
        if pct_change >= up_threshold:
            labels.append(1)
        else:
            labels.append(0)
    # Pad with np.nan for the last look_forward_days
    labels.extend([np.nan] * look_forward_days)
    return labels

def create_dataset(tickers, start_date='2020-01-01', end_date='2024-01-01'):
    """Create dataset for multiple tickers."""
    all_data = []
    for ticker in tickers:
        try:
            data = download_stock_data(ticker, start_date, end_date)
            data = compute_features(data)
            data['ticker'] = ticker
            # Create labels for this ticker
            data['target'] = create_labels(data)
            # Drop only rows with NaN target
            data = data.dropna(subset=['target'])
            data = data.reset_index(drop=True)
            all_data.append(data)
            print(f"Downloaded and processed {ticker}")
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    if all_data:
        combined_data = pd.concat(all_data, ignore_index=True)
        return combined_data
    else:
        return pd.DataFrame()

def train_model():
    """Train the ML model."""
    # Create dataset
    tickers = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'GOOGL', 'AMZN', 'META']
    dataset = create_dataset(tickers, start_date='2022-01-01', end_date='2023-01-01')

    if dataset.empty:
        print("No data available")
        return

    print(f"Dataset shape: {dataset.shape}")
    print(f"Positive labels: {dataset['target'].sum()}")
    print(f"Class balance: {dataset['target'].value_counts(normalize=True)}")

    # Feature columns
    feature_cols = [
        'returns', 'log_returns', 'volume_change', 'volatility_20', 'volume_ma_20',
        'price_ma_10', 'price_ma_20', 'price_ma_50', 'rsi', 'macd', 'macd_signal',
        'macd_diff', 'bb_high', 'bb_low', 'bb_middle'
    ]

    # Prepare data
    X = dataset[feature_cols]
    y = dataset['target']
    X = X.fillna(0)

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train/test split
    train_size = int(0.7 * len(X_scaled))
    X_train = X_scaled[:train_size]
    X_test = X_scaled[train_size:]
    y_train = y[:train_size]
    y_test = y[train_size:]

    # Train RandomForest
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight='balanced'
    )

    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    print("Test Results:")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.3f}")
    print(f"Precision: {precision_score(y_test, y_pred):.3f}")
    print(f"Recall: {recall_score(y_test, y_pred):.3f}")

    # Save model
    joblib.dump(model, 'stock_signal_model.pkl')
    joblib.dump(scaler, 'feature_scaler.pkl')
    joblib.dump(feature_cols, 'feature_columns.pkl')

    print("Model saved successfully!")
    return model, scaler, feature_cols

if __name__ == "__main__":
    train_model()