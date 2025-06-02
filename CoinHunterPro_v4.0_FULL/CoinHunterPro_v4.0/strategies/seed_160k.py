# strategies/seed_160k.py

import pandas as pd

class Seed160kStrategy:
    def __init__(self, capital=160_000):
        self.capital = capital
        self.position_size = capital * 0.08
        self.stop_loss_pct = 0.05
        self.take_profit_pct = 0.15

    def name(self):
        return "seed_160k_macd_fgi"

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        print("[DEBUG] Seed160kStrategy 실행 시작")
        df = df.copy()
        df['buy'] = False
        df['sell'] = False
        in_position = False
        entry_price = 0.0

        for i in range(1, len(df)):
            macd_now = df.loc[i, 'macd']
            signal_now = df.loc[i, 'signal']
            macd_prev = df.loc[i - 1, 'macd']
            signal_prev = df.loc[i - 1, 'signal']
            fgi = df.loc[i, 'fgi']
            price = df.loc[i, 'close']

            if not in_position and macd_now > signal_now and macd_prev <= signal_prev and fgi < 25:
                df.loc[i, 'buy'] = True
                entry_price = price
                in_position = True

            elif in_position:
                if price <= entry_price * (1 - self.stop_loss_pct):
                    df.loc[i, 'sell'] = True
                    in_position = False
                elif price >= entry_price * (1 + self.take_profit_pct):
                    df.loc[i, 'sell'] = True
                    in_position = False

        return df
