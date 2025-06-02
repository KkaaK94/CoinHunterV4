# app_core/analytics/backtester.py

import pandas as pd

class Backtester:
    def __init__(self, strategy, initial_capital=160_000):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.trades = []
        self.equity_curve = []

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.strategy.generate_signals(df)
        capital = self.initial_capital
        position = 0
        entry_price = 0

        for i in range(len(df)):
            row = df.iloc[i]

            if row['buy'] and position == 0:
                entry_price = row['close']
                position = self.strategy.position_size / entry_price
                self.trades.append({'type': 'BUY', 'price': entry_price, 'index': i})
                capital -= self.strategy.position_size

            elif row['sell'] and position > 0:
                exit_price = row['close']
                pnl = (exit_price - entry_price) * position
                capital += self.strategy.position_size + pnl
                self.trades.append({'type': 'SELL', 'price': exit_price, 'index': i, 'pnl': pnl})
                position = 0

            self.equity_curve.append(capital + (position * row['close'] if position else 0))

        df['equity'] = self.equity_curve
        return df

    def report(self):
        df = pd.DataFrame(self.trades)
        if df.empty:
            print("No trades executed.")
            return

        total_trades = len(df) // 2
        pnls = [t['pnl'] for t in self.trades if t['type'] == 'SELL']
        total_profit = sum(pnls)
        win_count = sum([1 for p in pnls if p > 0])
        win_rate = win_count / len(pnls) if pnls else 0
        max_drawdown = self._calculate_mdd()

        print(f"📊 전략명: {self.strategy.name()}")
        print(f"총 거래 횟수: {total_trades}")
        print(f"누적 수익: {total_profit:,.0f} 원")
        print(f"승률: {win_rate * 100:.2f}%")
        print(f"최대 낙폭(MDD): {max_drawdown:.2f}%")

    def _calculate_mdd(self):
        peak = -float('inf')
        mdd = 0
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > mdd:
                mdd = dd
        return mdd * 100
