import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

class MiroFishPredictor:
    def __init__(self, lookback=10):
        self.lookback = lookback
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)

    def prepare_data(self, df, feature_cols=['close', 'high', 'low', 'volume']):
        df = df[feature_cols].dropna()
        X, y = [], []
        for i in range(self.lookback, len(df)-1):
            X.append(df.iloc[i-self.lookback:i].values.flatten())
            y.append(1 if df['close'].iloc[i+1] > df['close'].iloc[i] else 0)
        return np.array(X), np.array(y)

    def train(self, df):
        X, y = self.prepare_data(df)
        if len(X) < 20:
            return
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)

    def predict(self, df):
        if not hasattr(self.model, 'classes_'):
            return None
        feature_cols = ['close', 'high', 'low', 'volume']
        X = df[feature_cols].dropna().iloc[-self.lookback:].values.flatten().reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        proba = self.model.predict_proba(X_scaled)[0][1]
        return float(proba)

    def get_signal(self, proba, threshold=0.55):
        if proba is None:
            return 0
        if proba >= threshold:
            return 1
        elif proba <= (1 - threshold):
            return -1
        return 0