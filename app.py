# ══════════════════════════════════════════════════════════════════════════════
#  📡 PromoTélécom Mali — 100% Automatique, zéro intervention manuelle
#  Développé par Sayoba GANSANE  |  © 2025
#
#  Sources : Playwright · requests · Catalogue · Google News · Nitter · Facebook
#  Refresh : offres 30min · réseaux sociaux 15min · UI 60s
# ══════════════════════════════════════════════════════════════════════════════

import streamlit as st
import json
import os
import urllib.parse
import pandas as pd
from datetime import datetime, date, timedelta

# ── PAGE CONFIG ──
st.set_page_config(
    page_title="📡 PromoTélécom Mali",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "📡 PromoTélécom Mali — Développé par Sayoba GANSANE © 2025"}
)

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60_000, limit=None, key="auto_refresh")
except ImportError:
    pass

# ── CONSTANTES ──
DATA_DIR     = "data"
STATS_FILE   = os.path.join(DATA_DIR, "stats.json")
HISTORY_FILE = os.path.join(DATA_DIR, "promo_history.json")
COLORS     = {"telecel": "#E30613", "orange": "#F7941D", "moov": "#0057A8"}
OP_EMOJI   = {"telecel": "🔴", "orange": "🟠", "moov": "🔵"}
OP_NAMES   = {"telecel": "Telecel Mali", "orange": "Orange Mali", "moov": "Moov Africa Malitel"}
CAT_LABELS = {
    "data": "📶 Data", "voice": "📞 Appels", "sms": "💬 SMS",
    "combo": "🎁 Combo", "money": "💳 Mobile Money",
    "fixe": "🌐 Internet Fixe", "enterprise": "🏢 Solutions Pro",
}
SOCIAL_LINKS = {
    "orange":  {"fb":"https://www.facebook.com/OrangeMALI","tw":"https://twitter.com/OrangeMali","li":"https://www.linkedin.com/company/orange-mali","ig":"https://www.instagram.com/orangemali/"},
    "moov":    {"fb":"https://www.facebook.com/MoovAfricaMalitel","tw":"https://twitter.com/MoovMalitel","li":"https://www.linkedin.com/company/moov-africa-malitel","ig":"https://www.instagram.com/moovafricamalitel/"},
    "telecel": {"fb":"https://www.facebook.com/TelecelMali","tw":"https://twitter.com/TelecelMali","li":"https://www.linkedin.com/company/telecel-mali","ig":"https://www.instagram.com/telecel_mali/"},
}
MONTHS_FR = ["Janvier","Février","Mars","Avril","Mai","Juin",
             "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]


# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
def inject_css():
    st.markdown("""<style>
.stApp{background:#080c14;color:#e8f0fe}
.main .block-container{padding:1.2rem 2rem 3rem;max-width:100%}
section[data-testid="stSidebar"]{background:#0f1520;border-right:1px solid #1e2a42}
#MainMenu,footer,header{visibility:hidden}
.ptm-header{background:linear-gradient(135deg,#0f1520,#161d2e);border:1px solid #1e2a42;border-radius:16px;padding:20px 28px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
.ptm-title{font-size:1.6rem;font-weight:800;margin:0}
.ptm-sub{font-size:.78rem;color:#556080;margin:0}
.live-pill{background:#22c55e18;border:1px solid #22c55e40;color:#22c55e;font-size:.72rem;font-weight:800;padding:5px 12px;border-radius:20px;display:inline-flex;align-items:center;gap:6px}
.live-dot{width:8px;height:8px;border-radius:50%;background:#22c55e;animation:blink 1s infinite;display:inline-block}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
.visit-box{background:#161d2e;border:1px solid #1e2a42;border-radius:14px;padding:18px;text-align:center;margin-bottom:12px}
.visit-total{font-size:2.8rem;font-weight:900;color:#6366f1;line-height:1}
.visit-lbl{font-size:.68rem;color:#556080;text-transform:uppercase;letter-spacing:.6px}
.visit-today{font-size:1.3rem;font-weight:700;color:#22c55e;margin-top:8px}
.status-chip{background:#161d2e;border:1px solid #1e2a42;border-radius:10px;padding:8px 12px;font-size:.75rem;display:inline-flex;align-items:center;gap:6px;margin:4px}
.sc-dot{width:7px;height:7px;border-radius:50%}
.sc-scraped{background:#22c55e}.sc-catalog{background:#6366f1}.sc-error{background:#ef4444}
.ticker-wrap{background:#0d1220;border:1px solid #1e2a42;border-radius:10px;overflow:hidden;margin-bottom:16px;height:38px;display:flex;align-items:center}
.ticker-live{background:#0f1520;border-right:1px solid #1e2a42;padding:0 14px;font-size:.68rem;font-weight:800;color:#22c55e;display:flex;align-items:center;gap:5px;letter-spacing:1px;height:100%;flex-shrink:0}
.ticker-scroll{overflow:hidden;flex:1}
.ticker-inner{display:flex;animation:scroll-left 45s linear infinite;white-space:nowrap}
.ticker-inner:hover{animation-play-state:paused}
@keyframes scroll-left{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
.ticker-item{font-size:.77rem;padding:0 24px;color:#8899bb;border-right:1px solid #1e2a42}
.ticker-item.telecel{color:#ff4d5e}.ticker-item.orange{color:#ffaa44}.ticker-item.moov{color:#3399ff}
.promo-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(285px,1fr));gap:18px;margin-top:12px}
.pcard{background:#0f1520;border:1px solid #1e2a42;border-radius:14px;overflow:hidden;display:flex;flex-direction:column;transition:transform .18s,box-shadow .18s}
.pcard:hover{transform:translateY(-3px);box-shadow:0 10px 36px rgba(0,0,0,.5)}
.pcard.telecel{border-top:3px solid #E30613}.pcard.orange{border-top:3px solid #F7941D}.pcard.moov{border-top:3px solid #0057A8}
.pcard.highlight.telecel{box-shadow:0 0 0 1px #E3061340,0 8px 28px #E3061320}
.pcard.highlight.orange{box-shadow:0 0 0 1px #F7941D40,0 8px 28px #F7941D20}
.pcard.highlight.moov{box-shadow:0 0 0 1px #0057A840,0 8px 28px #0057A820}
.pcard-head{padding:14px 16px 6px;display:flex;align-items:flex-start;justify-content:space-between}
.pcard-badges{display:flex;gap:6px;flex-wrap:wrap}
.badge{font-size:.65rem;font-weight:800;padding:3px 8px;border-radius:20px;text-transform:uppercase;letter-spacing:.4px;white-space:nowrap}
.badge-telecel{background:#E3061315;color:#ff4d5e;border:1px solid #E3061335}
.badge-orange{background:#F7941D15;color:#ffaa44;border:1px solid #F7941D35}
.badge-moov{background:#0057A815;color:#3399ff;border:1px solid #0057A835}
.badge-b2c{background:#22c55e12;color:#4ade80;border:1px solid #22c55e30}
.badge-b2b{background:#6366f112;color:#818cf8;border:1px solid #6366f130}
.badge-new{background:#f59e0b18;color:#fbbf24;border:1px solid #f59e0b35;animation:blink 2s infinite}
.badge-hot{background:#ef444418;color:#f87171;border:1px solid #ef444430}
.badge-src-scraped{background:#22c55e12;color:#4ade80;border:1px solid #22c55e25;font-size:.6rem}
.badge-src-catalog{background:#6366f112;color:#818cf8;border:1px solid #6366f125;font-size:.6rem}
.pcard-body{padding:4px 16px 14px;flex:1}
.pcard-cat{font-size:.72rem;color:#556080;margin-bottom:5px;font-weight:600}
.pcard-title{font-size:.98rem;font-weight:700;margin-bottom:4px;color:#e8f0fe;line-height:1.3}
.pcard-desc{font-size:.79rem;color:#8899bb;line-height:1.55;margin-bottom:9px}
.pcard-price{font-size:1.45rem;font-weight:900;margin-bottom:3px}
.pcard-validity{font-size:.73rem;color:#8899bb;background:#161d2e;padding:3px 8px;border-radius:6px;display:inline-block;margin-bottom:9px}
.features{list-style:none;padding:0;margin:0 0 9px}
.features li{font-size:.78rem;color:#8899bb;padding:2px 0;display:flex;gap:7px}
.features li::before{content:"✓";color:#22c55e;font-weight:800;flex-shrink:0}
.b2b-contact{background:#1a2240;border-left:3px solid #6366f1;border-radius:0 8px 8px 0;padding:7px 12px;font-size:.74rem;color:#8899bb;margin-bottom:9px}
.b2b-contact strong{color:#e8f0fe;display:block;margin-bottom:2px}
.countdown{background:#161d2e;border-radius:8px;padding:7px 12px;font-size:.73rem;display:flex;justify-content:space-between;margin-bottom:9px}
.countdown-v{font-weight:700;color:#f59e0b}.countdown-v.urgent{color:#ef4444;animation:blink .7s infinite}
.pcard-footer{padding:10px 16px;border-top:1px solid #1e2a42;background:#161d2e}
.wa-btn{display:inline-flex;align-items:center;gap:6px;background:#25D366;color:#fff;text-decoration:none;font-size:.78rem;font-weight:700;padding:8px 14px;border-radius:8px;width:100%;justify-content:center;transition:opacity .2s}
.wa-btn:hover{opacity:.85;color:#fff}
.sec-title{font-size:.72rem;font-weight:700;color:#556080;text-transform:uppercase;letter-spacing:.8px;margin:20px 0 12px;display:flex;align-items:center;gap:10px}
.sec-title::after{content:'';flex:1;height:1px;background:#1e2a42}
.update-banner{background:#6366f112;border:1px solid #6366f130;border-radius:10px;padding:10px 16px;font-size:.78rem;color:#818cf8;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px}
/* Stats */
.rank-card{border-radius:16px;padding:24px 20px;text-align:center;position:relative;overflow:hidden}
.rank-card.leader{border:2px solid;animation:glow 2s ease-in-out infinite}
@keyframes glow{0%,100%{box-shadow:0 0 20px currentColor}50%{box-shadow:0 0 40px currentColor,0 0 60px currentColor}}
.rank-crown{font-size:2rem;display:block;margin-bottom:6px}
.rank-num{font-size:3.5rem;font-weight:900;line-height:1}
.rank-lbl{font-size:.75rem;color:#556080;text-transform:uppercase;letter-spacing:.6px;margin-top:4px}
.rank-pct{font-size:1.1rem;font-weight:700;margin-top:8px;opacity:.8}
.rank-bar-wrap{background:#080c14;border-radius:8px;height:8px;margin-top:10px;overflow:hidden}
.rank-bar{height:100%;border-radius:8px;transition:width .8s ease}
.stat-info-box{background:#0f1520;border:1px solid #1e2a42;border-radius:12px;padding:16px;margin-bottom:12px}
/* Social */
.social-post{background:#080c14;border:1px solid #1e2a42;border-radius:10px;padding:14px;margin-bottom:10px}
.social-op-card{background:#0f1520;border:1px solid #1e2a42;border-radius:14px;padding:20px;margin-bottom:20px}
.social-btn{display:inline-flex;align-items:center;gap:6px;padding:8px 14px;border-radius:8px;font-size:.8rem;font-weight:700;text-decoration:none;transition:opacity .2s;margin:4px}
.social-btn:hover{opacity:.8}
.btn-fb{background:#1877F215;color:#4267B2;border:1px solid #1877F230}
.btn-tw{background:#1DA1F215;color:#1DA1F2;border:1px solid #1DA1F230}
.btn-li{background:#0A66C215;color:#0A66C2;border:1px solid #0A66C230}
.btn-ig{background:#E1306C15;color:#E1306C;border:1px solid #E1306C30}
.ptm-footer{text-align:center;padding:28px 20px 10px;font-size:.8rem;color:#556080;border-top:1px solid #1e2a42;margin-top:40px}
.ptm-footer strong{color:#e8f0fe}
div[data-testid="metric-container"]{background:#161d2e;border:1px solid #1e2a42;border-radius:10px;padding:12px}
div.stTabs [data-baseweb="tab-list"]{background:#0f1520;border-bottom:1px solid #1e2a42}
div.stTabs [data-baseweb="tab"]{color:#8899bb}
div.stTabs [aria-selected="true"]{color:#e8f0fe}
</style>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FIREBASE
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def get_db():
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate(dict(st.secrets["firebase"]))
            except Exception:
                if not os.path.exists("firebase_service_account.json"):
                    return None, False
                cred = credentials.Certificate("firebase_service_account.json")
            firebase_admin.initialize_app(cred)
        return firestore.client(), True
    except Exception:
        return None, False


# ══════════════════════════════════════════════════════════════════════════════
# SCRAPING AUTOMATIQUE (cache 30 min)
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=1800, show_spinner=False)
def auto_scrape():
    import scraper
    result = scraper.scrape_all()
    _persist_promos(result)
    _log_daily_stats(result)   # ← enregistre les stats quotidiennes
    return result

def _persist_promos(result):
    db, use_fb = get_db()
    if use_fb:
        try:
            from firebase_admin import firestore as fs
            batch = db.batch()
            for p in result["promos"]:
                batch.set(db.collection("promos").document(p["id"]), p)
            db.collection("meta").document("last_scrape").set({
                "scraped_at": result["scraped_at"],
                "next_update": result["next_update"],
                "status": result["status"],
            })
            batch.commit()
        except Exception:
            pass
    else:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR,"promos.json"),"w",encoding="utf-8") as f:
            json.dump(result["promos"], f, ensure_ascii=False, indent=2)

def _log_daily_stats(result):
    """Enregistre le nombre de promos par opérateur chaque jour (historique)."""
    today     = date.today().isoformat()
    promos    = result["promos"]
    db, use_fb = get_db()

    entries = []
    for op in ["orange", "moov", "telecel"]:
        op_promos = [p for p in promos if p.get("operator") == op]
        cats = {}
        for p in op_promos:
            c = p.get("category","other")
            cats[c] = cats.get(c,0) + 1
        entries.append({
            "date":       today,
            "operator":   op,
            "count":      len(op_promos),
            "categories": cats,
            "source":     result.get("status",{}).get(op,{}).get("source","catalog"),
            "b2c":        sum(1 for p in op_promos if p.get("segment") in ("b2c","both")),
            "b2b":        sum(1 for p in op_promos if p.get("segment") in ("b2b","both")),
        })

    if use_fb:
        try:
            batch = get_db()[0].batch()
            for e in entries:
                doc_id = f"{e['date']}_{e['operator']}"
                batch.set(get_db()[0].collection("promo_stats").document(doc_id), e, merge=True)
            batch.commit()
        except Exception:
            pass
    else:
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            with open(HISTORY_FILE, encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
        # Remplacer ou ajouter l'entrée du jour
        for e in entries:
            existing = next((h for h in history if h.get("date")==e["date"] and h.get("operator")==e["operator"]), None)
            if existing:
                existing.update(e)
            else:
                history.append(e)
        # Garder 90 jours
        history.sort(key=lambda x: x.get("date",""))
        history = history[-270:]   # 90 jours × 3 opérateurs
        with open(HISTORY_FILE,"w",encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# HISTORIQUE STATS (cache 1h)
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def load_history() -> list:
    """Charge l'historique quotidien des promos (90 jours)."""
    cutoff = (date.today() - timedelta(days=90)).isoformat()
    db, use_fb = get_db()
    if use_fb:
        try:
            docs = db.collection("promo_stats").where("date",">=",cutoff).stream()
            return [doc.to_dict() for doc in docs]
        except Exception:
            pass
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return [h for h in json.load(f) if h.get("date","") >= cutoff]
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# RÉSEAUX SOCIAUX (cache 15 min)
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=900, show_spinner=False)
def auto_social():
    try:
        import social_scraper
        return social_scraper.fetch_all()
    except Exception:
        return {"orange":[],"moov":[],"telecel":[]}


# ══════════════════════════════════════════════════════════════════════════════
# COMPTEUR DE VISITES
# ══════════════════════════════════════════════════════════════════════════════
def count_visit():
    if st.session_state.get("_vc"):
        return
    st.session_state["_vc"] = True
    today = date.today().isoformat()
    db, use_fb = get_db()
    if use_fb:
        from firebase_admin import firestore as fs
        db.collection("stats").document("visits").set(
            {"total": fs.Increment(1), f"daily.{today}": fs.Increment(1),
             "last_visit": datetime.now().isoformat()}, merge=True)
    else:
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            with open(STATS_FILE) as f: s = json.load(f)
        except Exception:
            s = {"total":0,"daily":{},"last_visit":None}
        s["total"] += 1
        s["daily"][today] = s["daily"].get(today,0) + 1
        s["last_visit"] = datetime.now().isoformat()
        with open(STATS_FILE,"w") as f: json.dump(s, f, ensure_ascii=False, indent=2)

def get_stats():
    today = date.today().isoformat()
    db, use_fb = get_db()
    if use_fb:
        doc = db.collection("stats").document("visits").get()
        if doc.exists:
            d = doc.to_dict()
            return {"total":d.get("total",0),"today":d.get("daily",{}).get(today,0),
                    "last_visit":d.get("last_visit","—"),"daily":d.get("daily",{})}
    try:
        with open(STATS_FILE) as f: s = json.load(f)
        return {"total":s["total"],"today":s["daily"].get(today,0),
                "last_visit":s.get("last_visit","—"),"daily":s.get("daily",{})}
    except Exception:
        return {"total":0,"today":0,"last_visit":"—","daily":{}}


# ══════════════════════════════════════════════════════════════════════════════
# FILTRES DATES
# ══════════════════════════════════════════════════════════════════════════════
def _date_range_from_filter(period, specific_day, month_idx, year):
    """Retourne (date_from, date_to) selon le filtre sélectionné."""
    today = date.today()
    if period == "Aujourd'hui":
        return today, today
    elif period == "7 derniers jours":
        return today - timedelta(days=6), today
    elif period == "Ce mois":
        return today.replace(day=1), today
    elif period == "Mois précédent":
        first = today.replace(day=1)
        last_m = first - timedelta(days=1)
        return last_m.replace(day=1), last_m
    elif period == "Mois spécifique":
        first = date(year, month_idx, 1)
        # Dernier jour du mois
        if month_idx == 12:
            last = date(year+1, 1, 1) - timedelta(days=1)
        else:
            last = date(year, month_idx+1, 1) - timedelta(days=1)
        return first, last
    elif period == "Jour spécifique":
        return specific_day, specific_day
    return None, None   # "Tout"

def _promo_date(p) -> date | None:
    raw = p.get("created_at","")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw).date()
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# RENDU HTML — CARTES PROMOS
# ══════════════════════════════════════════════════════════════════════════════
def _e(s): return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def _cd(valid_until):
    if not valid_until: return ""
    try:
        diff = datetime.fromisoformat(valid_until) - datetime.now()
        if diff.total_seconds() <= 0:
            return '<div class="countdown"><span style="color:#8899bb">⏱</span><span class="countdown-v urgent">EXPIRÉ</span></div>'
        d, h = diff.days, diff.seconds//3600
        m = (diff.seconds%3600)//60
        txt = f"{d}j {h}h {m}m" if d>0 else f"{h}h {m}m"
        cls = " urgent" if diff.total_seconds()<3600 else ""
        return f'<div class="countdown"><span style="color:#556080;font-size:.73rem">⏱ Expire</span><span class="countdown-v{cls}">{txt}</span></div>'
    except: return ""

def card_html(p):
    op  = p.get("operator","telecel")
    seg = p.get("segment","b2c")
    c   = COLORS.get(op,"#6366f1")
    src = p.get("source","catalog")
    hl  = " highlight" if p.get("highlight") else ""
    b   = f'<span class="badge badge-{op}">{_e(OP_NAMES.get(op,""))}</span>'
    b  += ('<span class="badge badge-b2c">B2C</span>' if seg=="b2c" else
           '<span class="badge badge-b2b">B2B</span>' if seg=="b2b" else
           '<span class="badge badge-b2c">B2C</span><span class="badge badge-b2b">B2B</span>')
    if p.get("isNew"): b += '<span class="badge badge-new">🆕 NOUVEAU</span>'
    if p.get("isHot"): b += '<span class="badge badge-hot">🔥 HOT</span>'
    src_label = {"scraped":"🌐 Live","catalog":"📋 Catalogue"}.get(src,"📋 Catalogue")
    src_badge = f'<span class="badge badge-src-{src if src in ("scraped","catalog") else "catalog"}">{src_label}</span>'
    feats = "".join(f"<li>{_e(f)}</li>" for f in (p.get("features") or [])[:4])
    contact = (f'<div class="b2b-contact"><strong>📞 Contact B2B</strong>{_e(p["contact"])}</div>'
               if p.get("contact") and seg in ("b2b","both") else "")
    wa  = f"📡 *{OP_NAMES.get(op,op).upper()}* — {p.get('title','')}\n"
    if p.get("price"): wa += f"💰 {p['price']}"+(f" / {p['validity']}" if p.get("validity") else "")+"\n"
    for f in p.get("features") or []: wa += f"• {f}\n"
    if p.get("desc"): wa += p["desc"]+"\n"
    wa += "\n🔗 PromoTélécom Mali — par Sayoba GANSANE"
    wa_link = "https://wa.me/?text=" + urllib.parse.quote(wa)
    src_url = p.get("source_url","")
    src_link = f'<a href="{_e(src_url)}" target="_blank" style="font-size:.65rem;color:#556080">🔗</a>' if src_url else ""
    return f"""
<div class="pcard {op}{hl}">
  <div class="pcard-head"><div class="pcard-badges">{b}{src_badge}</div>{src_link}</div>
  <div class="pcard-body">
    <div class="pcard-cat">{CAT_LABELS.get(p.get("category",""),"")}</div>
    <div class="pcard-title">{_e(p.get("title",""))}</div>
    {f'<div class="pcard-desc">{_e(p.get("desc",""))}</div>' if p.get("desc") else ""}
    {f'<div class="pcard-price" style="color:{c}">{_e(p.get("price",""))}</div>' if p.get("price") else ""}
    {f'<div class="pcard-validity">📅 {_e(p.get("validity",""))}</div>' if p.get("validity") else ""}
    {f'<ul class="features">{feats}</ul>' if feats else ""}
    {contact}{_cd(p.get("validUntil"))}
  </div>
  <div class="pcard-footer"><a class="wa-btn" href="{wa_link}" target="_blank">📤 Partager sur WhatsApp</a></div>
</div>"""

def render_grid(lst):
    if not lst: st.info("📭 Aucune offre pour ce filtre."); return
    st.markdown('<div class="promo-grid">'+"".join(card_html(p) for p in lst)+"</div>", unsafe_allow_html=True)

def render_ticker(promos):
    if not promos: return
    items = "".join(
        f'<span class="ticker-item {p.get("operator","")}">'
        f'{OP_EMOJI.get(p.get("operator",""),"")}'
        f' <strong>{OP_NAMES.get(p.get("operator",""),"")}</strong>'
        f' — {_e(p.get("title",""))}'
        +(f' — {_e(p.get("price",""))}' if p.get("price") else "")
        +"</span>"
        for p in promos[:14]
    )
    st.markdown(f"""<div class="ticker-wrap">
  <div class="ticker-live"><span class="live-dot"></span>LIVE</div>
  <div class="ticker-scroll"><div class="ticker-inner">{items*2}</div></div>
</div>""", unsafe_allow_html=True)

def render_status(status, scraped_at, next_update):
    chips = ""
    for op, s in status.items():
        src = s.get("source","?"); cnt = s.get("count",0)
        dot = "sc-scraped" if src=="scraped" else "sc-catalog"
        lbl = "🌐 Live" if src=="scraped" else "📋 Catalogue"
        chips += f'<span class="status-chip"><span class="sc-dot {dot}"></span><span style="color:{COLORS.get(op,"#fff")};font-weight:700">{OP_EMOJI.get(op,"")} {OP_NAMES.get(op,op)}</span> — {lbl} ({cnt})</span>'
    try:
        sa = datetime.fromisoformat(scraped_at).strftime("%d/%m %H:%M")
        nu = datetime.fromisoformat(next_update).strftime("%d/%m %H:%M")
    except Exception:
        sa = nu = "—"
    st.markdown(f'<div class="update-banner"><div>{chips}</div><div style="font-size:.72rem;color:#556080">Mis à jour : {sa} · Prochain : {nu}</div></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET STATISTIQUES
# ══════════════════════════════════════════════════════════════════════════════
def render_stats_tab(promos_all, history, date_from, date_to):
    """Statistiques : classement opérateurs, évolution quotidienne, répartition."""

    # ── Appliquer le filtre date aux promos (pour les stats snapshot)
    if date_from and date_to:
        snap = [p for p in promos_all
                if (lambda d: date_from <= d <= date_to if d else True)(_promo_date(p))]
    else:
        snap = promos_all

    total = len(snap) or 1

    # ── 1. CLASSEMENT OPÉRATEURS ─────────────────────────────────────────────
    st.markdown('<div class="sec-title">🏆 Classement par nombre de promos actives</div>', unsafe_allow_html=True)

    op_counts = {op: sum(1 for p in snap if p.get("operator")==op) for op in ["orange","moov","telecel"]}
    sorted_ops = sorted(op_counts.items(), key=lambda x: x[1], reverse=True)
    leader = sorted_ops[0][0] if sorted_ops and sorted_ops[0][1] > 0 else None

    cols = st.columns(3)
    for i, (op, count) in enumerate(sorted_ops):
        color = COLORS.get(op,"#6366f1")
        name  = OP_NAMES.get(op,"")
        emoji = OP_EMOJI.get(op,"")
        pct   = round(count/total*100) if total else 0
        crown = "👑" if op == leader else ["🥈","🥉"][i-1] if i < 3 else ""
        leader_cls = "leader" if op == leader else ""
        with cols[i]:
            st.markdown(f"""
<div class="rank-card {leader_cls}" style="background:{color}12;border:{'2px solid '+color if op==leader else '1px solid '+color+'30'};color:{color}">
  <span class="rank-crown">{crown}</span>
  <span style="font-size:2rem">{emoji}</span>
  <div style="font-size:.85rem;font-weight:700;margin:6px 0 2px;color:#e8f0fe">{name}</div>
  <div class="rank-num" style="color:{color}">{count}</div>
  <div class="rank-lbl">promos actives</div>
  <div class="rank-pct" style="color:{color}">{pct}% du total</div>
  <div class="rank-bar-wrap"><div class="rank-bar" style="width:{pct}%;background:{color}"></div></div>
</div>""", unsafe_allow_html=True)

    if leader:
        st.markdown(f"""
<div style="background:#f59e0b12;border:1px solid #f59e0b30;border-radius:10px;padding:12px 18px;margin-top:14px;font-size:.85rem;color:#fbbf24">
  👑 <strong>{OP_NAMES.get(leader,"")}</strong> mène avec <strong>{op_counts[leader]} promos actives</strong>
  ({round(op_counts[leader]/total*100)}% du total) — soit {op_counts[leader] - op_counts.get(sorted_ops[1][0],0) if len(sorted_ops)>1 else 0} promos de plus que le 2ᵉ.
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 2. RÉPARTITION B2C / B2B par opérateur ───────────────────────────────
    st.markdown('<div class="sec-title">👥 Répartition B2C / B2B par opérateur</div>', unsafe_allow_html=True)
    seg_data = {}
    for op in ["orange","moov","telecel"]:
        seg_data[OP_NAMES[op]] = {
            "👤 B2C": sum(1 for p in snap if p.get("operator")==op and p.get("segment") in ("b2c","both")),
            "🏢 B2B": sum(1 for p in snap if p.get("operator")==op and p.get("segment") in ("b2b","both")),
        }
    df_seg = pd.DataFrame(seg_data).T
    if not df_seg.empty:
        st.bar_chart(df_seg, color=["#22c55e","#6366f1"], height=220)

    # ── 3. RÉPARTITION PAR CATÉGORIE ─────────────────────────────────────────
    st.markdown('<div class="sec-title">📊 Répartition par catégorie</div>', unsafe_allow_html=True)
    cat_data = {CAT_LABELS[c]: {OP_NAMES[op]: sum(1 for p in snap if p.get("operator")==op and p.get("category")==c)
                                 for op in ["orange","moov","telecel"]}
                for c in CAT_LABELS}
    df_cat = pd.DataFrame(cat_data).T
    if not df_cat.empty:
        op_colors_list = [COLORS["orange"], COLORS["moov"], COLORS["telecel"]]
        st.bar_chart(df_cat, color=op_colors_list, height=260)

    # ── 4. ÉVOLUTION QUOTIDIENNE (historique) ────────────────────────────────
    st.markdown('<div class="sec-title">📈 Évolution quotidienne — Promos par opérateur (90 derniers jours)</div>', unsafe_allow_html=True)

    if history:
        df_h = pd.DataFrame(history)
        if "date" in df_h.columns and "operator" in df_h.columns and "count" in df_h.columns:
            pivot = df_h.pivot_table(index="date", columns="operator", values="count", aggfunc="sum").fillna(0)
            # Renommer les colonnes avec les noms complets
            pivot.rename(columns=OP_NAMES, inplace=True)
            if date_from and date_to:
                pivot = pivot[(pivot.index >= date_from.isoformat()) & (pivot.index <= date_to.isoformat())]
            if not pivot.empty:
                pivot.index = pd.to_datetime(pivot.index)
                st.line_chart(pivot, color=[COLORS["orange"], COLORS["moov"], COLORS["telecel"]], height=280)

                # Résumé période
                period_totals = pivot.sum().sort_values(ascending=False)
                st.markdown("**Totaux sur la période :**")
                row_cols = st.columns(len(period_totals))
                for i, (name, val) in enumerate(period_totals.items()):
                    op_key = next((k for k,v in OP_NAMES.items() if v==name), "")
                    crown_txt = "👑 " if i==0 else ""
                    row_cols[i].metric(f"{crown_txt}{name}", int(val))
            else:
                st.info("Aucune donnée historique pour cette période.")
        else:
            st.info("Format d'historique inattendu.")
    else:
        st.markdown("""
<div class="stat-info-box" style="text-align:center;color:#556080">
  <div style="font-size:2rem;margin-bottom:8px">📊</div>
  <div style="font-size:.85rem">L'historique s'accumule automatiquement à chaque scraping.</div>
  <div style="font-size:.75rem;margin-top:6px">Revenez dans 24h pour voir le graphique d'évolution.</div>
</div>""", unsafe_allow_html=True)

    # ── 5. TABLEAU RÉCAPITULATIF ──────────────────────────────────────────────
    st.markdown('<div class="sec-title">📋 Tableau récapitulatif détaillé</div>', unsafe_allow_html=True)
    rows = []
    for op in ["orange","moov","telecel"]:
        op_p = [p for p in snap if p.get("operator")==op]
        rows.append({
            "Opérateur":  OP_NAMES[op],
            "Total":      len(op_p),
            "B2C":        sum(1 for p in op_p if p.get("segment") in ("b2c","both")),
            "B2B":        sum(1 for p in op_p if p.get("segment") in ("b2b","both")),
            "Data":       sum(1 for p in op_p if p.get("category")=="data"),
            "Combo":      sum(1 for p in op_p if p.get("category")=="combo"),
            "Money":      sum(1 for p in op_p if p.get("category")=="money"),
            "Voix":       sum(1 for p in op_p if p.get("category")=="voice"),
            "Fixe/Pro":   sum(1 for p in op_p if p.get("category") in ("fixe","enterprise")),
            "% du total": f"{round(len(op_p)/total*100)}%",
        })
    df_table = pd.DataFrame(rows).set_index("Opérateur")
    st.dataframe(df_table, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET RÉSEAUX SOCIAUX
# ══════════════════════════════════════════════════════════════════════════════
def render_social_tab(social_data):
    for op_key in ["orange","moov","telecel"]:
        links = SOCIAL_LINKS.get(op_key,{})
        color = COLORS.get(op_key,"#fff")
        emoji = OP_EMOJI.get(op_key,"")
        name  = OP_NAMES.get(op_key,"")
        st.markdown(f"""<div class="social-op-card">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
    <span style="font-size:1.8rem">{emoji}</span>
    <div><div style="font-size:1rem;font-weight:800;color:#e8f0fe">{name}</div>
    <div style="font-size:.73rem;color:#556080">Pages officielles — actualisées automatiquement</div></div>
  </div>
  <div>
    <a class="social-btn btn-fb" href="{links.get('fb','#')}" target="_blank">📘 Facebook</a>
    <a class="social-btn btn-tw" href="{links.get('tw','#')}" target="_blank">🐦 X / Twitter</a>
    <a class="social-btn btn-li" href="{links.get('li','#')}" target="_blank">💼 LinkedIn</a>
    <a class="social-btn btn-ig" href="{links.get('ig','#')}" target="_blank">📸 Instagram</a>
  </div>""", unsafe_allow_html=True)
        posts = social_data.get(op_key,[])
        if posts:
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown(f'<div class="sec-title" style="margin-top:14px">📰 {len(posts)} publications récupérées</div>', unsafe_allow_html=True)
            for post in posts:
                url = post.get("url","")
                st.markdown(f"""<div class="social-post">
  <div style="font-size:.7rem;color:#556080;margin-bottom:8px">
    {f'<span style="color:#60a5fa">{_e(post.get("source",""))}</span>' if post.get("source") else ""}
    {f'· {_e(post.get("date",""))}' if post.get("date") else ""}
    {f'· <a href="{_e(url)}" target="_blank" style="color:#6366f1">Voir ↗</a>' if url else ""}
  </div>
  <div style="font-size:.82rem;color:#8899bb;line-height:1.6">{_e(post.get("text","")[:400])}</div>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="margin-top:10px;font-size:.75rem;color:#556080;font-style:italic">⚡ Publications récupérées automatiquement — mise à jour toutes les 15 min.</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    inject_css()
    count_visit()

    with st.spinner("⚡ Actualisation automatique…"):
        result      = auto_scrape()
        social_data = auto_social()
        history     = load_history()

    promos      = result["promos"]
    status      = result.get("status", {})
    scraped_at  = result.get("scraped_at","")
    next_update = result.get("next_update","")
    stats       = get_stats()
    _, use_fb   = get_db()

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 📡 PromoTélécom Mali")
        st.caption("⚡ 100% automatique — aucune intervention")
        st.divider()

        # Compteur visites
        st.markdown(f"""<div class="visit-box">
  <div class="visit-total">{stats['total']:,}</div>
  <div class="visit-lbl">Visites totales</div>
  <div class="visit-today">{stats['today']:,}</div>
  <div class="visit-lbl">Aujourd'hui</div>
</div>""", unsafe_allow_html=True)
        if stats.get("daily"):
            days = [(date.today()-timedelta(days=i)).isoformat() for i in range(6,-1,-1)]
            df_v = pd.DataFrame({"J":[d[-5:] for d in days],"V":[stats["daily"].get(d,0) for d in days]}).set_index("J")
            st.caption("📈 Visites — 7 jours")
            st.bar_chart(df_v, height=110, color="#6366f1")

        st.divider()

        # Filtres offres
        st.markdown("**🔍 Filtres offres**")
        search  = st.text_input("", placeholder="Rechercher…", label_visibility="collapsed")
        op_f    = st.radio("Opérateur", ["Tous","Telecel Mali","Orange Mali","Moov Africa Malitel"], label_visibility="collapsed")
        seg_f   = st.radio("Segment",   ["Tous","👤 B2C","🏢 B2B"], label_visibility="collapsed")
        cat_ops = ["Toutes"]+list(CAT_LABELS.values())
        cat_f   = st.selectbox("Catégorie", cat_ops, label_visibility="collapsed")

        op_sel  = {"Tous":"all","Telecel Mali":"telecel","Orange Mali":"orange","Moov Africa Malitel":"moov"}[op_f]
        seg_sel = {"Tous":"all","👤 B2C":"b2c","🏢 B2B":"b2b"}[seg_f]
        cat_rev = {v:k for k,v in CAT_LABELS.items()}
        cat_sel = cat_rev.get(cat_f,"all") if cat_f!="Toutes" else "all"

        st.divider()

        # ── FILTRES DATES ────────────────────────────────────────────────────
        st.markdown("**📅 Période**")
        period_opts = ["Tout","Aujourd'hui","7 derniers jours","Ce mois",
                       "Mois précédent","Mois spécifique","Jour spécifique"]
        period_f = st.selectbox("Période", period_opts, label_visibility="collapsed")

        specific_day  = date.today()
        month_idx     = date.today().month
        year_val      = date.today().year

        if period_f == "Jour spécifique":
            specific_day = st.date_input("Date", value=date.today(), key="dp_day")
        elif period_f == "Mois spécifique":
            current_year = date.today().year
            year_val  = st.selectbox("Année", list(range(current_year, current_year-3,-1)), key="dp_year")
            month_idx = st.selectbox("Mois", range(1,13), format_func=lambda x: MONTHS_FR[x-1], key="dp_month")

        date_from, date_to = _date_range_from_filter(period_f, specific_day, month_idx, year_val)

        if date_from and date_to:
            if date_from == date_to:
                st.caption(f"📅 Filtre : {date_from.strftime('%d/%m/%Y')}")
            else:
                st.caption(f"📅 Du {date_from.strftime('%d/%m')} au {date_to.strftime('%d/%m/%Y')}")

        st.divider()
        fb_ico = "🟢 Firebase" if use_fb else "🟡 Local JSON"
        scraped_n = sum(1 for p in promos if p.get("source")=="scraped")
        st.caption(f"**Mode :** {fb_ico}")
        st.caption(f"**Live scraped :** {scraped_n} / {len(promos)}")
        if st.button("🔄 Forcer mise à jour", use_container_width=True):
            st.cache_data.clear(); st.rerun()
        st.divider()
        st.caption("Développé par **Sayoba GANSANE** © 2025")

    # ── HEADER ───────────────────────────────────────────────────────────────
    total_social = sum(len(v) for v in social_data.values())
    period_label = ""
    if date_from and date_to:
        period_label = f" · Filtre : {date_from.strftime('%d/%m')}–{date_to.strftime('%d/%m/%Y')}"
    st.markdown(f"""<div class="ptm-header">
  <div>
    <p class="ptm-title">📡 PromoTélécom Mali</p>
    <p class="ptm-sub">100% automatique · Sites officiels · Facebook · X · LinkedIn · Google News{period_label}</p>
  </div>
  <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
    <span class="live-pill"><span class="live-dot"></span>DIRECT</span>
    <span style="background:#161d2e;border:1px solid #1e2a42;border-radius:20px;padding:5px 14px;font-size:.75rem;color:#8899bb">{len(promos)} offres</span>
    <span style="background:#22c55e12;border:1px solid #22c55e30;border-radius:20px;padding:5px 14px;font-size:.75rem;color:#4ade80">📱 {total_social} posts sociaux</span>
    <span style="background:#161d2e;border:1px solid #1e2a42;border-radius:20px;padding:5px 14px;font-size:.75rem;color:#8899bb">👥 {stats['total']:,} visites</span>
  </div>
</div>""", unsafe_allow_html=True)

    render_status(status, scraped_at, next_update)
    render_ticker(promos)

    # Métriques
    c = st.columns(7)
    c[0].metric("🔴 Telecel", sum(1 for p in promos if p.get("operator")=="telecel"))
    c[1].metric("🟠 Orange",  sum(1 for p in promos if p.get("operator")=="orange"))
    c[2].metric("🔵 Moov",    sum(1 for p in promos if p.get("operator")=="moov"))
    c[3].metric("👤 B2C",     sum(1 for p in promos if p.get("segment") in ("b2c","both")))
    c[4].metric("🏢 B2B",     sum(1 for p in promos if p.get("segment") in ("b2b","both")))
    c[5].metric("🌐 Live",    scraped_n)
    c[6].metric("📱 Sociaux", total_social)

    # ── FILTRAGE ─────────────────────────────────────────────────────────────
    def filt(lst):
        r = lst
        if op_sel  != "all": r = [p for p in r if p.get("operator")==op_sel]
        if seg_sel != "all": r = [p for p in r if p.get("segment") in (seg_sel,"both")]
        if cat_sel != "all": r = [p for p in r if p.get("category")==cat_sel]
        if search:
            q = search.lower()
            r = [p for p in r if q in (p.get("title") or "").lower() or q in (p.get("desc") or "").lower()]
        if date_from and date_to:
            r = [p for p in r if (lambda d: date_from <= d <= date_to if d else True)(_promo_date(p))]
        return r

    filtered = filt(promos)

    # ── ONGLETS ───────────────────────────────────────────────────────────────
    tabs = st.tabs(["🌐 Vue d'ensemble","👤 B2C","🏢 B2B","📊 Statistiques","📱 Réseaux Sociaux"])

    with tabs[0]:
        b2c = [p for p in filtered if p.get("segment") in ("b2c","both")]
        b2b = [p for p in filtered if p.get("segment") in ("b2b","both")]
        if b2c:
            st.markdown(f'<div class="sec-title">👤 B2C — Grand Public ({len(b2c)} offres)</div>', unsafe_allow_html=True)
            render_grid(b2c)
        if b2b:
            st.markdown(f'<div class="sec-title">🏢 B2B — Entreprises ({len(b2b)} offres)</div>', unsafe_allow_html=True)
            render_grid(b2b)
        if not b2c and not b2b:
            st.info("📭 Aucune offre pour ce filtre.")

    with tabs[1]:
        lst = [p for p in filtered if p.get("segment") in ("b2c","both")]
        st.markdown(f'<div class="sec-title">👤 Grand Public ({len(lst)} offres)</div>', unsafe_allow_html=True)
        render_grid(lst)

    with tabs[2]:
        lst = [p for p in filtered if p.get("segment") in ("b2b","both")]
        st.markdown(f'<div class="sec-title">🏢 Entreprises ({len(lst)} offres)</div>', unsafe_allow_html=True)
        render_grid(lst)

    with tabs[3]:
        render_stats_tab(promos, history, date_from, date_to)

    with tabs[4]:
        render_social_tab(social_data)

    # ── FOOTER ───────────────────────────────────────────────────────────────
    last_v = stats.get("last_visit","—")
    if last_v and last_v != "—":
        try: last_v = datetime.fromisoformat(last_v).strftime("%d/%m/%Y à %H:%M")
        except: pass
    try:
        sa_fmt = datetime.fromisoformat(scraped_at).strftime("%d/%m/%Y à %H:%M") if scraped_at else "—"
    except: sa_fmt = "—"
    st.markdown(f"""<div class="ptm-footer">
  <p>📡 <strong>PromoTélécom Mali</strong> — Suivi 100% automatique des promotions télécom au Mali</p>
  <p>Sources : Sites officiels · Facebook · X · LinkedIn · Instagram · Google News</p>
  <p>Développé avec ❤️ par <strong>Sayoba GANSANE</strong> &nbsp;|&nbsp; © 2025</p>
  <p style="margin-top:6px;font-size:.71rem">Telecel Mali · Orange Mali · Moov Africa Malitel<br>
  Dernière MAJ : {sa_fmt} · {stats['total']:,} visites · Dernière visite : {last_v}</p>
</div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
