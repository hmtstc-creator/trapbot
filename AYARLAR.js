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
  BACKEND_URL: "https://trapbot-backend.onrender.com",

  // ─── BİNANCE API ──────────────────────────────────────────────
  // Testnet için: testnet.binance.vision → Login → Generate Key
  // Gerçek için:  binance.com → API Management → Create API
  BINANCE_API_KEY:    "3aPb7S2xkF49MnWArfGrnUvGI98tAgd5u9h1AFJ7G9ZGptS5WzaQTjwDsbcc8z6Y",
  BINANCE_API_SECRET: "fmzvqZEzS0Zzvssvpa7KnuzZnv1J4B7HtoNj4L5ScL4mtNRwnyYf5LwLgw23A5g5",
  BINANCE_TESTNET:    true,   // true = testnet (güvenli), false = gerçek para

  // ─── SUPABASE VERİTABANI ──────────────────────────────────────
  // supabase.com → Projen → Settings → API
  // "Project URL" ve "anon public" key
  SUPABASE_URL: "https://gdwinajwxstssbtjgxjw.supabase.co",
  SUPABASE_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdkd2luYWp3eHN0c3NidGpneGp3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY4NDM1MzAsImV4cCI6MjA5MjQxOTUzMH0.o1EhzuW1L8xJ1A5nXWJukcYBUq-Y8t9CtTxmWNeaXY4",

};

// ── Aşağısına dokunma ──────────────────────────────────────────
if (typeof module !== "undefined") module.exports = TRAPBOT_CONFIG;
