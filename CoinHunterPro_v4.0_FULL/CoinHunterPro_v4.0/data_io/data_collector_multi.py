import pyupbit
import pandas as pd
import os
import time
from fear_and_greed import FearAndGreedIndex

# 수집 대상 종목 목록
TICKERS = [
    "KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL",
    "KRW-ARB", "KRW-AVAX", "KRW-DOGE", "KRW-SAND"
]

def fetch_upbit_data(ticker, interval="day", count=200):
    df = pyupbit.get_ohlcv(ticker=ticker, interval=interval, count=count)
    df.reset_index(inplace=True)
    df.rename(columns={"index": "date"}, inplace=True)
    return df

def calculate_macd(df, short_period=12, long_period=26, signal_period=9):
    df['ema_short'] = df['close'].ewm(span=short_period, adjust=False).mean()
    df['ema_long'] = df['close'].ewm(span=long_period, adjust=False).mean()
    df['macd'] = df['ema_short'] - df['ema_long']
    df['signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean()
    return df

def fetch_fgi_data(days=200):
    fng = FearAndGreedIndex()
    fgi_data = fng.get_last_n_days(days)
    fgi_df = pd.DataFrame(fgi_data)
    fgi_df['timestamp'] = pd.to_datetime(fgi_df['timestamp'], unit='s')
    fgi_df.rename(columns={'timestamp': 'date', 'value': 'fgi'}, inplace=True)
    fgi_df['fgi'] = pd.to_numeric(fgi_df['fgi'])
    return fgi_df[['date', 'fgi']]

def merge_data(price_df, fgi_df):
    merged = pd.merge(price_df, fgi_df, on='date', how='left')
    merged['fgi'].fillna(method='ffill', inplace=True)
    return merged

def main():
    os.makedirs("data_io/raw_data", exist_ok=True)
    fgi_df = fetch_fgi_data()

    for ticker in TICKERS:
        print(f"Fetching {ticker} ...")
        try:
            price_df = fetch_upbit_data(ticker)
            price_df = calculate_macd(price_df)
            final_df = merge_data(price_df, fgi_df)
            filename = f"data_io/raw_data/{ticker.replace('-', '_')}_macd_fgi.csv"
            final_df.to_csv(filename, index=False)
            print(f"Saved to {filename}")
        except Exception as e:
            print(f"Error on {ticker}: {e}")
        time.sleep(1.1)  # API rate limit 대응

if __name__ == "__main__":
    main()
