# ============================================================
# Supabase Client — Signal & Trade Logging (FIXED)
# ============================================================

from supabase import create_client, Client
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    def __init__(self, url: str, key: str):
        self.enabled = bool(url and key)
        self.client: Optional[Client] = None

        if self.enabled:
            try:
                self.client = create_client(url, key)
                logger.info("Supabase connected ✓")
            except Exception as e:
                logger.warning(f"Supabase connection failed: {e}")
                self.enabled = False

    # ─────────────────────────────────────────────
    # SIGNALS
    # ─────────────────────────────────────────────

    def log_signal(self, data: dict):
        if not self.enabled:
            return
        try:
            self.client.table("signals").insert(data).execute()
        except Exception as e:
            logger.error(f"Signal log failed: {e}")

    def get_signals(self, limit: int = 20):
        if not self.enabled:
            return []
        try:
            result = (
                self.client.table("signals")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Get signals failed: {e}")
            return []

    # ─────────────────────────────────────────────
    # TRADES
    # ─────────────────────────────────────────────

    def log_trade(self, data: dict):
        if not self.enabled:
            return
        try:
            self.client.table("trades").insert(data).execute()
        except Exception as e:
            logger.error(f"Trade log failed: {e}")

    def get_trades(self, limit: int = 20):
        if not self.enabled:
            return []
        try:
            result = (
                self.client.table("trades")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Get trades failed: {e}")
            return []