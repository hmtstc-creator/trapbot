import { useState } from "react"

export default function TradePanel({ symbol, balance, data, onTrade, tradeMsg }) {
  const [qty, setQty]       = useState("0.001")
  const [confirm, setConfirm] = useState(null)

  const usdt = balance?.balances?.find(b => b.asset === "USDT")
  const base = balance?.balances?.find(b => b.asset === symbol.replace("USDT",""))

  const handleClick = (side) => {
    setConfirm({ side, qty })
  }

  const handleConfirm = () => {
    if (confirm) {
      onTrade(confirm.side, confirm.qty)
      setConfirm(null)
    }
  }

  return (
    <div className="panel trade-panel">
      <div className="panel-title">
        ⚡ TRADE PANELİ
        {balance?.testnet && <span className="testnet-badge">TESTNET</span>}
      </div>

      {/* Balance */}
      <div className="balance-row">
        <div className="balance-item">
          <span className="balance-label">USDT</span>
          <span className="balance-val">{usdt ? parseFloat(usdt.free).toFixed(2) : "—"}</span>
        </div>
        <div className="balance-item">
          <span className="balance-label">{symbol.replace("USDT","")}</span>
          <span className="balance-val">{base ? parseFloat(base.free).toFixed(6) : "—"}</span>
        </div>
      </div>

      {/* Suggested from signal */}
      {data?.signal && (
        <div className="signal-hint">
          💡 Strateji önerisi: <strong>SELL</strong> — Entry: {data.entry} · SL: {data.sl} · TP: {data.tp}
        </div>
      )}

      {/* Qty input */}
      <div className="qty-row">
        <label className="qty-label">MİKTAR ({symbol.replace("USDT","")})</label>
        <input
          className="qty-input"
          type="number"
          value={qty}
          step="0.001"
          min="0.0001"
          onChange={e => setQty(e.target.value)}
        />
      </div>

      {/* Buttons */}
      {!confirm ? (
        <div className="trade-btns">
          <button className="btn-buy"  onClick={() => handleClick("BUY")}>▲ AL</button>
          <button className="btn-sell" onClick={() => handleClick("SELL")}>▼ SAT</button>
        </div>
      ) : (
        <div className="confirm-box">
          <div className="confirm-msg">
            {confirm.side === "BUY" ? "▲" : "▼"} {confirm.side} · {confirm.qty} {symbol.replace("USDT","")}
            <br/>Emin misin?
          </div>
          <div className="confirm-btns">
            <button className="btn-confirm" onClick={handleConfirm}>✓ Onayla</button>
            <button className="btn-cancel"  onClick={() => setConfirm(null)}>✗ İptal</button>
          </div>
        </div>
      )}

      {tradeMsg && (
        <div className={`trade-msg ${tradeMsg.startsWith("✅") ? "trade-msg-ok" : "trade-msg-err"}`}>
          {tradeMsg}
        </div>
      )}

      <div className="trade-warning">
        ⚠ Market emri · Anlık fiyattan gerçekleşir
      </div>
    </div>
  )
}
