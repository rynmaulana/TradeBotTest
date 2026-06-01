import os
import time
import logging
import ccxt
import pandas as pd
from dotenv import load_dotenv

from technical_engine import TechnicalEngine
from onchain_engine import OnChainEngine
from ai_engine import AIEngine
from risk_manager import RiskManager
from decision_engine import DecisionEngine

load_dotenv()

# -------------------------------------------------------------------
# Setup Logging
# -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Konfigurasi
# -------------------------------------------------------------------
SYMBOL = 'BTC/USDT'
TIMEFRAME = '5m'
LEVERAGE = 2
DRY_RUN = True  # False untuk eksekusi real di testnet

# -------------------------------------------------------------------
# Koneksi Exchange (Testnet)
# -------------------------------------------------------------------
exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_SECRET_KEY'),
    'enableRateLimit': True,
    'options': {'defaultType': 'future'},
})
exchange.set_sandbox_mode(True)
try:
    exchange.set_leverage(LEVERAGE, SYMBOL)
except Exception as e:
    logger.warning(f"Gagal set leverage: {e}")

# -------------------------------------------------------------------
# Inisialisasi Modul
# -------------------------------------------------------------------
tech_engine = TechnicalEngine({
    'ema_fast': 12,
    'ema_slow': 26,
    'rsi_oversold': 30,
    'rsi_overbought': 70,
})

# Jika tidak ada Coinglass API key, onchain_signal selalu 0
onchain_api_key = os.getenv('COINGLASS_API_KEY')
onchain_engine = OnChainEngine(onchain_api_key)

ai_engine = AIEngine()  # Hanya MiroFish

risk_manager = RiskManager({
    'max_drawdown': 0.15,
    'atr_threshold': 0.05,
})

decision_engine = DecisionEngine({
    'ta': 0.4,
    'onchain': 0.2,
    'ai': 0.4,
})

# -------------------------------------------------------------------
# Fungsi Ambil Data
# -------------------------------------------------------------------
def fetch_ohlcv(symbol, timeframe, limit=200):
    raw = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(raw, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

# -------------------------------------------------------------------
# Training Awal AI
# -------------------------------------------------------------------
logger.info("Mengambil data historis untuk training MiroFish...")
df_hist = fetch_ohlcv(SYMBOL, TIMEFRAME, limit=500)
ai_engine.train_mirofish(df_hist)
logger.info("MiroFish siap.")

# -------------------------------------------------------------------
# Loop Utama
# -------------------------------------------------------------------
last_side = None
logger.info("Bot dimulai (Testnet, Dry Run = %s)", DRY_RUN)

while True:
    try:
        df = fetch_ohlcv(SYMBOL, TIMEFRAME, limit=200)

        # 1. Sinyal Teknikal
        ta_result = tech_engine.analyze(df)
        ta_signal = ta_result['aggregate']
        logger.info(f"TA: {ta_signal}")

        # 2. Sinyal On-Chain
        try:
            onchain_signal = onchain_engine.aggregate()
        except Exception as e:
            logger.warning(f"On-chain error: {e}")
            onchain_signal = 0
        logger.info(f"OnChain: {onchain_signal}")

        # 3. Sinyal AI
        ai_signal = ai_engine.get_ai_signal(df, SYMBOL)
        logger.info(f"AI: {ai_signal}")

        # 4. Keputusan
        decision = decision_engine.decide(ta_signal, onchain_signal, ai_signal)
        logger.info(f"Decision: {decision}")

        # 5. Risk Management
        balance = exchange.fetch_balance()['total']['USDT']
        risk_manager.update_equity(balance)
        allowed, reason = risk_manager.is_trade_allowed(balance, df)
        if not allowed:
            logger.warning(f"Risk block: {reason}")
            decision = 'NONE'

        # 6. Eksekusi (jika sinyal berubah)
        if decision != 'NONE' and decision != last_side:
            # Tutup posisi sebelumnya
            positions = exchange.fetch_positions([SYMBOL])
            for pos in positions:
                if pos['symbol'] == SYMBOL and abs(pos['contracts']) > 0:
                    side_close = 'sell' if pos['side'] == 'long' else 'buy'
                    logger.info(f"Menutup posisi {pos['side']}...")
                    exchange.create_order(
                        SYMBOL, 'market', side_close,
                        abs(pos['contracts']),
                        {'reduceOnly': True}
                    )

            # Buka posisi baru
            side = 'buy' if decision == 'LONG' else 'sell'
            amount = 0.001  # kecil untuk test
            if not DRY_RUN:
                order = exchange.create_order(SYMBOL, 'market', side, amount)
                logger.info(f"Order {side} ditempatkan: {order['id']}")
            else:
                logger.info(f"DRY RUN: {side} {amount} {SYMBOL}")

            last_side = decision

        time.sleep(15)

    except KeyboardInterrupt:
        logger.info("Bot dihentikan manual.")
        break
    except Exception as e:
        logger.error(f"Error loop: {e}")
