"""İş arayan bilgileri ile işletme ilanlarını eşleştirir.

Puan (100 üzerinden):
  Uzmanlık alanları ........ 45  (ilanın aradığı alanlarda deneyim var mı; robot markası dahil)
  Deneyim süresi ........... 20  (ilgili alanlardaki toplam süre / istenen en az süre)
  Mezuniyet alanı .......... 15
  Sürücü belgesi ........... 10
  İlçe ..................... 10  (aynı ilçe ise)
Filtreler: il aynı olmalı; iş arayan sektör seçtiyse sektör aynı olmalı ("Tümü" ise hepsi).
"""
from datetime import date

from secenekler import MAKS_DENEYIM


def _months(giris, cikis):
    """'YYYY-MM' biçimindeki iki tarih arasındaki ay sayısı (çıkış boşsa bugün)."""
    try:
        gy, gm = map(int, giris.split("-")[:2])
    except (ValueError, AttributeError):
        return 0
    if cikis:
        try:
            cy, cm = map(int, cikis.split("-")[:2])
        except ValueError:
            return 0
    else:
        t = date.today()
        cy, cm = t.year, t.month
    return max(0, (cy - gy) * 12 + (cm - gm) + 1)


def parse_seeker(form):
    """İş arayan formundan sözlük üret. Hatalar listesi de döner."""
    s = {
        "il": form.get("il", "").strip(),
        "ilce": form.get("ilce", "").strip(),
        "sektor": form.get("sektor", "").strip(),  # boş = Tümü
        "mezuniyet": form.get("mezuniyet", "").strip(),
        "surucu_belgesi": form.get("surucu_belgesi") in ("1", "on"),
        "deneyimler": [],
    }
    hatalar = []
    if not s["il"]:
        hatalar.append("Lütfen il seçin.")
    for i in range(1, MAKS_DENEYIM + 1):
        alan = form.get(f"d{i}_alan", "").strip()
        if not alan:
            continue
        giris = form.get(f"d{i}_giris", "").strip()
        cikis = form.get(f"d{i}_cikis", "").strip()
        if not giris:
            hatalar.append(f"{i}. deneyim için giriş tarihini girin.")
            continue
        if cikis and cikis < giris:
            hatalar.append(f"{i}. deneyimde çıkış tarihi girişten önce olamaz.")
            continue
        markalar = form.getlist(f"d{i}_marka") if hasattr(form, "getlist") else form.get(f"d{i}_marka", [])
        s["deneyimler"].append({"alan": alan, "giris": giris, "cikis": cikis,
                                "ay": _months(giris, cikis), "markalar": list(markalar)})
    return s, hatalar


def _yil_metni(ay):
    if ay < 12:
        return f"{ay} ay"
    y, a = divmod(ay, 12)
    return f"{y} yıl" + (f" {a} ay" if a else "")


def score(seeker, job):
    eslesen, eksik = [], []
    deneyim_ay = {}
    deneyim_marka = {}
    for d in seeker["deneyimler"]:
        deneyim_ay[d["alan"]] = deneyim_ay.get(d["alan"], 0) + d["ay"]
        deneyim_marka.setdefault(d["alan"], set()).update(d["markalar"])

    # 1) Uzmanlık (45)
    istenen = job.get("uzmanliklar") or []
    if istenen:
        puan_alan = 0.0
        for alan in istenen:
            if alan in deneyim_ay:
                if alan == "Robot Programlama" and job.get("robot_markalari"):
                    ortak = set(job["robot_markalari"]) & deneyim_marka.get(alan, set())
                    if ortak:
                        puan_alan += 1
                        eslesen.append(f"{alan} ({', '.join(sorted(ortak))})")
                    else:
                        puan_alan += 0.5
                        eslesen.append(alan)
                        eksik.append("Robot markası: " + " / ".join(job["robot_markalari"]))
                else:
                    puan_alan += 1
                    eslesen.append(alan)
            else:
                eksik.append(alan)
        uzmanlik = 45 * puan_alan / len(istenen)
    else:
        uzmanlik = 45

    # 2) Deneyim süresi (20)
    ilgili_ay = sum(deneyim_ay.get(a, 0) for a in istenen) if istenen else sum(deneyim_ay.values())
    min_yil = int(job.get("min_deneyim") or 0)
    if min_yil <= 0:
        sure = 20
    else:
        oran = min(1.0, ilgili_ay / (min_yil * 12))
        sure = 20 * oran
        if oran >= 1:
            eslesen.append(f"Deneyim: {_yil_metni(ilgili_ay)} (istenen {min_yil} yıl)")
        else:
            eksik.append(f"Deneyim: {_yil_metni(ilgili_ay)} (istenen en az {min_yil} yıl)")

    # 3) Mezuniyet (15)
    mez = job.get("mezuniyet_alanlari") or []
    if not mez:
        mezuniyet = 15
    elif seeker["mezuniyet"] in mez:
        mezuniyet = 15
        eslesen.append("Mezuniyet alanı uygun")
    else:
        mezuniyet = 0
        eksik.append("Mezuniyet: " + " / ".join(mez))

    # 4) Sürücü belgesi (10)
    if job.get("surucu_belgesi"):
        if seeker["surucu_belgesi"]:
            belge = 10
            eslesen.append("Sürücü belgesi")
        else:
            belge = 0
            eksik.append("Sürücü belgesi isteniyor")
    else:
        belge = 10

    # 5) İlçe (10)
    if not job.get("ilce") or not seeker["ilce"]:
        ilce = 5
    elif job["ilce"].casefold() == seeker["ilce"].casefold():
        ilce = 10
        eslesen.append(f"Aynı ilçe ({job['ilce']})")
    else:
        ilce = 0

    toplam = int(round(uzmanlik + sure + mezuniyet + belge + ilce))
    return {"ilan": job, "skor": max(0, min(100, toplam)), "eslesen": eslesen, "eksik": eksik}


def match(seeker, jobs):
    uygun = []
    for j in jobs:
        if j.get("il") and seeker["il"] and j["il"] != seeker["il"]:
            continue
        if seeker["sektor"] and j.get("sektor") and j["sektor"] != seeker["sektor"]:
            continue
        uygun.append(score(seeker, j))
    uygun.sort(key=lambda r: r["skor"], reverse=True)
    return uygun
