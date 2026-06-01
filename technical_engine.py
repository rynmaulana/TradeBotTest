import pandas as pd
import pandas_ta as ta

class TechnicalEngine:
    def __init__(self, config=None):
        cfg = config or {}
        self.ema_fast = cfg.get('ema_fast', 12)
        self.ema_slow = cfg.get('ema_slow', 26)
        self.macd_fast = cfg.get('macd_fast', 12)
        self.macd_slow = cfg.get('macd_slow', 26)
        self.macd_signal = cfg.get('macd_signal', 9)
        self.rsi_period = cfg.get('rsi_period', 14)
        self.rsi_oversold = cfg.get('rsi_oversold', 30)
        self.rsi_overbought = cfg.get('rsi_overbought', 70)

    def analyze(self, df: pd.DataFrame) -> dict:
        df = df.copy()
        df['ema_fast'] = ta.ema(df['close'], length=self.ema_fast)
        df['ema_slow'] = ta.ema(df['close'], length=self.ema_slow)
        macd = ta.macd(df['close'], fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal)
        df = pd.concat([df, macd], axis=1)
        df['rsi'] = ta.rsi(df['close'], length=self.rsi_period)
        df['hh'] = (df['high'] > df['high'].shift(1)) & (df['high'].shift(1) > df['high'].shift(2))
        df['ll'] = (df['low'] < df['low'].shift(1)) & (df['low'].shift(1) < df['low'].shift(2))

        latest = df.iloc[-1]
        signals = {}

        # EMA
        signals['ema'] = 1 if latest['ema_fast'] > latest['ema_slow'] else -1

        # MACD (histogram > 0 atau signal line crossover)
        macd_line = latest['MACD_12_26_9']
        macd_signal_line = latest['MACDs_12_26_9']
        signals['macd'] = 1 if macd_line > macd_signal_line else -1

        # RSI
        rsi = latest['rsi']
        if rsi < self.rsi_oversold:
            signals['rsi'] = 1
        elif rsi > self.rsi_overbought:
            signals['rsi'] = -1
        else:
            signals['rsi'] = 0

        # Market Structure
        structure = 0
        if latest['hh']:
            structure = 1
        elif latest['ll']:
            structure = -1
        signals['structure'] = structure

        # Agregasi bobot: EMA(2), MACD(2), RSI(1), Structure(2)
        total = (signals['ema'] * 2 + signals['macd'] * 2 +
                 signals['rsi'] * 1 + structure * 2)
        signals['aggregate'] = 1 if total > 2 else (-1 if total < -2 else 0)
        return signals