// ── ZonePanel ────────────────────────────────────────────────
export function ZonePanel({ data }) {
  if (!data) return null
  const zones = [
    { label: "REAL ZONE",      high: data.real_zone_high, low: data.real_zone_low,  color: "#ef4444" },
    { label: "FAKE SELL ZONE", high: data.fake_zone_high, low: data.fake_zone_low,  color: "#f59e0b" },
    { label: "POC",            value: data.poc,                                      color: "#eab308" },
    { label: "VAH",            value: data.vah,                                      color: "#3b82f6" },
    { label: "VAL",            value: data.val,                                      color: "#22c55e" },
  ]
  return (
    <div className="panel zone-panel">
      <div className="panel-title">📐 ZONE SEVİYELERİ</div>
      {zones.map(z => (
        <div key={z.label} className="zone-row" style={{ borderLeftColor: z.color }}>
          <span className="zone-label" style={{ color: z.color }}>{z.label}</span>
          <span className="zone-val">
            {z.value !== undefined
              ? z.value
              : `${z.low} — ${z.high}`}
          </span>
        </div>
      ))}
      <div className="zone-row" style={{ borderLeftColor: "#a78bfa" }}>
        <span className="zone-label" style={{ color: "#a78bfa" }}>EMA 50</span>
        <span className="zone-val">{data.ema50}</span>
      </div>
      <div className="zone-row" style={{ borderLeftColor: "#f87171" }}>
        <span className="zone-label" style={{ color: "#f87171" }}>EMA 200</span>
        <span className="zone-val">{data.ema200}</span>
      </div>
    </div>
  )
}

// ── FilterBadges ─────────────────────────────────────────────
export function FilterBadges({ data }) {
  if (!data) return null
  const volRatio = data.avg_volume > 0
    ? (data.last_volume / data.avg_volume).toFixed(2)
    : "—"
  const volLabel = parseFloat(volRatio) > 1.5
    ? "💪 GÜÇLÜ" : parseFloat(volRatio) < 0.8 ? "⚠️ ZAYIF" : "➡ NORMAL"

  const badges = [
    { label: "EMA Trend",   val: data.ema_bearish  ? "✅ BEARISH" : "❌ BULLISH", ok: data.ema_bearish },
    { label: "RSI Bandı",   val: data.rsi_in_range ? `✅ ${data.rsi}` : `❌ ${data.rsi}`, ok: data.rsi_in_range },
    { label: "Hacim",       val: volLabel,           ok: parseFloat(volRatio) !== 0.8 },
  ]
  return (
    <div className="panel">
      <div className="panel-title">🔍 FİLTRE DURUMU</div>
      <div className="badges">
        {badges.map(b => (
          <div key={b.label} className={`badge ${b.ok ? "badge-ok" : "badge-fail"}`}>
            <span className="badge-label">{b.label}</span>
            <span className="badge-val">{b.val}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Ticker ───────────────────────────────────────────────────
export function Ticker({ price, symbol }) {
  return (
    <div className="ticker">
      <span className="ticker-symbol">{symbol}</span>
      <span className="ticker-price">
        {price ? `$${parseFloat(price).toLocaleString("en-US", { maximumFractionDigits: 4 })}` : "—"}
      </span>
    </div>
  )
}

// ── SignalLog ─────────────────────────────────────────────────
export function SignalLog({ signals }) {
  const stateColor = {
    SIGNAL:       "#ef4444",
    CONFIRMATION: "#8b5cf6",
    STOP_HUNT:    "#f97316",
    FAKE_ZONE:    "#f59e0b",
    SETUP:        "#3b82f6",
    WATCHING:     "#6b7280",
  }
  return (
    <div className="panel signal-log">
      <div className="panel-title">📋 SİNYAL GEÇMİŞİ</div>
      {signals.length === 0 ? (
        <div className="empty-log">Henüz kayıt yok (Supabase bağlantısı gerekir)</div>
      ) : (
        <div className="log-list">
          {signals.map((s, i) => (
            <div key={i} className="log-row">
              <span className="log-state"
                style={{ color: stateColor[s.state] || "#6b7280" }}>
                {s.state}
              </span>
              <span className="log-symbol">{s.symbol}</span>
              {s.entry && <span className="log-entry">{s.entry}</span>}
              <span className="log-time">
                {new Date(s.created_at).toLocaleTimeString("tr-TR")}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ZonePanel
