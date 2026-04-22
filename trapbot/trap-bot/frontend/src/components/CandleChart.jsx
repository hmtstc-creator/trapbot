import { useMemo } from "react"

export default function CandleChart({ candles, data }) {
  const W = 700, H = 280
  const PAD = { t: 20, r: 10, b: 30, l: 60 }
  const chartW = W - PAD.l - PAD.r
  const chartH = H - PAD.t - PAD.b

  const chart = useMemo(() => {
    if (!candles || candles.length === 0) return null
    const shown = candles.slice(-60)
    const highs  = shown.map(c => c.high)
    const lows   = shown.map(c => c.low)
    const minP   = Math.min(...lows)
    const maxP   = Math.max(...highs)
    const range  = maxP - minP || 1
    const candleW = chartW / shown.length

    const px = i => PAD.l + i * candleW + candleW * 0.1
    const py = v => PAD.t + chartH - ((v - minP) / range) * chartH
    const cw = candleW * 0.8

    return { shown, minP, maxP, range, px, py, cw, candleW }
  }, [candles, chartW, chartH])

  if (!chart) return (
    <div className="panel chart-panel">
      <div className="panel-title">📊 GRAFİK</div>
      <div className="chart-empty">Veri yükleniyor...</div>
    </div>
  )

  const { shown, minP, maxP, range, px, py, cw } = chart

  // Zone rectangles mapped to price axis
  const zoneRect = (high, low, color, opacity) => {
    if (!data || !high || !low) return null
    const y1 = py(Math.min(high, maxP))
    const y2 = py(Math.max(low,  minP))
    return (
      <rect x={PAD.l} y={y1} width={chartW} height={Math.max(y2 - y1, 1)}
        fill={color} opacity={opacity} />
    )
  }

  // Y-axis price labels
  const ticks = 5
  const yTicks = Array.from({ length: ticks }, (_, i) => {
    const val = minP + (range / (ticks - 1)) * i
    return { val, y: py(val) }
  })

  return (
    <div className="panel chart-panel">
      <div className="panel-title">📊 {shown.length > 0 ? shown[0].open_time ? "OHLCV GRAFİK" : "GRAFİK" : "GRAFİK"}
        <span className="chart-count"> — son {shown.length} mum</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" preserveAspectRatio="xMidYMid meet">
        {/* Background */}
        <rect width={W} height={H} fill="#0a0e1a" />
        <rect x={PAD.l} y={PAD.t} width={chartW} height={chartH} fill="#0d1225" />

        {/* Grid lines */}
        {yTicks.map((t, i) => (
          <g key={i}>
            <line x1={PAD.l} y1={t.y} x2={PAD.l + chartW} y2={t.y}
              stroke="#1e2a4a" strokeWidth="0.5" />
            <text x={PAD.l - 4} y={t.y + 4} textAnchor="end"
              fill="#4a5578" fontSize="9" fontFamily="'Courier New', monospace">
              {t.val.toLocaleString("en", { maximumFractionDigits: 0 })}
            </text>
          </g>
        ))}

        {/* Zone overlays */}
        {data && zoneRect(data.real_zone_high, data.real_zone_low, "#ef4444", 0.12)}
        {data && zoneRect(data.fake_zone_high, data.fake_zone_low, "#f59e0b", 0.10)}

        {/* POC line */}
        {data?.poc && (
          <line x1={PAD.l} x2={PAD.l + chartW}
            y1={py(data.poc)} y2={py(data.poc)}
            stroke="#eab308" strokeWidth="1" strokeDasharray="4 3" opacity="0.8" />
        )}

        {/* EMA lines */}
        {data?.ema50 && (() => {
          const y = py(data.ema50)
          return <line x1={PAD.l} x2={PAD.l + chartW} y1={y} y2={y}
            stroke="#f97316" strokeWidth="1" opacity="0.7" />
        })()}
        {data?.ema200 && (() => {
          const y = py(data.ema200)
          return <line x1={PAD.l} x2={PAD.l + chartW} y1={y} y2={y}
            stroke="#ef4444" strokeWidth="1.5" opacity="0.6" />
        })()}

        {/* Candles */}
        {shown.map((c, i) => {
          const bullish = c.close >= c.open
          const color   = bullish ? "#22c55e" : "#ef4444"
          const bodyTop = py(Math.max(c.open, c.close))
          const bodyBot = py(Math.min(c.open, c.close))
          const bodyH   = Math.max(bodyBot - bodyTop, 1)
          const wickX   = px(i) + cw / 2

          return (
            <g key={i}>
              {/* Wick */}
              <line x1={wickX} x2={wickX} y1={py(c.high)} y2={py(c.low)}
                stroke={color} strokeWidth="1" opacity="0.8" />
              {/* Body */}
              <rect x={px(i)} y={bodyTop} width={cw} height={bodyH}
                fill={bullish ? "#166534" : "#7f1d1d"}
                stroke={color} strokeWidth="0.5" rx="0.5" />
            </g>
          )
        })}

        {/* Zone labels */}
        {data?.real_zone_high && (
          <text x={PAD.l + 4} y={py(data.real_zone_high) - 3}
            fill="#ef4444" fontSize="8" fontFamily="monospace" opacity="0.9">
            REAL ZONE
          </text>
        )}
        {data?.fake_zone_high && (
          <text x={PAD.l + 4} y={py(data.fake_zone_high) - 3}
            fill="#f59e0b" fontSize="8" fontFamily="monospace" opacity="0.9">
            FAKE ZONE
          </text>
        )}
      </svg>

      {/* Legend */}
      <div className="chart-legend">
        <span style={{color:"#ef4444"}}>█ Real Zone</span>
        <span style={{color:"#f59e0b"}}>█ Fake Zone</span>
        <span style={{color:"#eab308"}}>── POC</span>
        <span style={{color:"#f97316"}}>── EMA50</span>
        <span style={{color:"#ef4444"}}>── EMA200</span>
      </div>
    </div>
  )
}
