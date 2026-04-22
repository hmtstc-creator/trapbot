const STATE_INFO = {
  WATCHING:     { emoji: "👁", label: "İZLİYOR", desc: "Setup bekleniyor..." },
  SETUP:        { emoji: "📍", label: "SETUP", desc: "Real Zone'a dokunuldu. Tuzak kurulmaya başlıyor." },
  FAKE_ZONE:    { emoji: "🎣", label: "FAKE ZONE", desc: "Düşük hacimli geri çekilme. Retail'lar tuzağa düşüyor." },
  STOP_HUNT:    { emoji: "⏳", label: "STOP HUNT", desc: "Konsolidasyon. Retail stop'ları temizleniyor." },
  CONFIRMATION: { emoji: "🔍", label: "ONAY BEKLENİYOR", desc: "Real Zone'a dönüş. Rejection mumu bekleniyor." },
  SIGNAL:       { emoji: "🔴", label: "SMART SELL!", desc: "Tam onaylı Bearish Sell Trap. İşlem yapılabilir." },
  INSUFFICIENT_DATA: { emoji: "📊", label: "VERİ YETERSİZ", desc: "Daha fazla geçmiş mum verisi gerekiyor." },
}

export default function StateCard({ state, color, data }) {
  const info = STATE_INFO[state] || STATE_INFO.WATCHING

  return (
    <div className="state-card" style={{ borderColor: color }}>
      <div className="state-emoji">{info.emoji}</div>
      <div className="state-body">
        <div className="state-label" style={{ color }}>{info.label}</div>
        <div className="state-desc">{info.desc}</div>
      </div>
      <div className="state-metrics">
        <div className="metric">
          <span className="metric-key">RSI</span>
          <span className="metric-val"
            style={{ color: data?.rsi_in_range ? "#22c55e" : "#ef4444" }}>
            {data?.rsi ?? "—"}
          </span>
        </div>
        <div className="metric">
          <span className="metric-key">ATR</span>
          <span className="metric-val">{data?.atr ?? "—"}</span>
        </div>
        <div className="metric">
          <span className="metric-key">EMA Trend</span>
          <span className="metric-val"
            style={{ color: data?.ema_bearish ? "#22c55e" : "#f59e0b" }}>
            {data?.ema_bearish ? "BEARISH ✓" : "BULLISH"}
          </span>
        </div>
      </div>
    </div>
  )
}
