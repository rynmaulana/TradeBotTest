import requests

class OnChainEngine:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://open-api.coinglass.com/public/v2"

    def _get(self, endpoint, params=None):
        headers = {}
        if self.api_key:
            headers['coinglassSecret'] = self.api_key
        try:
            resp = requests.get(f"{self.base_url}{endpoint}", headers=headers, params=params, timeout=5)
            if resp.status_code == 200:
                return resp.json().get('data', [])
        except:
            pass
        return None

    def whale_movement_signal(self, symbol='BTC'):
        data = self._get("/whale_transaction", {'symbol': symbol})
        if data:
            # contoh: lebih dari 2 transaksi besar (>100 BTC) dalam 1 jam terakhir → bullish
            recent_big = [t for t in data if float(t.get('amount', 0)) > 100]
            return 1 if len(recent_big) > 2 else 0
        return 0

    def funding_rate_signal(self, symbol='BTCUSDT'):
        data = self._get("/funding_rate", {'symbol': symbol})
        if data and len(data) > 0:
            rate = float(data[-1].get('fundingRate', 0))
            if rate < -0.001:
                return 1   # funding negatif besar → potensi short squeeze
            elif rate > 0.001:
                return -1  # funding positif besar → potensi koreksi
        return 0

    def open_interest_signal(self, symbol='BTCUSDT'):
        data = self._get("/open_interest", {'symbol': symbol})
        if data and len(data) >= 2:
            current_oi = data[-1].get('openInterest', 0)
            prev_oi = data[-2].get('openInterest', 0)
            # (penyederhanaan) OI naik → minat meningkat → ikuti tren
            change = (current_oi - prev_oi) / prev_oi if prev_oi else 0
            if change > 0.05:
                return 1
            elif change < -0.05:
                return -1
        return 0

    def aggregate(self):
        if not self.api_key:
            return 0  # fallback jika tidak ada API key
        whale = self.whale_movement_signal()
        funding = self.funding_rate_signal()
        oi = self.open_interest_signal()
        total = whale * 2 + funding * 2 + oi * 1
        if total > 1:
            return 1
        elif total < -1:
            return -1
        return 0