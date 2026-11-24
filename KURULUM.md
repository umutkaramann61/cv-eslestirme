# İş Arayan – İşletme Eşleştirme Sitesi · Kurulum Rehberi

Sitenin iki bölümü var:

- **İşletme (İlan Ver):** Firma; il, ilçe, sektör, aranan uzmanlık alanları (PLC, HMI, SCADA,
  Robot Programlama + marka…), en az deneyim, mezuniyet alanları, sürücü belgesi ve ilan detayını girer.
  İlan **onay bekliyor** olarak kaydedilir; siz yönetim panelinden **Onayla** deyince yayına girer.
- **İş Arayan (İş Arıyorum):** İl, ilçe, sektör (veya Tümü), mezuniyet alanı, en fazla 3 deneyim
  (alan + giriş/çıkış tarihi; robot için marka) ve sürücü belgesini girer. Aynı ildeki ilanlar
  **0–100 uygunluk puanıyla**, uygun ve eksik yönleriyle listelenir.

- **Puanlama:** Uzmanlık 45 · Deneyim süresi 20 · Mezuniyet 15 · Sürücü belgesi 10 · Aynı ilçe 10.
- **Seçim listeleri** (iller, ilçeler, sektörler, mezuniyet ve uzmanlık alanları) `secenekler.py`
  dosyasındadır; değiştirmek için o dosyayı düzenlemek yeterlidir.
- **Gizlilik:** İş arayan bilgileri hiçbir yere kaydedilmez, yalnızca o an işlenir.
- **Örnek ilanlar:** İlk açılışta "(ÖRNEK İLAN)" yazan 4 deneme ilanı gelir. Gerçek ilanlar
  geldikten sonra bunları yönetim panelinden silin.

---

## 1. Bilgisayarınızda denemek

1. `cv-eslestirme` klasöründeki **`baslat.bat`** dosyasına çift tıklayın.
2. Tarayıcıda `http://127.0.0.1:5000` açılır.
3. Yönetim paneli: `http://127.0.0.1:5000/yonetim` — deneme şifresi: `deneme123`


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
4. **Apply** → birkaç dakika sonra siteniz şu gibi bir adreste yayında olur:
   `https://cv-eslestirme.onrender.com`

> Ücretsiz planda site 15 dk kullanılmazsa uyur; ilk ziyaret ~30–50 saniye sürebilir, sonra hızlanır.

---

## 3. Başka sitenize eklemek

### Seçenek 1 — Bağlantı (en kolay)
Okul sitenize bir buton/bağlantı ekleyin:
```html
<a href="https://cv-eslestirme.onrender.com" target="_blank">Kariyer Eşleştirme</a>
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
- **Onay bekleyen ilanlar** yönetim sayfasında en üstte sarı etiketle görünür: Düzenle ile inceleyin, **Onayla** ile yayına alın.
- **Yeni ilan:** Yönetim → **+ Yeni ilan** (yöneticinin eklediği ilan doğrudan yayına girer).
- **Son başvuru tarihi** geçen ilanlar otomatik olarak öğrencilere gösterilmez.
- **Yayından kaldır** ile ilanı silmeden gizleyebilirsiniz.
- **Yedek:** Yönetim sayfasının altından ilanları `.json` olarak indirip saklayın.

## 5. İsteğe bağlı ayarlar (Render → Environment)
| Ad | Açıklama |
|---|---|
| `SITE_ADI` | Üst başlıkta görünen ad (varsayılan: Kariyer Eşleştirme) |
| `OKUL_ADI` | Başlığın yanındaki okul adı |
| `FRAME_ANCESTORS` | Siteyi gömebilecek adresler |
