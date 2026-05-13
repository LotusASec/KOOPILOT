# KOOPILOT

**🔗 Canlı Demo → https://koopilot-production-928b.up.railway.app**

Küçük işletmeler ve üretici kooperatifleri için geliştirilmiş AI destekli operasyon paneli. Ürün stoğu, siparişler, müşteri mesajları ve satış verileri tek bir arayüzde toplanır; Google Gemini entegrasyonu sayesinde işletme sahibi kendi verileri üzerine doğal dilde soru sorabilir.

---

## Motivasyon

Küçük ölçekli üreticiler ve kooperatifler günlük operasyonlarını genellikle not defteri, WhatsApp grupları ve Excel tablolarıyla yönetiyor. Stok takibi unutuluyor, müşteri mesajları kaybolabiliyor, satış verisi hiçbir zaman derli toplu bir yerde durmuyor. KOOPILOT bu soruna pratik, düşük maliyetli ve kullanımı kolay bir çözüm sunmayı amaçlıyor.

---

## Özellikler

**Dashboard**
Günlük sipariş sayısı, kritik stok uyarıları, bekleyen mesajlar ve tahmini ciro tek ekranda. Sayfayı açar açmaz ne durumda olduğunu görürsün.

**Ürünler & Stok**
Tüm ürünlerin fiyat, stok adedi ve durum bilgisi. Kritik seviyeye düşen ürünler renk kodlamasıyla öne çıkar.

**Siparişler**
Son siparişler tarih, müşteri, tutar ve durum bilgisiyle listelenir.

**Müşteri Mesajları & DM**
Gelen kutusu satır satır, okunmamış mesajlar yeşil nokta ile işaretli. Müşteriye tıklayınca özel mesaj ekranı açılır, sohbet akışı buradan devam eder ve tüm yazışma geçmişi saklanır.

**Raporlar**
Sipariş sayısı ve ciro için iki ayrı eğri grafik. Günlük / Haftalık / Aylık görünüm arasında geçiş yapılabilir. Yıl ve ay seçici ile geçmiş dönemlere gidilir.

**AI Asistan**
Google Gemini API ile çalışır. Canlı işletme verisi — ürünler, stoklar, fiyatlar, son 20 sipariş, bekleyen mesajlar — prompt'a eklenerek her soruda güncel bilgi üzerinden cevap üretilir. Konu dışı sorular kibarca reddedilir. Bağlantı kesilirse kendi kendine "bağlantı hatası" mesajı gösterir, uygulama çökmez.

**Ayarlar**
İşletme bilgileri ve tercihler.

---

## Mimari

```
KOOPILOT/
├── app.py                    # Tüm route'lar ve uygulama konfigürasyonu
├── data/
│   ├── db.py                 # psycopg2 bağlantı katmanı (query / execute)
│   ├── mock_data.py          # Veritabanı sorgu fonksiyonları
│   └── seed.py               # Geçmiş sipariş verisi yükleyici (tek seferlik)
├── services/
│   ├── gemini_service.py     # Gemini API entegrasyonu, model otomatik seçimi
│   ├── ai_service.py         # AI cevap akışı
│   ├── dashboard_service.py  # Özet kart hesaplamaları
│   └── insight_service.py    # Günlük içgörü üretimi
├── templates/
│   ├── layout.html           # Ortak sayfa iskeleti (sidebar dahil)
│   ├── dashboard.html
│   ├── products.html
│   ├── orders.html
│   ├── stock.html
│   ├── messages.html
│   ├── dm.html               # Müşteri DM ekranı
│   ├── reports.html
│   └── settings.html
└── static/
    ├── css/style.css
    └── js/
        ├── dashboard.js      # AI chat ve durum rozeti
        ├── dm.js             # Mesaj gönderme
        └── reports.js        # Chart.js grafik mantığı
```

**Katmanlar arası veri akışı:**

```
Tarayıcı → Flask route → data/ sorgu fonksiyonu → Supabase PostgreSQL
                      ↘ services/ → Gemini API
```

Servis fonksiyonları veriyi parametre olarak alır, doğrudan veritabanına dokunmaz. Bu sayede test edilebilirliği korunur ve bağımlılıklar tek yönlü akar.

---

## Teknolojiler

| Katman | Teknoloji |
|---|---|
| Backend | Python 3, Flask 3.1 |
| Veritabanı | PostgreSQL (Supabase) |
| DB Sürücüsü | psycopg2-binary |
| Templating | Jinja2 |
| Frontend | Vanilla JS, CSS |
| Grafikler | Chart.js 4.4 (CDN) |
| AI | Google Gemini API (`google-generativeai`) |
| Konfigürasyon | python-dotenv |
| Üretim Sunucusu | Gunicorn |

---

## Kurulum

**1. Bağımlılıkları yükle**
```bash
pip install -r requirements.txt
```

**2. `.env` dosyası oluştur**

`.env.example`'ı `.env` olarak kopyala, değerleri doldur:

```env
GEMINI_API_KEY=AIza...        # aistudio.google.com/app/apikey
GEMINI_MODEL=                  # boş bırakırsan otomatik seçer
DATABASE_URL=postgresql://postgres.PROJE_ID:SIFRE@aws-0-BOLGE.pooler.supabase.com:5432/postgres
```

> Supabase bağlantısı için → Connect → **Session pooler** → URI kopyala.

**3. Veritabanı tablolarını oluştur**

Supabase SQL Editor'de `data/schema.sql` dosyasındaki sorguları çalıştır.

**4. Geçmiş veriyi yükle (opsiyonel)**
```bash
python3 data/seed.py
```

**5. Çalıştır**
```bash
python3 app.py
```

`http://127.0.0.1:5000`

---

## API Endpoint'leri

| Method | Yol | Açıklama |
|---|---|---|
| GET | `/` | Dashboard |
| GET | `/products` | Ürün listesi |
| GET | `/orders` | Sipariş listesi |
| GET | `/stock` | Stok durumu |
| GET | `/messages` | Mesaj gelen kutusu |
| GET | `/messages/<id>` | DM sohbet ekranı |
| GET | `/reports` | Grafik raporlar |
| GET | `/settings` | Ayarlar |
| POST | `/api/ai/chat` | AI'a soru gönder |
| GET | `/api/ai/status` | Gemini bağlantı durumu |
| POST | `/api/messages/<id>/send` | DM cevabı gönder |
| GET | `/api/reports/data` | Grafik verisi (`granularity`, `year`, `month`) |
| GET | `/health` | Uygulama sağlık kontrolü |

---

## Future Work

**Çok kanallı mesaj yönetimi**
WhatsApp, Instagram DM ve e-posta gibi farklı platformlardan gelen müşteri mesajlarının tek bir gelen kutusunda toplanması ve buradan yönetilmesi.

**AI destekli mesaj yanıtlama**
Gelen müşteri mesajının içeriğine göre Gemini'nin otomatik cevap önerisi üretmesi, kullanıcının tek tıkla onaylayıp göndermesi.

**Gerçek zamanlı bildirimler**
Yeni sipariş veya mesaj geldiğinde anlık bildirim (WebSocket veya push notification).

**Stok yönetimi**
Ürün ekleme, stok güncelleme, kritik seviye eşiği tanımlama ve otomatik uyarı sistemi.

**Sipariş yönetimi**
Sipariş durumu güncelleme, kargo takip numarası girişi, müşteriye otomatik durum bildirimi.

**Gelişmiş raporlama**
En çok satan ürünler, müşteri başına ortalama sipariş değeri, iade oranları gibi metrikler. PDF olarak dışa aktarma.

**Mobil uygulama**
Kooperatif üyelerinin telefon üzerinden stok ve sipariş takibi yapabilmesi.

**Çoklu kullanıcı ve rol yönetimi**
Farklı kooperatif üyeleri için ayrı hesaplar ve yetki seviyeleri (yönetici, üretici, teslimat).
