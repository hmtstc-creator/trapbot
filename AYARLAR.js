// ╔══════════════════════════════════════════════════════════════╗
// ║          TRAPBOT — TEK AYAR DOSYASI                         ║
// ║  Sadece bu dosyayı doldur, başka hiçbir yere dokunma!       ║
// ╚══════════════════════════════════════════════════════════════╝
//
// ADIM 1: Bu dosyayı bir metin editörüyle aç (Notepad bile olur)
// ADIM 2: Aşağıdaki boş tırnakları doldur
// ADIM 3: Kaydet — bitti!
//
// Nereden alacağını her satırın yanında yazdım ↓

const TRAPBOT_CONFIG = {

  // ─── RENDER.COM BACKEND URL ───────────────────────────────────
  // Render.com → Dashboard → trapbot servisi → URL kısmı
  // Örnek: "https://trapbot.onrender.com"
  BACKEND_URL: "trapbot-backend.up.railway.app",

  // ─── BİNANCE API ──────────────────────────────────────────────
  // Testnet için: testnet.binance.vision → Login → Generate Key
  // Gerçek için:  binance.com → API Management → Create API
  BINANCE_API_KEY:    "xojOtAddR2wiZn8Ejf1ApM7vSXsG1g8YN9T59mciwNsvqgIwG08b4MqJTqKVAbIG",
  BINANCE_API_SECRET: "ccSwg8IAmqzeSzpLdbX7P1keFvY9hPRuLTk9t3Ohv5W0WnjggIxOaC3nDsZbuoHl",
  BINANCE_TESTNET:    true,   // true = testnet (güvenli), false = gerçek para

  // ─── SUPABASE VERİTABANI ──────────────────────────────────────
  // supabase.com → Projen → Settings → API
  // "Project URL" ve "anon public" key
  SUPABASE_URL: "https://gdwinajwxstssbtjgxjw.supabase.co",
  SUPABASE_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdkd2luYWp3eHN0c3NidGpneGp3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY4NDM1MzAsImV4cCI6MjA5MjQxOTUzMH0.o1EhzuW1L8xJ1A5nXWJukcYBUq-Y8t9CtTxmWNeaXY4",

};

// ── Aşağısına dokunma ──────────────────────────────────────────
if (typeof module !== "undefined") module.exports = TRAPBOT_CONFIG;
