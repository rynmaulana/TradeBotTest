from mirofish_sklearn import MiroFishPredictor

class AIEngine:
    def __init__(self, use_deepseek=False, use_sentiment=False):
        self.mirofish = MiroFishPredictor()
        # Tempat untuk DeepSeek / Sentiment bisa ditambahkan nanti
        self.deepseek = None
        self.sentiment = None

    def train_mirofish(self, df):
        self.mirofish.train(df)

    def get_ai_signal(self, df, symbol=None):
        proba = self.mirofish.predict(df)
        return self.mirofish.get_signal(proba, threshold=0.55)