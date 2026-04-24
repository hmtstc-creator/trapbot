import { useState, useEffect, useCallback } from "react"
import Dashboard from "./pages/Dashboard"
import "./index.css"

const API = import.meta.env.VITE_API_URL || "https://trapbot-backend.onrender.com"

export default function App() {
  const [symbol, setSymbol]   = useState("BTCUSDT")
  const [interval, setInterval] = useState("1h")
  const [data, setData]       = useState(null)
  const [price, setPrice]     = useState(null)
  const [balance, setBalance] = useState(null)
  const [loading, setLoading] = useState(false)
  const [signals, setSignals] = useState([])
  const [candles, setCandles] = useState([])
  const [error, setError]     = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)

  const fetchAll = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [priceRes, analyzeRes, signalsRes, candlesRes] = await Promise.all([
        fetch(`${API}/api/price/${symbol}`).then(r => r.json()),
        fetch(`${API}/api/analyze/${symbol}?interval=${interval}`).then(r => r.json()),
        fetch(`${API}/api/signals?limit=15`).then(r => r.json()),
        fetch(`${API}/api/candles/${symbol}?interval=${interval}&limit=60`).then(r => r.json()),
      ])
      setPrice(priceRes.price)
      setData(analyzeRes)
      setSignals(signalsRes.signals || [])
      setCandles(candlesRes.candles || [])
      setLastUpdate(new Date())
    } catch (e) {
      setError("API bağlantısı kurulamadı. Backend çalışıyor mu?")
    } finally {
      setLoading(false)
    }
  }, [symbol, interval])

  const fetchBalance = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/balance`)
      const d   = await res.json()
      setBalance(d)
    } catch {}
  }, [])

  const executeTrade = async (side, quantity) => {
    try {
      const res = await fetch(`${API}/api/trade`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol, side, quantity: parseFloat(quantity) })
      })
      const result = await res.json()
      if (result.orderId) {
        await fetchAll()
        await fetchBalance()
        return { success: true, data: result }
      }
      return { success: false, error: result.detail || "Trade failed" }
    } catch (e) {
      return { success: false, error: e.message }
    }
  }

  useEffect(() => {
    fetchAll()
    fetchBalance()
    const interval_id = setInterval(() => {
      fetchAll()
      fetchBalance()
    }, 30000) // auto refresh every 30s
    return () => clearInterval(interval_id)
  }, [fetchAll, fetchBalance])

  return (
    <Dashboard
      symbol={symbol}
      setSymbol={setSymbol}
      interval={interval}
      setInterval={setInterval}
      data={data}
      price={price}
      balance={balance}
      loading={loading}
      signals={signals}
      candles={candles}
      error={error}
      lastUpdate={lastUpdate}
      onRefresh={fetchAll}
      onTrade={executeTrade}
    />
  )
}
