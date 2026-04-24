# ============================================================
# TRAP BOT — FastAPI Backend
# Binance API + Bearish Sell Trap Detection
# ============================================================

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
from dotenv import load_dotenv
from binance_client import BinanceClient
from strategy import BearishSellTrapStrategy
from supabase_client import SupabaseClient
from besbot.besbot_routes import besbot_router
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trap Bot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# BesBot stratejileri
app.include_router(besbot_router)

# Clients
binance = BinanceClient(
    api_key=os.getenv("BINANCE_API_KEY", ""),
    api_secret=os.getenv("BINANCE_API_SECRET", ""),
    testnet=os.getenv("BINANCE_TESTNET", "true").lower() == "true"
)
strategy = BearishSellTrapStrategy()
db = SupabaseClient(
    url=os.getenv("SUPABASE_URL", ""),
    key=os.getenv("SUPABASE_KEY", "")
)

# ── Models ──────────────────────────────────────────────────
class TradeOrder(BaseModel):
    symbol: str
    side: str        # BUY or SELL
    quantity: float
    order_type: str = "MARKET"

class BotConfig(BaseModel):
    symbol: str = "BTCUSDT"
    interval: str = "1h"
    lookback: int = 50
    risk_percent: float = 1.0   # % of balance per trade
    auto_trade: bool = False

# ── State ────────────────────────────────────────────────────
bot_state = {
    "running": False,
    "config": BotConfig().dict(),
    "last_signal": None,
    "current_state": "WATCHING"
}

# ── Routes ───────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "Trap Bot is alive 🔴"}

@app.get("/api/price/{symbol}")
async def get_price(symbol: str):
    """Get current price from Binance"""
    try:
        price = await binance.get_price(symbol.upper())
        return {"symbol": symbol.upper(), "price": price}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/balance")
async def get_balance():
    """Get account balance"""
    try:
        balance = await binance.get_balance()
        return balance
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/candles/{symbol}")
async def get_candles(symbol: str, interval: str = "1h", limit: int = 100):
    """Get OHLCV candle data"""
    try:
        candles = await binance.get_klines(symbol.upper(), interval, limit)
        return {"symbol": symbol, "interval": interval, "candles": candles}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/analyze/{symbol}")
async def analyze(symbol: str, interval: str = "1h"):
    """Run Bearish Sell Trap analysis on symbol"""
    try:
        candles = await binance.get_klines(symbol.upper(), interval, 100)
        result = strategy.analyze(candles)
        
        # Log to Supabase
        if db.enabled:
            await db.log_signal({
                "symbol": symbol.upper(),
                "interval": interval,
                "state": result["state"],
                "signal": result["signal"],
                "real_zone_high": result["real_zone_high"],
                "real_zone_low": result["real_zone_low"],
                "fake_zone_high": result["fake_zone_high"],
                "fake_zone_low": result["fake_zone_low"],
                "poc": result["poc"],
                "rsi": result["rsi"],
                "entry": result.get("entry"),
                "sl": result.get("sl"),
                "tp": result.get("tp"),
            })
        
        bot_state["last_signal"] = result
        bot_state["current_state"] = result["state"]
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/trade")
async def manual_trade(order: TradeOrder):
    """Execute a manual trade"""
    try:
        result = await binance.place_order(
            symbol=order.symbol.upper(),
            side=order.side.upper(),
            quantity=order.quantity,
            order_type=order.order_type
        )
        
        if db.enabled:
            await db.log_trade({
                "symbol": order.symbol,
                "side": order.side,
                "quantity": order.quantity,
                "order_id": result.get("orderId"),
                "status": result.get("status"),
                "type": "MANUAL"
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/trades")
async def get_trades(symbol: str = "BTCUSDT", limit: int = 50):
    """Get recent trade history"""
    try:
        trades = await binance.get_my_trades(symbol.upper(), limit)
        return {"trades": trades}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/signals")
async def get_signals(limit: int = 20):
    """Get signal history from Supabase"""
    if not db.enabled:
        return {"signals": [], "note": "Supabase not configured"}
    try:
        signals = await db.get_signals(limit)
        return {"signals": signals}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/bot/status")
async def bot_status():
    return bot_state

@app.post("/api/bot/config")
async def update_config(config: BotConfig):
    bot_state["config"] = config.dict()
    return {"status": "Config updated", "config": config}

@app.get("/api/open-orders/{symbol}")
async def open_orders(symbol: str):
    try:
        orders = await binance.get_open_orders(symbol.upper())
        return {"orders": orders}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/cancel-order/{symbol}/{order_id}")
async def cancel_order(symbol: str, order_id: int):
    try:
        result = await binance.cancel_order(symbol.upper(), order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
