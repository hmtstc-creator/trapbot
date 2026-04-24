# ============================================================
# BESBOT — STRATEJİ 1: GRID BOT
# ============================================================
# Grid Bot mantığı:
#   Belirlenen fiyat aralığını eşit parçalara böler.
#   Her seviyeye bir BUY emri, bir üst seviyeye SELL emri koyar.
#   Fiyat yukarı çıkınca SELL → aşağı inince BUY → sürekli döner.
#
# Örnek: BTC 90.000 - 100.000 arası, 10 grid
#   Level 1: 90.000 BUY / 91.000 SELL
#   Level 2: 91.000 BUY / 92.000 SELL
#   ...
#   Fiyat her 1000$ hareket ettiğinde küçük kâr keser.
# ============================================================

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import math

@dataclass
class GridLevel:
    index:      int
    buy_price:  float
    sell_price: float
    quantity:   float
    status:     str = "WAITING"   # WAITING / BUY_FILLED / SELL_FILLED
    buy_order_id:  Optional[str] = None
    sell_order_id: Optional[str] = None
    profit:     float = 0.0

@dataclass
class GridConfig:
    symbol:       str   = "BTCUSDT"
    lower_price:  float = 0.0      # Grid alt sınırı
    upper_price:  float = 0.0      # Grid üst sınırı
    grid_count:   int   = 10       # Kaç seviye
    total_budget: float = 100.0    # Toplam USDT bütçesi
    use_futures:  bool  = False    # Spot mu Futures mu
    leverage:     int   = 1        # Futures kaldıraç (1 = kaldıraçsız)

class GridBot:
    """
    Grid Trading Bot
    ----------------
    Nasıl çalışır:
    1. setup()   → grid seviyelerini hesaplar
    2. on_price_update(price) → her yeni fiyatta kontrol eder
    3. Dolmuş emirleri tespit eder, karşı taraf emri açar
    4. Her döngüde kâr birikir
    """

    def __init__(self, config: GridConfig):
        self.config  = config
        self.levels: List[GridLevel] = []
        self.total_profit = 0.0
        self.trade_count  = 0
        self.active       = False

    def setup(self) -> Dict:
        """Grid seviyelerini hesapla ve döndür"""
        cfg = self.config
        if cfg.upper_price <= cfg.lower_price:
            return {"error": "Üst fiyat alt fiyattan büyük olmalı"}
        if cfg.grid_count < 2:
            return {"error": "En az 2 grid seviyesi gerekli"}

        step = (cfg.upper_price - cfg.lower_price) / cfg.grid_count
        budget_per_grid = cfg.total_budget / cfg.grid_count

        self.levels = []
        for i in range(cfg.grid_count):
            buy_price  = cfg.lower_price + step * i
            sell_price = cfg.lower_price + step * (i + 1)
            quantity   = round(budget_per_grid / buy_price, 6)

            self.levels.append(GridLevel(
                index      = i,
                buy_price  = round(buy_price, 2),
                sell_price = round(sell_price, 2),
                quantity   = quantity,
            ))

        self.active = True
        return {
            "status":      "GRID_READY",
            "levels":      len(self.levels),
            "step_size":   round(step, 2),
            "per_grid_budget": round(budget_per_grid, 2),
            "grid_levels": [
                {
                    "index":      l.index,
                    "buy_price":  l.buy_price,
                    "sell_price": l.sell_price,
                    "quantity":   l.quantity,
                }
                for l in self.levels
            ]
        }

    def on_price_update(self, current_price: float) -> List[Dict]:
        """
        Her fiyat güncellemesinde çağır.
        Doldurulması gereken emirleri döndürür.
        """
        if not self.active or not self.levels:
            return []

        actions = []

        for level in self.levels:
            # BUY emri doldu mu? (fiyat buy fiyatına indi)
            if level.status == "WAITING" and current_price <= level.buy_price:
                level.status = "BUY_FILLED"
                actions.append({
                    "action":    "BUY",
                    "level":     level.index,
                    "price":     level.buy_price,
                    "quantity":  level.quantity,
                    "symbol":    self.config.symbol,
                    "reason":    f"Grid seviye {level.index} BUY tetiklendi"
                })

            # SELL emri doldu mu? (fiyat sell fiyatına çıktı)
            elif level.status == "BUY_FILLED" and current_price >= level.sell_price:
                profit = (level.sell_price - level.buy_price) * level.quantity
                level.profit   += profit
                self.total_profit += profit
                self.trade_count  += 1
                level.status = "WAITING"  # Tekrar bekle

                actions.append({
                    "action":    "SELL",
                    "level":     level.index,
                    "price":     level.sell_price,
                    "quantity":  level.quantity,
                    "symbol":    self.config.symbol,
                    "profit":    round(profit, 4),
                    "total_profit": round(self.total_profit, 4),
                    "reason":    f"Grid seviye {level.index} SELL tetiklendi"
                })

        return actions

    def get_status(self) -> Dict:
        """Bot durumu özeti"""
        filled = sum(1 for l in self.levels if l.status == "BUY_FILLED")
        waiting = sum(1 for l in self.levels if l.status == "WAITING")
        return {
            "active":        self.active,
            "symbol":        self.config.symbol,
            "lower":         self.config.lower_price,
            "upper":         self.config.upper_price,
            "grid_count":    self.config.grid_count,
            "filled_levels": filled,
            "waiting_levels":waiting,
            "total_profit":  round(self.total_profit, 4),
            "trade_count":   self.trade_count,
        }

    def stop(self):
        self.active = False
        return {"status": "GRID_STOPPED", "final_profit": self.total_profit}

    def suggest_grid_range(self, candles: list) -> Dict:
        """
        Son N mum verisine bakarak otomatik grid aralığı öner.
        Volatiliteye göre alt/üst sınır hesaplar.
        """
        if len(candles) < 20:
            return {"error": "Yeterli veri yok"}

        highs = [c["high"]  for c in candles[-50:]]
        lows  = [c["low"]   for c in candles[-50:]]

        suggested_high = max(highs)
        suggested_low  = min(lows)
        mid            = (suggested_high + suggested_low) / 2
        spread_pct     = (suggested_high - suggested_low) / mid * 100

        # Optimal grid sayısı: spread'e göre
        if spread_pct < 5:
            suggested_grids = 5
        elif spread_pct < 15:
            suggested_grids = 10
        else:
            suggested_grids = 20

        return {
            "suggested_lower":  round(suggested_low  * 0.99, 2),
            "suggested_upper":  round(suggested_high * 1.01, 2),
            "suggested_grids":  suggested_grids,
            "spread_percent":   round(spread_pct, 2),
            "note": f"Son 50 mumun %{round(spread_pct,1)} spread'ine göre hesaplandı"
        }
