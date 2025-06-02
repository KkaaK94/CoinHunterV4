# tests/test_backtest_seed160k.py

import os
import sys
import pandas as pd  # ← 반드시 추가하세요!
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from strategies.seed_160k import Seed160kStrategy
from app_core.analytics.backtester import Backtester


def run_backtest_for_file(filepath):
    try:
        df = pd.read_csv(filepath)
        strategy = Seed160kStrategy()
        bt = Backtester(strategy)
        result_df = bt.run(df)
        print(f"\n📈 종목: {os.path.basename(filepath)}")
        bt.report()
    except Exception as e:
        print(f"❌ 오류 - {filepath}: {e}")

def main():
    data_folder = "data_io/raw_data"
    files = [f for f in os.listdir(data_folder) if f.endswith(".csv") and "macd_fgi" in f]

    print(f"총 테스트 파일 수: {len(files)}")

    for file in files:
        filepath = os.path.join(data_folder, file)
        run_backtest_for_file(filepath)

if __name__ == "__main__":
    main()
