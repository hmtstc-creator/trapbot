import { useState } from "react"
import StateCard from "../components/StateCard"
import ZonePanel from "../components/ZonePanel"
import PriceBar from "../components/PriceBar"
import CandleChart from "../components/CandleChart"
import TradePanel from "../components/TradePanel"
import SignalLog from "../components/SignalLog"
import FilterBadges from "../components/FilterBadges"
import Ticker from "../components/Ticker"

const SYMBOLS  = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","ADAUSDT"]
const INTERVALS = ["15m","30m","1h","4h","1d"]

export default function Dashboard({
  symbol, setSymbol, interval, setInterval,
  data, price, balance, loading, signals, candles,
  error, lastUpdate, onRefresh, onTrade
}) {
  const [tradeMsg, setTradeMsg] = useState(null)

  const handleTrade = async (side, qty) => {
    const res = await onTrade(side, qty)
    setTradeMsg(res.success
      ? `✅ ${side} emri verildi — Order ID: ${res.data.orderId}`
      : `❌ Hata: ${res.error}`)
    setTimeout(() => setTradeMsg(null), 5000)
  }

  const stateColor = {
    WATCHING:      "#4a5568",
    SETUP:         "#3b82f6",
    FAKE_ZONE:     "#f59e0b",
    STOP_HUNT:     "#f97316",
    CONFIRMATION:  "#8b5cf6",
    SIGNAL:        "#ef4444",
    INSUFFICIENT_DATA: "#6b7280"
  }

  const state = data?.state || "WATCHING"
  const color = stateColor[state] || "#4a5568"

  return (
    <div className="terminal">
      {/* ── Header ── */}
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">▼</span>
            <span className="logo-text">TRAP<span className="logo-accent">BOT</span></span>
          </div>
          <div className="tagline">Bearish Sell Trap Detection System</div>
        </div>

        <div className="header-center">
          <Ticker price={price} symbol={symbol} />
        </div>

        <div className="header-right">
          <div className="controls">
            <select className="select" value={symbol}
              onChange={e => setSymbol(e.target.value)}>
              {SYMBOLS.map(s => <option key={s}>{s}</option>)}
            </select>
            <select className="select" value={interval}
              onChange={e => setInterval(e.target.value)}>
              {INTERVALS.map(i => <option key={i}>{i}</option>)}
            </select>
            <button className={`refresh-btn ${loading ? "spinning" : ""}`}
              onClick={onRefresh} disabled={loading}>
              {loading ? "⟳" : "↺"} Tazele
            </button>
          </div>
          {lastUpdate && (
            <div className="last-update">
              Son: {lastUpdate.toLocaleTimeString("tr-TR")}
              <span className="auto-label"> · 30s auto</span>
            </div>
          )}
        </div>
      </header>

      {/* ── Error Banner ── */}
      {error && (
        <div className="error-banner">⚠ {error}</div>
      )}

      {/* ── State Hero ── */}
      <div className="state-hero" style={{ "--state-color": color }}>
        <StateCard state={state} color={color} data={data} />
      </div>

      {/* ── Main Grid ── */}
      <div className="main-grid">
        {/* Left column */}
        <div className="col-left">
          <CandleChart candles={candles} data={data} />
          <ZonePanel data={data} />
        </div>

        {/* Right column */}
        <div className="col-right">
          <FilterBadges data={data} />
          {data?.signal && (
            <div className="signal-alert">
              <div className="signal-alert-icon">🔴</div>
              <div className="signal-alert-body">
                <div className="signal-alert-title">SMART SELL SİNYALİ</div>
                <div className="signal-alert-row">
                  <span>GİRİŞ</span><strong>{data.entry}</strong>
                </div>
                <div className="signal-alert-row sl">
                  <span>STOP LOSS</span><strong>{data.sl}</strong>
                </div>
                <div className="signal-alert-row tp">
                  <span>HEDEF</span><strong>{data.tp}</strong>
                </div>
                <div className="signal-alert-row">
                  <span>R:R</span><strong>1:{data.risk_reward}</strong>
                </div>
              </div>
            </div>
          )}
          <TradePanel
            symbol={symbol}
            balance={balance}
            data={data}
            onTrade={handleTrade}
            tradeMsg={tradeMsg}
          />
          <SignalLog signals={signals} />
        </div>
      </div>

      {/* ── Footer ── */}
      <footer className="footer">
        <span>⚠ Bu sistem eğitim amaçlıdır. Gerçek para kaybedebilirsiniz.</span>
        <span>Testnet modu aktif · DYOR · NFA</span>
      </footer>
    </div>
  )
}
