# CV – İş İlanı Eşleştirme Sitesi · Kurulum Rehberi

Bu site; öğrenci ve mezunların CV'lerini yükleyip okulun yayınladığı staj/iş ilanlarıyla
eşleşmesini sağlar. Her ilan için **0–100 uygunluk puanı**, **eşleşen beceriler** ve
**eksik beceriler** gösterilir. İlanları yalnızca **şifreli yönetici paneli** üzerinden siz eklersiniz.

- **Eşleştirme:** Yapay zekâ (Claude) anahtarı girilirse ayrıntılı yorum ve CV önerileri verir.
  Anahtar yoksa ya da yapay zekâ o an yanıt veremezse site otomatik olarak ücretsiz
  **anahtar kelime** yöntemine geçer; site hiçbir zaman durmaz.
- **Gizlilik:** Yüklenen CV'ler hiçbir yere kaydedilmez, yalnızca o an işlenir.
- **Örnek ilanlar:** İlk açılışta "(ÖRNEK İLAN)" yazan 4 deneme ilanı gelir. Gerçek ilanları
  ekledikten sonra bunları yönetim panelinden silin.

---

## 1. Bilgisayarınızda denemek

1. `cv-eslestirme` klasöründeki **`baslat.bat`** dosyasına çift tıklayın.
2. Tarayıcıda `http://127.0.0.1:5000` açılır.
3. Yönetim paneli: `http://127.0.0.1:5000/yonetim` — deneme şifresi: `deneme123`

Yapay zekâyı yerelde denemek için `baslat.bat`'ı çalıştırmadan önce komut isteminde:
```
set ANTHROPIC_API_KEY=sk-ant-...
```

---

## 2. İnternette yayınlamak (ücretsiz)

Önerilen kurulum: **Render** (siteyi çalıştırır) + **Neon** (ilanları kalıcı saklar).
İkisi de ücretsizdir ve kredi kartı gerektirmez.

> **Neden Neon?** Render'ın ücretsiz planında dosyalar kalıcı değildir; site yeniden
> başladığında eklediğiniz ilanlar silinir. Neon ücretsiz bir veritabanıdır ve ilanları kalıcı tutar.

### Adım A — Kodu GitHub'a koyun
1. <https://github.com> adresinde ücretsiz hesap açın.
2. **New repository** → ad: `cv-eslestirme` → **Create**.
3. **uploading an existing file** bağlantısına tıklayıp `cv-eslestirme` klasörünün
   **içindeki tüm dosya ve klasörleri** (`app.py`, `templates`, `static` vb.) sürükleyin → **Commit**.
   (`data` klasörü varsa yüklemeyin.)

### Adım B — Ücretsiz veritabanı (Neon)
1. <https://neon.tech> → GitHub ile giriş → **Create project** (bölge: Europe/Frankfurt).
2. Açılan sayfada **Connection string**'i kopyalayın
   (`postgresql://...` ile başlar). Bunu kimseyle paylaşmayın.

### Adım C — Siteyi yayınlayın (Render)
1. <https://render.com> → GitHub ile giriş.
2. **New + → Blueprint** → `cv-eslestirme` deposunu seçin. (`render.yaml` ayarları otomatik okur.)
3. Sizden şu değerler istenecek:
   | Ad | Ne yazılacak |
   |---|---|
   | `ADMIN_PASSWORD` | Yönetim paneli için güçlü bir şifre |
   | `DATABASE_URL` | Neon'dan kopyaladığınız bağlantı adresi |
   | `ANTHROPIC_API_KEY` | Yapay zekâ anahtarı (aşağıya bakın). İstemiyorsanız boş bırakın. |
4. **Apply** → birkaç dakika sonra siteniz şu gibi bir adreste yayında olur:
   `https://cv-eslestirme.onrender.com`

> Ücretsiz planda site 15 dk kullanılmazsa uyur; ilk ziyaret ~30–50 saniye sürebilir, sonra hızlanır.

### Yapay zekâ anahtarı (Claude API)
1. <https://console.anthropic.com> → hesap açın → **Billing** bölümünden bakiye yükleyin.
2. **API Keys → Create Key** → `sk-ant-...` ile başlayan anahtarı kopyalayıp Render'da
   `ANTHROPIC_API_KEY` alanına yapıştırın (Render → servis → **Environment**).
3. Maliyet: Her CV analizi tek istekte en uygun 12 ilanı birlikte değerlendirir;
   kabaca CV başına birkaç kuruş–birkaç TL düzeyindedir. Console'da aylık harcama
   sınırı koymanızı öneririz (**Settings → Limits**).

---

## 3. Başka sitenize eklemek

### Seçenek 1 — Bağlantı (en kolay)
Okul sitenize bir buton/bağlantı ekleyin:
```html
<a href="https://cv-eslestirme.onrender.com" target="_blank">Kariyer Eşleştirme – CV'ni Yükle</a>
```

### Seçenek 2 — Sayfanın içine gömmek (iframe)
Sitenizin HTML düzenleyicisine (WordPress'te "Özel HTML" bloğu) şunu yapıştırın:
```html
<iframe src="https://cv-eslestirme.onrender.com"
        style="width:100%; height:900px; border:0;"
        title="Kariyer Eşleştirme"></iframe>
```

**Yalnızca kendi sitenizde gömülsün istiyorsanız** Render → Environment'a ekleyin:
`FRAME_ANCESTORS` = `https://www.okulsiteniz.meb.k12.tr` (birden fazlaysa boşlukla ayırın).
Varsayılan `*` değeri tüm sitelere izin verir.

> İpucu: Yönetim panelini gömülü sayfa yerine doğrudan adresinden açın:
> `https://cv-eslestirme.onrender.com/yonetim`

---

## 4. Günlük kullanım (yönetici)
- **Yeni ilan:** Yönetim → **+ Yeni ilan**. Becerileri virgülle yazın
  (ör. `PLC, pnömatik, teknik resim`). Eşleştirme bu listeye göre yapılır.
- **Son başvuru tarihi** geçen ilanlar otomatik olarak öğrencilere gösterilmez.
- **Yayında** kutucuğunu kaldırarak ilanı silmeden gizleyebilirsiniz.
- **Yedek:** Yönetim sayfasının altından ilanları `.json` olarak indirip saklayın.

## 5. İsteğe bağlı ayarlar (Render → Environment)
| Ad | Açıklama |
|---|---|
| `SITE_ADI` | Üst başlıkta görünen ad (varsayılan: Kariyer Eşleştirme) |
| `OKUL_ADI` | Başlığın yanındaki okul adı |
| `FRAME_ANCESTORS` | Siteyi gömebilecek adresler |
| `CLAUDE_MODEL` | Kullanılacak Claude modeli (varsayılan `claude-opus-5-5`) |
