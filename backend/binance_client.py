# ============================================================
# Binance Client — Async HTTP wrapper
# Supports both Testnet and Live
# ============================================================

import hmac
import hashlib
import time
import aiohttp
from urllib.parse import urlencode
from typing import Optional

class BinanceClient:
    LIVE_URL    = "https://api.binance.com"
    TESTNET_URL = "https://testnet.binance.vision"

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

    async def _get(self, path: str, params: dict = None, signed: bool = False):
        params = params or {}
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._sign(params)
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{self.base_url}{path}",
                params=params,
                headers=self._headers()
            ) as r:
                data = await r.json()
                if isinstance(data, dict) and "code" in data and data["code"] < 0:
                    raise Exception(f"Binance error {data['code']}: {data['msg']}")
                return data

    async def _post(self, path: str, params: dict):
        params["timestamp"] = int(time.time() * 1000)
        params["signature"] = self._sign(params)
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{self.base_url}{path}",
                params=params,
                headers=self._headers()
            ) as r:
                data = await r.json()
                if isinstance(data, dict) and "code" in data and data["code"] < 0:
                    raise Exception(f"Binance error {data['code']}: {data['msg']}")
                return data

    async def _delete(self, path: str, params: dict):
        params["timestamp"] = int(time.time() * 1000)
        params["signature"] = self._sign(params)
        async with aiohttp.ClientSession() as s:
            async with s.delete(
                f"{self.base_url}{path}",
                params=params,
                headers=self._headers()
            ) as r:
                return await r.json()

    # ── Public endpoints ────────────────────────────────────

    async def get_price(self, symbol: str) -> float:
        data = await self._get("/api/v3/ticker/price", {"symbol": symbol})
        if isinstance(data,dict) and "price" in data:
            return float(data["price"])
        raise Exception(f"Binance Fiyat Alınamadı: {data}")

    async def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100):
        raw = await self._get("/api/v3/klines", {
            "symbol": symbol, "interval": interval, "limit": limit
        })
        return [{
            "open_time": c[0],
            "open":      float(c[1]),
            "high":      float(c[2]),
            "low":       float(c[3]),
            "close":     float(c[4]),
            "volume":    float(c[5]),
            "close_time":c[6],
        } for c in raw]

    async def get_exchange_info(self, symbol: str):
        return await self._get("/api/v3/exchangeInfo", {"symbol": symbol})

    # ── Private endpoints ────────────────────────────────────

    async def get_balance(self):
        data = await self._get("/api/v3/account", signed=True)
        balances = [b for b in data.get("balances", [])
                    if float(b["free"]) > 0 or float(b["locked"]) > 0]
        return {"balances": balances, "testnet": self.testnet}

    async def place_order(self, symbol: str, side: str,
                          quantity: float, order_type: str = "MARKET",
                          price: Optional[float] = None):
        params = {
            "symbol":   symbol,
            "side":     side,
            "type":     order_type,
            "quantity": quantity,
        }
        if order_type == "LIMIT" and price:
            params["price"]    = price
            params["timeInForce"] = "GTC"
        return await self._post("/api/v3/order", params)

    async def get_my_trades(self, symbol: str, limit: int = 50):
        return await self._get("/api/v3/myTrades",
                               {"symbol": symbol, "limit": limit}, signed=True)

    async def get_open_orders(self, symbol: str):
        return await self._get("/api/v3/openOrders",
                               {"symbol": symbol}, signed=True)

    async def cancel_order(self, symbol: str, order_id: int):
        return await self._delete("/api/v3/order",
                                  {"symbol": symbol, "orderId": order_id})
