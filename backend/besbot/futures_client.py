# ============================================================
# BESBOT — Binance FUTURES Client
# ============================================================
# Ana binance_client.py spot işlemler içindi.
# Bu dosya FUTURES (vadeli) işlemleri için.
#
# FARK:
#   Spot endpoint:    /api/v3/...
#   Futures endpoint: /fapi/v1/... (Futures API)
#   Testnet URL:      https://testnet.binancefuture.com
# ============================================================

import hmac, hashlib, time, aiohttp
from urllib.parse import urlencode
from typing import Optional

class BinanceFuturesClient:
    LIVE_URL    = "https://fapi.binance.com"
    TESTNET_URL = "https://testnet.binancefuture.com"

    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key    = api_key
        self.api_secret = api_secret
        self.base_url   = self.TESTNET_URL if testnet else self.LIVE_URL
        self.testnet    = testnet

    def _sign(self, params: dict) -> str:
        query = urlencode(params)
        return hmac.new(
            self.api_secret.encode(), query.encode(), hashlib.sha256
        ).hexdigest()

    def _headers(self):
        return {"X-MBX-APIKEY": self.api_key}

    async def _get(self, path, params=None, signed=False):
        params = params or {}
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._sign(params)
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{self.base_url}{path}",
                             params=params, headers=self._headers()) as r:
                data = await r.json()
                if isinstance(data, dict) and data.get("code", 0) < 0:
                    raise Exception(f"Binance Futures error: {data}")
                return data

    async def _post(self, path, params):
        params["timestamp"] = int(time.time() * 1000)
        params["signature"] = self._sign(params)
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{self.base_url}{path}",
                              params=params, headers=self._headers()) as r:
                data = await r.json()
                if isinstance(data, dict) and data.get("code", 0) < 0:
                    raise Exception(f"Binance Futures error: {data}")
                return data

    # ── Kaldıraç Ayarla ─────────────────────────────────────
    async def set_leverage(self, symbol: str, leverage: int):
        """
        ÖNEMLİ: İlk pozisyon açmadan önce kaldıracı ayarla.
        Render.com'da bot başlarken otomatik çağrılır.
        """
        return await self._post("/fapi/v1/leverage", {
            "symbol": symbol, "leverage": leverage
        })

    async def set_margin_type(self, symbol: str, margin_type: str = "ISOLATED"):
        """
        ISOLATED = sadece o pozisyon için ayırdığın para riske girer
        CROSSED  = tüm bakiye riske girer (tehlikeli)
        Her zaman ISOLATED kullan!
        """
        try:
            return await self._post("/fapi/v1/marginType", {
                "symbol": symbol, "marginType": margin_type
            })
        except Exception as e:
            if "No need to change" in str(e):
                return {"status": "already_set"}
            raise

    # ── Pozisyon Aç ─────────────────────────────────────────
    async def open_short(self, symbol: str, quantity: float,
                          sl: float, tp: float):
        """
        SHORT pozisyon aç + otomatik SL/TP koy.
        SHORT = fiyat düşeceğini bekliyorsun.
        """
        # Ana SHORT emri
        order = await self._post("/fapi/v1/order", {
            "symbol":    symbol,
            "side":      "SELL",        # SHORT açmak için SELL
            "type":      "MARKET",
            "quantity":  quantity,
            "positionSide": "SHORT",
        })

        # Stop-Loss emri
        sl_order = await self._post("/fapi/v1/order", {
            "symbol":        symbol,
            "side":          "BUY",     # SHORT kapatmak için BUY
            "type":          "STOP_MARKET",
            "stopPrice":     sl,
            "closePosition": "true",
            "positionSide":  "SHORT",
        })

        # Take-Profit emri
        tp_order = await self._post("/fapi/v1/order", {
            "symbol":        symbol,
            "side":          "BUY",
            "type":          "TAKE_PROFIT_MARKET",
            "stopPrice":     tp,
            "closePosition": "true",
            "positionSide":  "SHORT",
        })

        return {
            "position": order,
            "sl_order": sl_order,
            "tp_order": tp_order,
        }

    # ── Hesap Bilgileri ──────────────────────────────────────
    async def get_account(self):
        return await self._get("/fapi/v2/account", signed=True)

    async def get_positions(self, symbol: Optional[str] = None):
        data = await self._get("/fapi/v2/positionRisk", signed=True)
        if symbol:
            return [p for p in data if p["symbol"] == symbol
                    and float(p["positionAmt"]) != 0]
        return [p for p in data if float(p["positionAmt"]) != 0]

    async def get_balance(self):
        data = await self._get("/fapi/v2/balance", signed=True)
        usdt = next((b for b in data if b["asset"] == "USDT"), None)
        return {
            "usdt_balance":    float(usdt["balance"])    if usdt else 0,
            "usdt_available":  float(usdt["availableBalance"]) if usdt else 0,
            "testnet":         self.testnet,
        }

    async def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100):
        raw = await self._get("/fapi/v1/klines", {
            "symbol": symbol, "interval": interval, "limit": limit
        })
        return [{
            "open_time": c[0], "open": float(c[1]), "high": float(c[2]),
            "low": float(c[3]), "close": float(c[4]), "volume": float(c[5]),
        } for c in raw]

    async def close_position(self, symbol: str, quantity: float,
                              position_side: str = "SHORT"):
        """Açık pozisyonu kapat"""
        side = "BUY" if position_side == "SHORT" else "SELL"
        return await self._post("/fapi/v1/order", {
            "symbol":       symbol,
            "side":         side,
            "type":         "MARKET",
            "quantity":     quantity,
            "positionSide": position_side,
            "reduceOnly":   "true",
        })

    async def cancel_all_orders(self, symbol: str):
        return await self._post("/fapi/v1/allOpenOrders",
                                {"symbol": symbol})
