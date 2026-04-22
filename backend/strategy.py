# ============================================================
# Bearish Sell Trap Strategy — Python Implementation
# Mirrors the Pine Script logic exactly
# ============================================================

import statistics
from typing import List, Dict, Any

class BearishSellTrapStrategy:
    """
    State machine that detects the Bearish Sell Trap pattern:
    State 0 → WATCHING   : No setup
    State 1 → SETUP      : Real Zone touched
    State 2 → FAKE_ZONE  : Price pulled back to fake zone (low volume)
    State 3 → STOP_HUNT  : Consolidating in fake zone (retail stops being hunted)
    State 4 → CONFIRMATION: Price returned to Real Zone for rejection
    State 5 → SIGNAL     : Rejection candle confirmed → SELL
    """

    def __init__(self, lookback: int = 50, atr_length: int = 14,
                 volume_mult: float = 1.5, rsi_length: int = 14):
        self.lookback     = lookback
        self.atr_length   = atr_length
        self.volume_mult  = volume_mult
        self.rsi_length   = rsi_length

    # ── Indicators ──────────────────────────────────────────

    def _atr(self, candles: List[Dict]) -> float:
        trs = []
        for i in range(1, len(candles)):
            h = candles[i]["high"]
            l = candles[i]["low"]
            pc = candles[i-1]["close"]
            trs.append(max(h - l, abs(h - pc), abs(l - pc)))
        if not trs:
            return 0
        return statistics.mean(trs[-self.atr_length:])

    def _rsi(self, candles: List[Dict]) -> float:
        closes = [c["close"] for c in candles]
        if len(closes) < self.rsi_length + 1:
            return 50.0
        gains, losses = [], []
        for i in range(1, self.rsi_length + 1):
            diff = closes[-i] - closes[-i-1]
            (gains if diff > 0 else losses).append(abs(diff))
        avg_gain = statistics.mean(gains) if gains else 0.001
        avg_loss = statistics.mean(losses) if losses else 0.001
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _ema(self, candles: List[Dict], period: int) -> float:
        closes = [c["close"] for c in candles]
        if len(closes) < period:
            return closes[-1]
        k = 2 / (period + 1)
        ema = statistics.mean(closes[:period])
        for price in closes[period:]:
            ema = price * k + ema * (1 - k)
        return ema

    def _poc(self, candles: List[Dict]) -> float:
        """Point of Control: close of the highest-volume candle"""
        best = max(candles, key=lambda c: c["volume"])
        return best["close"]

    def _avg_volume(self, candles: List[Dict]) -> float:
        return statistics.mean(c["volume"] for c in candles)

    # ── Zone Detection ───────────────────────────────────────

    def _real_zone(self, candles: List[Dict], atr: float):
        highs = [c["high"] for c in candles[-self.lookback:]]
        rz_high = max(highs)
        rz_low  = rz_high - atr
        return rz_high, rz_low

    def _fake_zone(self, rz_low: float, atr: float):
        fz_high = rz_low
        fz_low  = rz_low - atr * 1.5
        return fz_high, fz_low

    # ── Candle Patterns ──────────────────────────────────────

    def _is_rejection_candle(self, c: Dict) -> bool:
        body        = abs(c["close"] - c["open"])
        upper_shadow = c["high"] - max(c["close"], c["open"])
        if body == 0:
            return False
        return upper_shadow > body * 2.0

    # ── Main Analysis ────────────────────────────────────────

    def analyze(self, candles: List[Dict]) -> Dict[str, Any]:
        if len(candles) < self.lookback + 5:
            return {"state": "INSUFFICIENT_DATA", "signal": False}

        recent   = candles[-self.lookback:]
        last     = candles[-1]
        prev     = candles[-2]
        atr      = self._atr(candles)
        rsi      = self._rsi(candles)
        avg_vol  = self._avg_volume(recent)
        poc      = self._poc(recent)
        ema50    = self._ema(candles, 50)
        ema200   = self._ema(candles, 200) if len(candles) >= 200 else self._ema(candles, len(candles))

        rz_high, rz_low = self._real_zone(candles, atr)
        fz_high, fz_low = self._fake_zone(rz_low, atr)

        vah = poc + atr * 1.5
        val = poc - atr * 1.5

        # Zone membership
        in_real_zone = rz_low <= last["close"] <= rz_high + atr * 0.5
        in_fake_zone = fz_low <= last["close"] <= fz_high
        touched_real = last["high"] >= rz_low

        # Filters
        ema_bearish  = last["close"] < ema200 or ema50 < ema200
        rsi_in_range = 45 <= rsi <= 72
        low_volume   = last["volume"] < avg_vol * 0.85
        rejection    = self._is_rejection_candle(last)

        # ── State Machine ─────────────────────────────────────
        # We run a mini-replay over last N candles to determine state
        state        = 0
        fake_count   = 0
        state_label  = "WATCHING"

        for i, c in enumerate(candles[-30:]):
            vol_avg_local = self._avg_volume(candles[max(0, -30+i-self.lookback):-30+i+1] or [c])

            in_real = rz_low <= c["close"] <= rz_high + atr * 0.5
            in_fake = fz_low <= c["close"] <= fz_high
            touched = c["high"] >= rz_low
            low_v   = c["volume"] < (vol_avg_local * 0.85 if vol_avg_local else 1)

            if state == 0:
                if touched and c["volume"] > (vol_avg_local * 0.9 if vol_avg_local else 0):
                    state = 1
                    fake_count = 0

            elif state == 1:
                if in_fake and low_v:
                    state = 2
                    fake_count = 1
                elif c["close"] > rz_high + atr * 0.3:
                    state = 0

            elif state == 2:
                if in_fake:
                    fake_count += 1
                if fake_count >= 2:
                    state = 3
                if c["close"] > rz_high + atr * 0.3:
                    state = 0

            elif state == 3:
                if in_real:
                    state = 4

            elif state == 4:
                filter_ok = ema_bearish and rsi_in_range
                body_s    = abs(c["close"] - c["open"])
                up_sh     = c["high"] - max(c["close"], c["open"])
                is_rej    = up_sh > body_s * 2.0 and body_s > 0
                if is_rej and c["close"] < rz_high and filter_ok:
                    state = 5

        # State labels
        labels = {
            0: "WATCHING",
            1: "SETUP",
            2: "FAKE_ZONE",
            3: "STOP_HUNT",
            4: "CONFIRMATION",
            5: "SIGNAL"
        }
        state_label = labels.get(state, "WATCHING")

        # Signal details
        signal   = state == 5
        entry    = last["close"] if signal else None
        sl       = (rz_high + atr) if signal else None
        tp       = (last["close"] - (sl - last["close"]) * 2.0) if signal else None
        risk_reward = 2.0 if signal else None

        return {
            "state":          state_label,
            "signal":         signal,
            "entry":          round(entry, 4) if entry else None,
            "sl":             round(sl, 4) if sl else None,
            "tp":             round(tp, 4) if tp else None,
            "risk_reward":    risk_reward,
            "real_zone_high": round(rz_high, 4),
            "real_zone_low":  round(rz_low, 4),
            "fake_zone_high": round(fz_high, 4),
            "fake_zone_low":  round(fz_low, 4),
            "poc":            round(poc, 4),
            "vah":            round(vah, 4),
            "val":            round(val, 4),
            "rsi":            round(rsi, 2),
            "ema50":          round(ema50, 4),
            "ema200":         round(ema200, 4),
            "ema_bearish":    ema_bearish,
            "rsi_in_range":   rsi_in_range,
            "avg_volume":     round(avg_vol, 2),
            "last_volume":    round(last["volume"], 2),
            "last_close":     last["close"],
            "atr":            round(atr, 4),
        }
