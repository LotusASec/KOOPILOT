# KOOPILOT

KOOPILOT, küçük işletmeler ve üretici kooperatifleri için geliştirilen AI destekli operasyon panelidir. Ürün, stok, sipariş ve müşteri mesajlarını tek panelde takip etmenizi sağlar; Google Gemini API ile gerçek zamanlı işletme verisi üzerinden doğal dilde sorularınızı yanıtlar.

## Problem

Küçük işletmeler ve kooperatifler ürün, stok, sipariş ve müşteri mesajlarını çoğunlukla manuel olarak takip eder. Bu durum zaman kaybına, stok hatalarına ve müşteri mesajlarının geç cevaplanmasına neden olabilir.

## Çözüm

KOOPILOT, işletme sahibinin günlük operasyonlarını tek panelden görmesini sağlar. Stok seviyeleri, siparişler, müşteri mesajları, satış grafikleri ve günlük özetler tek bir yerde toplanır. AI Asistan bölümü Google Gemini API'sini kullanarak işletme verisi üzerinden doğal dilde soruları yanıtlar.

## Özellikler

### Dashboard
- Bugünkü sipariş sayısı, kritik stok, bekleyen mesaj ve tahmini satış için özet kartlar
- Ürün ve stok durumu tablosu
- Son siparişler tablosu
- Günlük içgörüler (stok uyarıları, bekleyen mesaj sayısı, satış özeti)
- AI Asistan chat kutusu (Gemini destekli)

### Ürünler
- Tüm ürünlerin listesi, stok adetleri, fiyatları ve durum rozetleri

### Siparişler
- Son 50 sipariş, tarih sütunu ile birlikte
- Sipariş no, müşteri, tutar ve durum bilgisi

### Stok
- Toplam ürün, kritik stok, stokta yok ve toplam adet özet kartları
- Ürün bazında detaylı stok tablosu

### Müşteri Mesajları
- WhatsApp tarzı satır tabanlı gelen kutusu
- Okunmamış mesajlar için yeşil nokta göstergesi
- Müşteriye tıklayınca DM (özel mesaj) sayfası açılır
- DM sayfasında sohbet kabarcıkları (müşteri solda, sahip sağda) + cevap yazma kutusu

### Raporlar
- Sipariş sayısı ve ciro için iki yan yana eğri (line) grafik
- Görünüm geçişi: Günlük / Haftalık / Aylık
- Yıl ve ay seçici ile geçmiş dönemlere navigasyon
- Chart.js (CDN) ile interaktif grafikler, hover tooltip ve toplam değer rozeti

### Ayarlar
- İşletme bilgileri (isim, e-posta, telefon)
- Tercihler (kritik stok uyarıları, yeni mesaj bildirimi, günlük rapor e-postası, para birimi)

### AI Asistan
- **Google Gemini API** entegrasyonu (ücretsiz tier)
- Başlangıçta `list_models()` ile otomatik en iyi modeli seçer (`gemini-2.5-flash` öncelikli, model deprecate olsa da otomatik yenisine geçer)
- Gerçek zamanlı işletme verisini prompt'a ekler: ürünler (stok + fiyat + durum), son 20 sipariş, bekleyen mesajlar
- Konu dışı sorulara (hava durumu, matematik, genel kültür, vs.) sabit red mesajı verir
- Bağlantı / quota / model hatalarında kullanıcıya **"Bağlantı hatası"** mesajı gösterir
- Dashboard'da canlı durum rozeti: **"Gemini bağlı"** (yeşil) / **"Bağlantı yok"** (turuncu, hover'da sebep tooltip'i)

## Stack

- **Backend:** Python 3.x, Flask 3.1
- **Templating:** Jinja2
- **Frontend:** Vanilla JavaScript, CSS (özel tasarım, bej + koyu yeşil palet)
- **Grafikler:** Chart.js 4.4 (CDN)
- **AI:** Google Generative AI SDK (`google-generativeai`)
- **Yapılandırma:** `python-dotenv` ile `.env` yönetimi

## Proje Yapısı

```
KOOPILOT/
├── app.py                    # Flask uygulaması, tüm route'lar
├── requirements.txt          # Python bağımlılıkları
├── .env.example              # Ortam değişkenleri şablonu (.env olarak kopyalayın)
├── .gitignore
├── README.md
│
├── data/
│   └── mock_data.py          # Ürün, sipariş, konuşma mock verisi
│                             # (1 yıllık deterministik sipariş geçmişi)
│
├── services/
│   ├── ai_service.py         # AI cevap akışı (Gemini wrapper)
│   ├── gemini_service.py     # Google Gemini API entegrasyonu
│   ├── dashboard_service.py  # Dashboard özet hesaplamaları
│   └── insight_service.py    # Günlük içgörü üretimi
│
├── templates/
│   ├── layout.html           # Base template (sidebar + main wrapper)
│   ├── dashboard.html        # Dashboard
│   ├── products.html         # Ürünler
│   ├── orders.html           # Siparişler
│   ├── stock.html            # Stok
│   ├── messages.html         # Müşteri mesajları (inbox)
│   ├── dm.html               # DM sohbet sayfası
│   ├── reports.html          # Raporlar (grafikler)
│   └── settings.html         # Ayarlar
│
└── static/
    ├── css/
    │   └── style.css         # Tüm stil dosyası
    └── js/
        ├── dashboard.js      # AI chat + durum rozeti
        ├── dm.js             # DM gönderme
        └── reports.js        # Chart.js grafikler + filtreler
```

## Kurulum

### 1. Bağımlılıkları yükle

```bash
pip install -r requirements.txt
```

### 2. Gemini API key al

[Google AI Studio](https://aistudio.google.com/app/apikey) → **Create API key** → kopyala. Ücretsizdir.

### 3. `.env` dosyasını oluştur

`.env.example`'ı `.env` olarak kopyala ve key'ini yapıştır:

```env
GEMINI_API_KEY=AIza...senin_key_in
GEMINI_MODEL=
```

> **Notlar:**
> - `=` etrafında boşluk yok, key etrafında tırnak yok.
> - `GEMINI_MODEL` boş bırakılırsa kod otomatik olarak kullanılabilir en iyi modeli seçer (önerilen).
> - `.env` zaten `.gitignore` içinde, repoya pushlanmaz.

### 4. Çalıştır

```bash
python3 app.py
```

Tarayıcıda [http://127.0.0.1:5000](http://127.0.0.1:5000) açılır.

## Route'lar

| Yöntem | Yol | Açıklama |
|---|---|---|
| GET  | `/` | Dashboard |
| GET  | `/products` | Ürünler listesi |
| GET  | `/orders` | Siparişler (son 50) |
| GET  | `/stock` | Stok durumu |
| GET  | `/messages` | Mesaj gelen kutusu |
| GET  | `/messages/<id>` | DM sohbet sayfası |
| GET  | `/reports` | Raporlar (grafikler) |
| GET  | `/settings` | Ayarlar |
| POST | `/api/ai/chat` | AI chat (Gemini'ye soru) |
| GET  | `/api/ai/status` | AI bağlantı durumu (debug) |
| POST | `/api/messages/<id>/send` | DM'de cevap gönder |
| GET  | `/api/reports/data` | Grafik için aggregate veri (params: `granularity`, `year`, `month`) |

## AI Davranışı

| Soru Tipi | Cevap |
|---|---|
| Ürün / stok / fiyat sorusu | Gemini canlı veriden cevaplar |
| Sipariş sorusu | Gemini son 20 siparişten cevaplar |
| Bekleyen mesaj sorusu | Gemini okunmamış mesajları kullanır |
| Konu dışı (hava, matematik, genel kültür) | Sabit red: *"Üzgünüm, sadece işletmenizdeki ürün, stok, sipariş ve müşteri mesajları hakkında yardımcı olabilirim."* |
| Gemini'ye ulaşılamıyor | Kırmızı kenarlı: *"Bağlantı hatası: AI asistanına şu an ulaşılamıyor..."* |

## Sorun Giderme

**AI Asistan rozeti turuncu / "Bağlantı yok":**
- `.env` dosyası kayıtlı mı? VS Code'da kaydedilmemiş dosya sekmesinde **●** simgesi olur — `Cmd+S` ile kaydet.
- `python3 app.py` sonrası `.env` değişikliklerini almak için Flask'i tam yeniden başlat (Ctrl+C → tekrar başlat).
- `http://127.0.0.1:5000/api/ai/status` → JSON'daki `reason` alanı tam nedeni söyler.
- Terminal'de `[GEMINI] ...` log satırları hata detaylarını verir.

**`pip install` UTF-16 hatası:**
- `requirements.txt` UTF-8 olmalı. Bozulursa şu komutla yeniden yaz:
  ```bash
  python3 -c "open('requirements.txt','w',encoding='utf-8').write(open('requirements.txt','rb').read().decode('utf-16','ignore'))"
  ```

**Model 404 hatası (`gemini-1.5-flash is not found`):**
- Google bazı modelleri zaman zaman emekli ediyor. `.env` içinde `GEMINI_MODEL=` boş bırak, kod otomatik yenisini bulur.
