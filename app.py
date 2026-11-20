"""CV - İş İlanı Eşleştirme sitesi (Flask)."""
import hmac
import json
import os
import secrets
from functools import wraps

from flask import (Flask, Response, abort, flash, redirect, render_template,
                   request, session, url_for)
from werkzeug.middleware.proxy_fix import ProxyFix

import db
import matcher

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

# Site başka bir sitenin içine (iframe) gömüldüğünde de yönetici girişinin
# çalışması için HTTPS'te çerez SameSite=None + Secure olmalı.
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
    return {"SITE_ADI": SITE_ADI, "OKUL_ADI": OKUL_ADI,
            "csrf_token": session["csrf"], "ai_aktif": matcher.ai_available(),
            "is_admin": session.get("admin", False)}


@app.after_request
def security_headers(resp):
    # Gömülebilirlik: hangi sitelerin bu sayfayı iframe ile gösterebileceği
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


# ---------------------------------------------------------------- herkese açık
@app.route("/")
def index():
    jobs = db.list_jobs()
    return render_template("index.html", ilan_sayisi=len(jobs))


@app.route("/ilanlar")
def ilanlar():
    return render_template("ilanlar.html", ilanlar=db.list_jobs())


@app.route("/eslestir", methods=["POST"])
def eslestir():
    check_csrf()
    cv_text = ""
    f = request.files.get("cv_dosya")
    if f and f.filename:
        try:
            cv_text = matcher.extract_text(f.filename, f.read())
        except ValueError as e:
            flash(str(e), "hata")
            return redirect(url_for("index"))
        except Exception:
            flash("Dosya okunamadı. Dosya bozuk veya şifreli olabilir; metni kopyalayıp yapıştırmayı deneyin.", "hata")
            return redirect(url_for("index"))
    if not cv_text.strip():
        cv_text = request.form.get("cv_metin", "")
    cv_text = cv_text.strip()

    if len(cv_text) < 30:
        flash("CV metni okunamadı veya çok kısa. Taranmış (resim) PDF ise metni elle yapıştırın.", "hata")
        return redirect(url_for("index"))
    if len(cv_text) > matcher.MAX_CV_CHARS:
        flash("CV çok uzun. Lütfen en fazla birkaç sayfalık bir CV yükleyin.", "hata")
        return redirect(url_for("index"))

    jobs = db.list_jobs()
    if not jobs:
        flash("Şu anda yayında ilan yok. Daha sonra tekrar deneyin.", "bilgi")
        return redirect(url_for("index"))

    sonuc = matcher.match(cv_text, jobs, use_ai=request.form.get("yontem") != "anahtar")
    # Gizlilik: CV hiçbir yere kaydedilmez, yalnızca bu istekte işlenir.
    return render_template("sonuc.html", sonuc=sonuc)


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
    return render_template("admin.html", ilanlar=db.list_jobs(only_active=False))


@app.route("/yonetim/ilan/yeni", methods=["GET", "POST"])
@admin_required
def ilan_yeni():
    if request.method == "POST":
        check_csrf()
        if not request.form.get("baslik") or not request.form.get("firma"):
            flash("Başlık ve firma zorunludur.", "hata")
            return render_template("ilan_form.html", ilan=request.form, yeni=True)
        db.add_job(request.form)
        flash("İlan eklendi.", "basari")
        return redirect(url_for("admin"))
    return render_template("ilan_form.html", ilan={"aktif": 1}, yeni=True)


@app.route("/yonetim/ilan/<int:job_id>", methods=["GET", "POST"])
@admin_required
def ilan_duzenle(job_id):
    ilan = db.get_job(job_id)
    if not ilan:
        abort(404)
    if request.method == "POST":
        check_csrf()
        db.update_job(job_id, request.form)
        flash("İlan güncellendi.", "basari")
        return redirect(url_for("admin"))
    return render_template("ilan_form.html", ilan=ilan, yeni=False)


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
        for it in items:
            if it.get("baslik") and it.get("firma"):
                db.add_job(it)
        flash(f"{len(items)} ilan içe aktarıldı.", "basari")
    except Exception:
        flash("Yedek dosyası okunamadı.", "hata")
    return redirect(url_for("admin"))


@app.errorhandler(413)
def too_large(_e):
    flash("Dosya çok büyük (en fazla 5 MB).", "hata")
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  Site açıldı:  http://127.0.0.1:{port}\n  Yönetim:      http://127.0.0.1:{port}/yonetim\n")
    app.run(host="127.0.0.1", port=port, debug=False)
