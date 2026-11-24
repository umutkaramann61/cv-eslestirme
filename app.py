"""İş arayan – İşletme eşleştirme sitesi (Flask)."""
import hmac
import json
import os
import re
import secrets
from functools import wraps

from flask import (Flask, Response, abort, flash, redirect, render_template,
                   request, session, url_for)
from werkzeug.middleware.proxy_fix import ProxyFix

import db
import instagram
import matcher
import secenekler as S

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

# Site başka bir sitenin içine (iframe) gömüldüğünde de çerezlerin çalışması için
if os.environ.get("RENDER") or os.environ.get("COOKIE_SECURE") == "1":
    app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)

SITE_ADI = os.environ.get("SITE_ADI", "Kariyer Eşleştirme")
OKUL_ADI = os.environ.get("OKUL_ADI", "Haydarpaşa MTAL")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
FRAME_ANCESTORS = os.environ.get("FRAME_ANCESTORS", "*")

db.init_db(seed_file=os.path.join(BASE_DIR, "ornek_ilanlar.json"))


@app.context_processor
def inject_globals():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return {"SITE_ADI": SITE_ADI, "OKUL_ADI": OKUL_ADI, "S": S,
            "csrf_token": session["csrf"], "is_admin": session.get("admin", False),
            "deneyim_etiketi": dict(S.DENEYIM_SECENEKLERI)}


@app.before_request
def instagram_kontrol():
    # Süresi geldiyse Instagram'daki yeni ilan gönderilerini arka planda çek
    if request.method == "GET" and not request.path.startswith("/static"):
        try:
            instagram.arka_planda_kontrol()
        except Exception:
            pass


@app.after_request
def security_headers(resp):
    resp.headers["Content-Security-Policy"] = f"frame-ancestors {FRAME_ANCESTORS}"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return resp


def check_csrf():
    token = request.form.get("csrf", "")
    if not token or not hmac.compare_digest(token, session.get("csrf", "")):
        abort(400, "Oturum süresi doldu, sayfayı yenileyip tekrar deneyin.")


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper


IG_RE = re.compile(r"^(?:https?://)?(?:www\.)?instagram\.com/(?:[\w.]+/)?(p|reel|tv)/([\w-]+)", re.I)


def normalize_instagram(link):
    """Instagram gönderi linkini standart biçime çevirir; geçersizse None döner."""
    m = IG_RE.match((link or "").strip())
    if not m:
        return None
    return f"https://www.instagram.com/{m.group(1).lower()}/{m.group(2)}/"


def prepare_admin_form(form):
    """Yönetici formu: Instagram linkini düzelt, boş başvuru/iletişim alanlarını doldur."""
    f = form.copy()
    hatalar = []
    link = f.get("instagram", "").strip()
    if link:
        norm = normalize_instagram(link)
        if not norm:
            hatalar.append("Instagram linki bir gönderi linki olmalı (ör. https://www.instagram.com/p/ABC123/).")
            norm = link
        f["instagram"] = norm
        if not f.get("basvuru", "").strip():
            f["basvuru"] = norm
        if not f.get("iletisim", "").strip():
            f["iletisim"] = "Instagram gönderisi"
    return f, hatalar


def validate_job(form):
    hatalar = []
    for alan, ad in [("firma", "Firma adı"), ("iletisim", "İletişim bilgisi"), ("baslik", "İlan başlığı"),
                     ("il", "İl"), ("sektor", "Sektör"), ("basvuru", "Başvuru yolu")]:
        if not form.get(alan, "").strip():
            hatalar.append(f"{ad} zorunludur.")
    if form.get("il") and form.get("il") not in S.ILLER:
        hatalar.append("Geçerli bir il seçin.")
    return hatalar


# ---------------------------------------------------------------- herkese açık
@app.route("/")
def index():
    return render_template("index.html", ilan_sayisi=len(db.list_jobs()))


@app.route("/ilanlar")
def ilanlar():
    il = request.args.get("il", "")
    jobs = db.list_jobs()
    if il:
        jobs = [j for j in jobs if j.get("il") == il]
    return render_template("ilanlar.html", ilanlar=jobs, secili_il=il)


@app.route("/is-ara", methods=["GET", "POST"])
def is_ara():
    if request.method == "GET":
        return render_template("is_ara.html", form={})
    check_csrf()
    seeker, hatalar = matcher.parse_seeker(request.form)
    if hatalar:
        for h in hatalar:
            flash(h, "hata")
        return render_template("is_ara.html", form=request.form)
    sonuclar = matcher.match(seeker, db.list_jobs())
    # Gizlilik: iş arayan bilgileri kaydedilmez, yalnızca bu istekte işlenir.
    return render_template("sonuc.html", sonuclar=sonuclar, seeker=seeker)


@app.route("/ilan-ver", methods=["GET", "POST"])
def ilan_ver():
    if request.method == "GET":
        return render_template("ilan_form.html", ilan={}, mod="isletme")
    check_csrf()
    if request.form.get("web_sitesi"):  # bot tuzağı (gizli alan)
        return render_template("tesekkur.html")
    hatalar = validate_job(request.form)
    if hatalar:
        for h in hatalar:
            flash(h, "hata")
        return render_template("ilan_form.html", ilan=_form_as_job(request.form), mod="isletme")
    form = request.form.copy()
    form.pop("instagram", None)
    db.add_job(form, durum="bekliyor")
    return render_template("tesekkur.html")


def _form_as_job(form):
    """Hatalı gönderimde formu yeniden doldurmak için."""
    d = {k: form.get(k, "") for k in db.NAMES}
    for k in ("mezuniyet_alanlari", "uzmanliklar", "robot_markalari"):
        d[k] = form.getlist(k)
    d["surucu_belgesi"] = form.get("surucu_belgesi") in ("1", "on")
    try:
        d["min_deneyim"] = int(form.get("min_deneyim") or 0)
    except ValueError:
        d["min_deneyim"] = 0
    return d


# ---------------------------------------------------------------- yönetici
@app.route("/yonetim/giris", methods=["GET", "POST"])
def admin_login():
    if not ADMIN_PASSWORD:
        return render_template("admin_login.html", kapali=True)
    if request.method == "POST":
        check_csrf()
        if hmac.compare_digest(request.form.get("sifre", ""), ADMIN_PASSWORD):
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Şifre hatalı.", "hata")
    return render_template("admin_login.html", kapali=False)


@app.route("/yonetim/cikis", methods=["POST"])
def admin_logout():
    check_csrf()
    session.pop("admin", None)
    return redirect(url_for("index"))


@app.route("/yonetim")
@admin_required
def admin():
    jobs = db.list_jobs(only_published=False)
    sira = {"bekliyor": 0, "yayinda": 1, "pasif": 2}
    jobs.sort(key=lambda j: (sira.get(j["durum"], 3), -j["id"]))
    bekleyen = sum(1 for j in jobs if j["durum"] == "bekliyor")
    return render_template("admin.html", ilanlar=jobs, bekleyen=bekleyen, ig=instagram.durum())


@app.route("/yonetim/instagram/cek", methods=["POST"])
@admin_required
def instagram_cek():
    check_csrf()
    n = instagram.cek(zorla=True)
    if n is None:
        flash("Instagram'dan çekilemedi: " + (instagram.durum()["son_hata"] or "bağlantı kurulamadı."), "hata")
    elif n == 0:
        flash("Instagram'da yeni ilan gönderisi yok.", "bilgi")
    else:
        flash(f"Instagram'dan {n} yeni ilan geldi. Kontrol edip onaylayın.", "basari")
    return redirect(url_for("admin"))


@app.route("/yonetim/ilan/yeni", methods=["GET", "POST"])
@admin_required
def ilan_yeni():
    if request.method == "POST":
        check_csrf()
        form, hatalar = prepare_admin_form(request.form)
        hatalar += validate_job(form)
        if hatalar:
            for h in hatalar:
                flash(h, "hata")
            return render_template("ilan_form.html", ilan=_form_as_job(form), mod="yeni")
        db.add_job(form, durum=form.get("durum") or "yayinda")
        flash("İlan eklendi ve yayına alındı.", "basari")
        return redirect(url_for("admin"))
    return render_template("ilan_form.html", ilan={}, mod="yeni")


@app.route("/yonetim/ilan/<int:job_id>", methods=["GET", "POST"])
@admin_required
def ilan_duzenle(job_id):
    ilan = db.get_job(job_id)
    if not ilan:
        abort(404)
    if request.method == "POST":
        check_csrf()
        form, hatalar = prepare_admin_form(request.form)
        hatalar += validate_job(form)
        if hatalar:
            for h in hatalar:
                flash(h, "hata")
            return render_template("ilan_form.html", ilan=_form_as_job(form) | {"id": job_id}, mod="duzenle")
        db.update_job(job_id, form)
        flash("İlan güncellendi.", "basari")
        return redirect(url_for("admin"))
    return render_template("ilan_form.html", ilan=ilan, mod="duzenle")


@app.route("/yonetim/ilan/<int:job_id>/durum", methods=["POST"])
@admin_required
def ilan_durum(job_id):
    check_csrf()
    durum = request.form.get("durum", "")
    db.set_status(job_id, durum)
    flash({"yayinda": "İlan yayına alındı.", "pasif": "İlan yayından kaldırıldı."}.get(durum, "Güncellendi."), "basari")
    return redirect(url_for("admin"))


@app.route("/yonetim/ilan/<int:job_id>/sil", methods=["POST"])
@admin_required
def ilan_sil(job_id):
    check_csrf()
    db.delete_job(job_id)
    flash("İlan silindi.", "basari")
    return redirect(url_for("admin"))


@app.route("/yonetim/yedek")
@admin_required
def yedek_indir():
    data = json.dumps(db.export_jobs(), ensure_ascii=False, indent=2)
    return Response(data, mimetype="application/json",
                    headers={"Content-Disposition": "attachment; filename=ilanlar_yedek.json"})


@app.route("/yonetim/yedek-yukle", methods=["POST"])
@admin_required
def yedek_yukle():
    check_csrf()
    f = request.files.get("yedek")
    try:
        items = json.loads(f.read().decode("utf-8"))
        assert isinstance(items, list)
        n = 0
        for it in items:
            if it.get("baslik") and it.get("firma"):
                db.add_job(it)
                n += 1
        flash(f"{n} ilan içe aktarıldı.", "basari")
    except Exception:
        flash("Yedek dosyası okunamadı.", "hata")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  Site açıldı:  http://127.0.0.1:{port}\n  Yönetim:      http://127.0.0.1:{port}/yonetim\n")
    app.run(host="127.0.0.1", port=port, debug=False)
