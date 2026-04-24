# ============================================================
# BESBOT — STRATEJİ 2: BEARISH SELL TRAP (FUTURES/KALDIRAÇLI)
# ============================================================
# Ana strategy.py'deki BearishSellTrapStrategy'yi kaldıraçlı
# futures işlemleri için genişletir.
#
# FARK:
#   Spot     → direkt SAT (elindeki coini sat)
#   Futures  → SHORT aç (coini ödünç al, sat, düşünce geri al)
#
# KALDIRAÇ UYARISI:
#   5x kaldıraç = 1000$ ile 5000$'lık pozisyon açmak demek
#   Lehine giderse 5x kâr, aleyhine giderse 5x zarar
#   Tasfiye (liquidation) = tüm parayı kaybetmek
#   ÖNERİ: Başlangıçta max 3x kullan
# ============================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from strategy import BearishSellTrapStrategy
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class TrapFuturesConfig:
    symbol:           str   = "BTCUSDT"
    interval:         str   = "1h"
    leverage:         int   = 3        # Kaldıraç — başlangıç 3x önerilir
    risk_per_trade:   float = 1.0      # Her işlemde bakiyenin %kaçı risk alınsın
    max_positions:    int   = 1        # Aynı anda max açık pozisyon
    use_futures:      bool  = True
    # Stop-Loss ve Take-Profit
    sl_atr_mult:      float = 1.0      # SL = signal + 1x ATR
    tp_rr_ratio:      float = 2.0      # TP = 1:2 risk/reward
    # Güvenlik
    max_loss_pct:     float = 5.0      # Günlük max kayıp %5 → bot durur
    trailing_stop:    bool  = False    # Takip eden stop (ileri seviye)

class TrapFuturesBot:
    """
    Bearish Sell Trap → Futures SHORT stratejisi
    --------------------------------------------
    1. BearishSellTrapStrategy sinyal üretir (state=SIGNAL)
    2. Bot futures'ta SHORT pozisyon açar
    3. Stop-Loss ve Take-Profit otomatik hesaplanır
    4. Kaldıraç ile amplified kâr/zarar
    """

    def __init__(self, config: TrapFuturesConfig):
        self.config   = config
        self.strategy = BearishSellTrapStrategy()
        self.positions: List[Dict] = []
        self.daily_pnl = 0.0
        self.active    = True

    def analyze_and_signal(self, candles: List[Dict]) -> Dict:
        """
        Mum verilerini analiz et, sinyal varsa pozisyon detayı döndür.
        """
        result = self.strategy.analyze(candles)

        if not result.get("signal"):
            return {
                "signal":  False,
                "state":   result.get("state", "WATCHING"),
                "message": "Henüz sinyal yok, bekle.",
                "analysis": result
            }

        # Sinyal VAR → pozisyon hesapla
        entry    = result["entry"]
        atr      = result["atr"]
        sl       = entry + atr * self.config.sl_atr_mult   # SHORT için SL yukarıda
        tp       = entry - (sl - entry) * self.config.tp_rr_ratio

        # Kaldıraçlı pozisyon büyüklüğü
        # risk_per_trade = bakiyenin %1'i → örnek 1000$ bakiye → 10$ risk
        # quantity = risk_amount / (sl - entry)
        # Burası gerçek bakiyeye göre main.py'de hesaplanacak

        return {
            "signal":    True,
            "state":     "SIGNAL",
            "side":      "SHORT",
            "symbol":    self.config.symbol,
            "entry":     round(entry, 4),
            "sl":        round(sl, 4),
            "tp":        round(tp, 4),
            "leverage":  self.config.leverage,
            "rr_ratio":  self.config.tp_rr_ratio,
            "atr":       atr,
            "analysis":  result,
            "message":   f"SHORT sinyali! Entry: {entry:.4f} SL: {sl:.4f} TP: {tp:.4f} ({self.config.leverage}x)"
        }

    def calculate_position_size(self, balance_usdt: float, entry: float, sl: float) -> float:
        """
        Risk yönetimine göre pozisyon büyüklüğü hesapla.
        risk_per_trade = %1 → 1000$ bakiyede 10$ riske gir
        """
        risk_amount  = balance_usdt * (self.config.risk_per_trade / 100)
        price_risk   = abs(entry - sl)           # Entry ile SL arası fark
        if price_risk == 0:
            return 0
        raw_qty      = risk_amount / price_risk
        # Kaldıraçla gerçek pozisyon değeri
        notional     = raw_qty * entry
        leveraged    = notional / self.config.leverage
        return round(raw_qty, 6)

    def check_daily_loss_limit(self) -> bool:
        """Günlük kayıp limitine ulaşıldı mı?"""
        return abs(self.daily_pnl) >= self.config.max_loss_pct

    def get_status(self) -> Dict:
        return {
            "active":          self.active,
            "symbol":          self.config.symbol,
            "leverage":        self.config.leverage,
            "open_positions":  len(self.positions),
            "daily_pnl":       round(self.daily_pnl, 2),
            "risk_per_trade":  f"%{self.config.risk_per_trade}",
            "max_loss_limit":  f"%{self.config.max_loss_pct}",
        }
