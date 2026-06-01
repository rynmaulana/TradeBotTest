import pandas as pd
import numpy as np

class RiskManager:
    def __init__(self, config=None):
        cfg = config or {}
        self.max_drawdown = cfg.get('max_drawdown', 0.15)
        self.atr_threshold = cfg.get('atr_threshold', 0.05)
        self.initial_balance = None
        self.peak_balance = None

    def update_equity(self, balance):
        if self.initial_balance is None:
            self.initial_balance = balance
            self.peak_balance = balance
        if balance > self.peak_balance:
            self.peak_balance = balance

    def check_drawdown(self, balance):
        if self.peak_balance is None:
            return False
        drawdown = (self.peak_balance - balance) / self.peak_balance
        return drawdown >= self.max_drawdown

    def volatility_filter(self, df):
        if 'atr' not in df.columns:
            # hitung ATR manual jika belum ada
            from pandas_ta import atr
            df['atr'] = atr(df['high'], df['low'], df['close'], length=14)
        last_atr = df['atr'].iloc[-1]
        last_price = df['close'].iloc[-1]
        return (last_atr / last_price) > self.atr_threshold

    def news_filter(self):
        # Implementasi sederhana: selalu False (tidak ada blackout)
        # Bisa ditambahkan scraping ForexFactory
        return False

    def is_trade_allowed(self, balance, df):
        if self.check_drawdown(balance):
            return False, "Max drawdown tercapai"
        if self.volatility_filter(df):
            return False, "Volatilitas terlalu tinggi"
        if self.news_filter():
            return False, "News blackout aktif"
        return True, "OK"