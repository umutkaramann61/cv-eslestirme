"""Instagram hesabındaki yeni ilan gönderilerini otomatik olarak siteye aktarır.

Resmî "Instagram API with Instagram Login" kullanılır (İşletme / İçerik Üreticisi hesabı gerekir).
- Erişim anahtarı ilk kez INSTAGRAM_TOKEN ortam değişkeninden alınır, sonra veritabanında
  saklanır ve 60 günlük süresi dolmadan kendiliğinden yenilenir.
- Yalnızca açıklamasında ilan kelimeleri geçen gönderiler alınır (IG_ANAHTAR_KELIMELER).
- Aktarılan gönderiler "Onay bekliyor" olarak eklenir; yönetici kontrol edip onaylar.
"""
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import db
import secenekler as S

API = "https://graph.instagram.com"
KONTROL_ARALIGI = int(os.environ.get("IG_KONTROL_DAKIKA", "60")) * 60
YENILEME_GUN = 30
ANAHTAR_KELIMELER = [k.strip() for k in os.environ.get(
    "IG_ANAHTAR_KELIMELER",
    "ilan,aranıyor,arıyoruz,arıyor,alınacak,alım,personel,eleman,stajyer,staj,pozisyon,başvuru,kariyer,iş fırsatı,#işilanı,#isilani",
).split(",") if k.strip()]

_kilit = threading.Lock()


# ---------------------------------------------------------------- yardımcılar
def _kucuk(s):
    return (s or "").replace("İ", "i").replace("I", "ı").lower()


def _get(path, params):
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def token():
    env = os.environ.get("INSTAGRAM_TOKEN", "").strip()
    # Render'da yeni bir anahtar girildiyse onu kullanmaya başla
    if env and env != db.get_setting("ig_env_token"):
        db.set_setting("ig_env_token", env)
        db.set_setting("ig_token", env)
        db.set_setting("ig_token_yenilendi", _simdi().isoformat())
    return db.get_setting("ig_token") or env


def aktif_mi():
    return bool(token())


def durum():
    return {
        "aktif": aktif_mi(),
        "son_kontrol": db.get_setting("ig_son_kontrol"),
        "son_hata": db.get_setting("ig_son_hata"),
        "son_eklenen": db.get_setting("ig_son_eklenen", "0"),
    }


def _simdi():
    return datetime.now(timezone.utc)


def _yenile_gerekirse():
    """Anahtarı 30 günde bir yenile (Instagram anahtarları 60 gün geçerli)."""
    t = token()
    son = db.get_setting("ig_token_yenilendi")
    if son:
        try:
            if (_simdi() - datetime.fromisoformat(son)).days < YENILEME_GUN:
                return
        except ValueError:
            pass
    else:
        db.set_setting("ig_token_yenilendi", _simdi().isoformat())
        return
    try:
        yeni = _get("refresh_access_token", {"grant_type": "ig_refresh_token", "access_token": t})
        if yeni.get("access_token"):
            db.set_setting("ig_token", yeni["access_token"])
            db.set_setting("ig_token_yenilendi", _simdi().isoformat())
    except urllib.error.URLError:
        pass  # Bir sonraki kontrolde tekrar denenir


# ---------------------------------------------------------------- açıklamadan alan çıkarma
UZMANLIK_KELIMELERI = {
    "PLC Programlama": ["plc", "tia portal", "step 7", "s7-1200", "s7-1500", "siemens"],
    "HMI Programlama": ["hmi", "operatör paneli", "wincc"],
    "SCADA Programlama": ["scada"],
    "Mekanik Tasarım": ["mekanik tasarım", "solidworks", "autocad", "catia", "inventor"],
    "Robot Programlama": ["robot", "kuka", "fanuc", "abb", "yaskawa"],
    "Gömülü Sistem PCB Tasarım": ["gömülü", "pcb", "embedded", "mikrodenetleyici"],
    "Pano Tasarımı": ["pano tasarım", "eplan"],
    "Proje Mühendisliği": ["proje mühendis"],
    "Satış Mühendisliği": ["satış mühendis"],
    "Bakım Mühendisliği": ["bakım", "arıza", "maintenance"],
    "Pano Montajı": ["pano montaj", "kablaj", "pano kablo"],
}


def _kelime_var(metin, kelime):
    return re.search(r"(?<![a-zçğıöşü0-9])" + re.escape(kelime), metin) is not None


def ilan_mi(caption):
    m = _kucuk(caption)
    return any(_kelime_var(m, _kucuk(k)) for k in ANAHTAR_KELIMELER)


def alanlari_cikar(caption):
    """Gönderi açıklamasından il, ilçe, uzmanlık vb. tahmin et (yönetici sonra düzeltir)."""
    m = _kucuk(caption)
    d = {"il": "", "ilce": "", "uzmanliklar": [], "robot_markalari": [], "surucu_belgesi": 0, "min_deneyim": 0}
    for il in S.ILLER:
        if _kelime_var(m, _kucuk(il)):
            d["il"] = il
            break
    for il, ilceler in S.ILCELER.items():
        for ilce in ilceler:
            if _kelime_var(m, _kucuk(ilce)):
                d["ilce"] = ilce
                d["il"] = d["il"] or il
                break
        if d["ilce"]:
            break
    for alan, kelimeler in UZMANLIK_KELIMELERI.items():
        if any(_kelime_var(m, k) for k in kelimeler):
            d["uzmanliklar"].append(alan)
    d["robot_markalari"] = [x for x in S.ROBOT_MARKALARI if _kelime_var(m, _kucuk(x))]
    if "ehliyet" in m or "sürücü belgesi" in m:
        d["surucu_belgesi"] = 1
    yil = re.search(r"(\d+)\s*(?:\+|yıl|sene)", m)
    if yil and int(yil.group(1)) <= 15 and ("deneyim" in m or "tecrübe" in m):
        d["min_deneyim"] = min(int(yil.group(1)), 5)
    return d


GENEL_BASLIKLAR = {"iş ilanı", "is ilani", "ilan", "ilanı", "personel alımı", "eleman aranıyor",
                   "iş fırsatı", "kariyer fırsatı", "duyuru", "staj ilanı"}


def _baslik(caption):
    for satir in (caption or "").splitlines():
        s = re.sub(r"[#@]\S+", "", satir)
        s = re.sub(r"[^\w\s'’.,()/&+-]", "", s).strip(" \t-–•*.,")
        if len(s) >= 4 and _kucuk(s).strip(" !:") not in GENEL_BASLIKLAR:
            return s[:90]
    return "Instagram ilanı"


# ---------------------------------------------------------------- aktarım
def cek(zorla=False):
    """Yeni gönderileri çek. Dönüş: eklenen ilan sayısı (hata olursa None)."""
    if not aktif_mi():
        return None
    if not _kilit.acquire(blocking=False):
        return None
    try:
        son = db.get_setting("ig_son_kontrol_ts")
        if not zorla and son and time.time() - float(son) < KONTROL_ARALIGI:
            return 0
        db.set_setting("ig_son_kontrol_ts", time.time())
        db.set_setting("ig_son_kontrol", datetime.now().strftime("%d.%m.%Y %H:%M"))
        _yenile_gerekirse()
        try:
            veri = _get("me/media", {"fields": "id,caption,permalink,timestamp,media_type",
                                     "limit": 25, "access_token": token()})
        except urllib.error.HTTPError as e:
            try:
                mesaj = json.loads(e.read().decode("utf-8")).get("error", {}).get("message", "")
            except Exception:
                mesaj = ""
            db.set_setting("ig_son_hata", f"Instagram hatası {e.code}: {mesaj}"[:300])
            return None
        except urllib.error.URLError as e:
            db.set_setting("ig_son_hata", f"Bağlantı hatası: {e.reason}"[:300])
            return None

        gorulen = db.instagram_links()
        eklenen = 0
        yeni_gorulen = []
        for g in veri.get("data", []):
            link = g.get("permalink", "")
            m = re.search(r"instagram\.com/(?:[\w.]+/)?(p|reel|tv)/([\w-]+)", link)
            if not m:
                continue
            link = f"https://www.instagram.com/{m.group(1)}/{m.group(2)}/"
            if link in gorulen:
                continue
            yeni_gorulen.append(link)
            caption = g.get("caption", "") or ""
            if not ilan_mi(caption):
                continue
            alanlar = alanlari_cikar(caption)
            db.add_job({
                "firma": "Instagram ilanı", "iletisim": "Instagram gönderisi",
                "baslik": _baslik(caption), "calisma_turu": "Tam zamanlı",
                "il": alanlar["il"], "ilce": alanlar["ilce"], "sektor": "",
                "mezuniyet_alanlari": [], "uzmanliklar": alanlar["uzmanliklar"],
                "robot_markalari": alanlar["robot_markalari"], "min_deneyim": alanlar["min_deneyim"],
                "surucu_belgesi": alanlar["surucu_belgesi"], "ilan_detayi": caption[:3000],
                "basvuru": link, "son_tarih": "", "instagram": link,
            }, durum="bekliyor")
            eklenen += 1
        if yeni_gorulen:
            eski = [x for x in db.get_setting("ig_gorulen").split("|") if x]
            db.set_setting("ig_gorulen", "|".join((eski + yeni_gorulen)[-500:]))
        db.set_setting("ig_son_hata", "")
        db.set_setting("ig_son_eklenen", eklenen)
        return eklenen
    finally:
        _kilit.release()


def arka_planda_kontrol():
    """Sayfa ziyaretlerinde çağrılır; süresi geldiyse arka planda çeker (siteyi yavaşlatmaz)."""
    if not aktif_mi():
        return
    son = db.get_setting("ig_son_kontrol_ts")
    if son and time.time() - float(son) < KONTROL_ARALIGI:
        return
    threading.Thread(target=_guvenli_cek, daemon=True).start()


def _guvenli_cek():
    try:
        cek()
    except Exception as e:  # Arka plan hatası siteyi düşürmesin
        try:
            db.set_setting("ig_son_hata", f"Beklenmeyen hata: {e}"[:300])
        except Exception:
            pass
