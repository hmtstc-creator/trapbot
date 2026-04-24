# ============================================================
# BESBOT — API Endpoint'leri
# ============================================================
# Bu dosyayı main.py'nin sonuna ekle:
#
#   from besbot.besbot_routes import besbot_router
#   app.include_router(besbot_router)
#
# Sonra yeni endpoint'ler:
#   GET  /besbot/grid/suggest/{symbol}  → Otomatik grid aralığı öner
#   POST /besbot/grid/setup             → Grid bot kur
#   GET  /besbot/grid/status            → Grid durumu
#   POST /besbot/grid/stop              → Grid durdur
#   GET  /besbot/trap/analyze/{symbol}  → Trap analizi (futures için)
#   POST /besbot/trap/open-short        → SHORT pozisyon aç
#   GET  /besbot/futures/balance        → Futures bakiyesi
#   GET  /besbot/futures/positions      → Açık pozisyonlar
# ============================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from besbot.grid_strategy import GridBot, GridConfig
from besbot.trap_futures_strategy import TrapFuturesBot, TrapFuturesConfig
from besbot.futures_client import BinanceFuturesClient

besbot_router = APIRouter(prefix="/besbot", tags=["BesBot Strategies"])

# ── Client ve Bot örnekleri ──────────────────────────────────
futures_client = BinanceFuturesClient(
    api_key    = os.getenv("BINANCE_API_KEY", ""),
    api_secret = os.getenv("BINANCE_API_SECRET", ""),
    testnet    = os.getenv("BINANCE_TESTNET", "true").lower() == "true"
)

# Aktif botlar (bellekte tutulur, Render yeniden başlayınca sıfırlanır)
active_grid_bots:  dict = {}
active_trap_bots:  dict = {}

# ── Pydantic Modeller ────────────────────────────────────────
class GridSetupRequest(BaseModel):
    symbol:       str   = "BTCUSDT"
    lower_price:  float
    upper_price:  float
    grid_count:   int   = 10
    total_budget: float = 100.0

class TrapShortRequest(BaseModel):
    symbol:   str   = "BTCUSDT"
    interval: str   = "1h"
    leverage: int   = 3
    risk_pct: float = 1.0

# ════════════════════════════════════════════════════════════
# GRID BOT ENDPOINT'LERİ
# ════════════════════════════════════════════════════════════

@besbot_router.get("/grid/suggest/{symbol}")
async def grid_suggest(symbol: str, interval: str = "1h"):
    """
    Sembol için otomatik grid aralığı öner.
    Son 50 mumun high/low'una bakarak hesaplar.
    """
    try:
        # Spot fiyat verisi kullan (futures da aynı fiyat)
        from binance_client import BinanceClient
        spot = BinanceClient(
            os.getenv("BINANCE_API_KEY",""),
            os.getenv("BINANCE_API_SECRET",""),
            testnet=os.getenv("BINANCE_TESTNET","true").lower()=="true"
        )
        candles = await spot.get_klines(symbol.upper(), interval, 50)
        bot     = GridBot(GridConfig(symbol=symbol.upper()))
        result  = bot.suggest_grid_range(candles)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@besbot_router.post("/grid/setup")
async def grid_setup(req: GridSetupRequest):
    """
    Grid bot kur ve seviyeleri hesapla.
    Henüz gerçek emir açmaz — sadece seviyeler hesaplanır.
    Gerçek emirler için /grid/start endpoint'i gelecek versiyonda.
    """
    try:
        config  = GridConfig(
            symbol       = req.symbol.upper(),
            lower_price  = req.lower_price,
            upper_price  = req.upper_price,
            grid_count   = req.grid_count,
            total_budget = req.total_budget,
        )
        bot     = GridBot(config)
        result  = bot.setup()
        active_grid_bots[req.symbol.upper()] = bot
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@besbot_router.get("/grid/status/{symbol}")
async def grid_status(symbol: str):
    bot = active_grid_bots.get(symbol.upper())
    if not bot:
        return {"status": "NO_ACTIVE_GRID", "symbol": symbol.upper()}
    return bot.get_status()

@besbot_router.post("/grid/stop/{symbol}")
async def grid_stop(symbol: str):
    bot = active_grid_bots.pop(symbol.upper(), None)
    if not bot:
        return {"status": "NOT_FOUND"}
    return bot.stop()

# ════════════════════════════════════════════════════════════
# TRAP FUTURES ENDPOINT'LERİ
# ════════════════════════════════════════════════════════════

@besbot_router.get("/trap/analyze/{symbol}")
async def trap_analyze_futures(symbol: str, interval: str = "1h", leverage: int = 3):
    """
    Bearish Sell Trap analizi yap, futures SHORT sinyali döndür.
    """
    try:
        from binance_client import BinanceClient
        spot = BinanceClient(
            os.getenv("BINANCE_API_KEY",""),
            os.getenv("BINANCE_API_SECRET",""),
            testnet=os.getenv("BINANCE_TESTNET","true").lower()=="true"
        )
        candles = await spot.get_klines(symbol.upper(), interval, 100)
        config  = TrapFuturesConfig(
            symbol=symbol.upper(), interval=interval, leverage=leverage
        )
        bot     = TrapFuturesBot(config)
        result  = bot.analyze_and_signal(candles)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@besbot_router.post("/trap/open-short")
async def trap_open_short(req: TrapShortRequest):
    """
    Trap sinyali varsa otomatik SHORT pozisyon aç.
    ⚠ TESTNET'TE TEST ET — gerçek para kaybedebilirsin!
    """
    try:
        from binance_client import BinanceClient
        spot = BinanceClient(
            os.getenv("BINANCE_API_KEY",""),
            os.getenv("BINANCE_API_SECRET",""),
            testnet=os.getenv("BINANCE_TESTNET","true").lower()=="true"
        )
        candles = await spot.get_klines(req.symbol.upper(), req.interval, 100)
        config  = TrapFuturesConfig(
            symbol=req.symbol.upper(), leverage=req.leverage,
            risk_per_trade=req.risk_pct
        )
        bot     = TrapFuturesBot(config)
        signal  = bot.analyze_and_signal(candles)

        if not signal["signal"]:
            return {"executed": False, "reason": "Sinyal yok", "state": signal["state"]}

        # Bakiye al
        balance = await futures_client.get_balance()
        usdt    = balance["usdt_available"]

        # Kaldıraç ayarla
        await futures_client.set_leverage(req.symbol.upper(), req.leverage)
        await futures_client.set_margin_type(req.symbol.upper(), "ISOLATED")

        # Pozisyon büyüklüğü
        qty = bot.calculate_position_size(usdt, signal["entry"], signal["sl"])

        if qty <= 0:
            return {"executed": False, "reason": "Yetersiz bakiye"}

        # SHORT aç
        result = await futures_client.open_short(
            symbol   = req.symbol.upper(),
            quantity = qty,
            sl       = signal["sl"],
            tp       = signal["tp"],
        )

        return {
            "executed": True,
            "symbol":   req.symbol.upper(),
            "side":     "SHORT",
            "quantity": qty,
            "entry":    signal["entry"],
            "sl":       signal["sl"],
            "tp":       signal["tp"],
            "leverage": req.leverage,
            "order":    result,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ════════════════════════════════════════════════════════════
# FUTURES HESAP ENDPOINT'LERİ
# ════════════════════════════════════════════════════════════

@besbot_router.get("/futures/balance")
async def futures_balance():
    try:
        return await futures_client.get_balance()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@besbot_router.get("/futures/positions")
async def futures_positions(symbol: Optional[str] = None):
    try:
        return await futures_client.get_positions(symbol)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@besbot_router.post("/futures/close/{symbol}")
async def futures_close(symbol: str, quantity: float):
    try:
        return await futures_client.close_position(symbol.upper(), quantity)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
