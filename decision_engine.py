class DecisionEngine:
    def __init__(self, weights=None):
        self.weights = weights or {'ta': 0.4, 'onchain': 0.2, 'ai': 0.4}

    def decide(self, ta_signal, onchain_signal, ai_signal):
        """
        Masing-masing sinyal bernilai -1, 0, atau 1
        """
        weighted = (ta_signal * self.weights['ta'] +
                    onchain_signal * self.weights['onchain'] +
                    ai_signal * self.weights['ai'])
        if weighted > 0.15:
            return 'LONG'
        elif weighted < -0.15:
            return 'SHORT'
        return 'NONE'