# ══════════════════════════════════════════════════════════════════════════════
#  📡 PromoTélécom Mali — 100% Automatisé, zéro intervention manuelle
#  Développé par Sayoba GANSANE  |  © 2025
#
#  Fonctionnement :
#   • Le scraper tourne automatiquement toutes les heures (cache TTL=3600s)
#   • L'interface se rafraîchit automatiquement toutes les 60 secondes
#   • Aucun admin nécessaire — tout est autonome
# ══════════════════════════════════════════════════════════════════════════════

import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime, date, timedelta

# ── PAGE CONFIG ──
st.set_page_config(
    page_title="📡 PromoTélécom Mali",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "📡 PromoTélécom Mali — Développé par Sayoba GANSANE © 2025"}
)

# ── AUTO-REFRESH (60 secondes) ──
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60_000, limit=None, key="auto_refresh")
except ImportError:
    pass  # Optionnel — fonctionne sans

# ── CONSTANTES ──
DATA_DIR    = "data"
STATS_FILE  = os.path.join(DATA_DIR, "stats.json")
COLORS      = {"telecel": "#E30613", "orange": "#F7941D", "moov": "#0057A8"}
OP_EMOJI    = {"telecel": "🔴", "orange": "🟠", "moov": "🔵"}
OP_NAMES    = {"telecel": "Telecel Mali", "orange": "Orange Mali", "moov": "Moov Africa Malitel"}
CAT_LABELS  = {
    "data": "📶 Data", "voice": "📞 Appels", "sms": "💬 SMS",
    "combo": "🎁 Combo", "money": "💳 Mobile Money",
    "fixe": "🌐 Internet Fixe", "enterprise": "🏢 Solutions Pro",
}

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
def inject_css():
    st.markdown("""<style>
.stApp{background:#080c14;color:#e8f0fe}
.main .block-container{padding:1.2rem 2rem 3rem;max-width:100%}
section[data-testid="stSidebar"]{background:#0f1520;border-right:1px solid #1e2a42}
#MainMenu,footer,header{visibility:hidden}
/* Header */
.ptm-header{background:linear-gradient(135deg,#0f1520,#161d2e);border:1px solid #1e2a42;border-radius:16px;padding:20px 28px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
.ptm-title{font-size:1.6rem;font-weight:800;margin:0}.ptm-sub{font-size:.78rem;color:#556080;margin:0}
.live-pill{background:#22c55e18;border:1px solid #22c55e40;color:#22c55e;font-size:.72rem;font-weight:800;padding:5px 12px;border-radius:20px;display:inline-flex;align-items:center;gap:6px}
.live-dot{width:8px;height:8px;border-radius:50%;background:#22c55e;animation:blink 1s infinite;display:inline-block}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
/* Visit counter */
.visit-box{background:#161d2e;border:1px solid #1e2a42;border-radius:14px;padding:18px;text-align:center;margin-bottom:12px}
.visit-total{font-size:2.8rem;font-weight:900;color:#6366f1;line-height:1}
.visit-lbl{font-size:.68rem;color:#556080;text-transform:uppercase;letter-spacing:.6px}
.visit-today{font-size:1.3rem;font-weight:700;color:#22c55e;margin-top:8px}
/* Scrape status */
.status-row{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}
.status-chip{background:#161d2e;border:1px solid #1e2a42;border-radius:10px;padding:8px 12px;font-size:.75rem;display:flex;align-items:center;gap:6px}
.sc-dot{width:7px;height:7px;border-radius:50%}
.sc-scraped{background:#22c55e}.sc-generated{background:#f59e0b}.sc-error{background:#ef4444}
/* Ticker */
.ticker-wrap{background:#0d1220;border:1px solid #1e2a42;border-radius:10px;overflow:hidden;margin-bottom:16px;height:38px;display:flex;align-items:center}
.ticker-live{background:#0f1520;border-right:1px solid #1e2a42;padding:0 14px;font-size:.68rem;font-weight:800;color:#22c55e;display:flex;align-items:center;gap:5px;letter-spacing:1px;height:100%;flex-shrink:0}
.ticker-scroll{overflow:hidden;flex:1}.ticker-inner{display:flex;animation:scroll-left 40s linear infinite;white-space:nowrap}
.ticker-inner:hover{animation-play-state:paused}
@keyframes scroll-left{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
.ticker-item{font-size:.77rem;padding:0 24px;color:#8899bb;border-right:1px solid #1e2a42}
.ticker-item.telecel{color:#ff4d5e}.ticker-item.orange{color:#ffaa44}.ticker-item.moov{color:#3399ff}
/* Promo grid */
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
.badge-src-generated{background:#f59e0b10;color:#fbbf2490;border:1px solid #f59e0b20;font-size:.6rem}
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
/* Update banner */
.update-banner{background:#6366f112;border:1px solid #6366f130;border-radius:10px;padding:10px 16px;font-size:.78rem;color:#818cf8;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px}
/* Footer */
.ptm-footer{text-align:center;padding:28px 20px 10px;font-size:.8rem;color:#556080;border-top:1px solid #1e2a42;margin-top:40px}
.ptm-footer strong{color:#e8f0fe}
div[data-testid="metric-container"]{background:#161d2e;border:1px solid #1e2a42;border-radius:10px;padding:12px}
div.stTabs [data-baseweb="tab-list"]{background:#0f1520;border-bottom:1px solid #1e2a42}
div.stTabs [data-baseweb="tab"]{color:#8899bb}
div.stTabs [aria-selected="true"]{color:#e8f0fe}
</style>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FIREBASE (optionnel)
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
# SCRAPING AUTOMATIQUE (cache 1 heure)
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def auto_scrape():
    """
    Appelé automatiquement à chaque expiration du cache (1 h).
    Scrape les 3 opérateurs → stocke dans Firebase ou JSON local.
    """
    import scraper
    result = scraper.scrape_all()
    _persist(result)
    return result

def _persist(result):
    """Sauvegarde les résultats (Firebase ou fichier local)."""
    db, use_fb = get_db()
    promos = result["promos"]
    if use_fb:
        from firebase_admin import firestore as fs
        # Désactiver les anciennes offres puis insérer les nouvelles
        old = db.collection("promos").where("active", "==", True).stream()
        batch = db.batch()
        for doc in old:
            batch.update(doc.reference, {"active": False})
        for p in promos:
            ref = db.collection("promos").document(p["id"])
            batch.set(ref, p)
        batch.commit()
        # Sauvegarder le statut
        db.collection("meta").document("last_scrape").set({
            "scraped_at":  result["scraped_at"],
            "next_update": result["next_update"],
            "status":      result["status"],
        })
    else:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, "promos.json"), "w", encoding="utf-8") as f:
            json.dump(promos, f, ensure_ascii=False, indent=2)
        with open(os.path.join(DATA_DIR, "scrape_meta.json"), "w", encoding="utf-8") as f:
            json.dump({"scraped_at": result["scraped_at"],
                       "next_update": result["next_update"],
                       "status": result["status"]}, f, ensure_ascii=False, indent=2)


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
        path = STATS_FILE
        try:
            with open(path) as f: s = json.load(f)
        except Exception:
            s = {"total": 0, "daily": {}, "last_visit": None}
        s["total"] += 1
        s["daily"][today] = s["daily"].get(today, 0) + 1
        s["last_visit"] = datetime.now().isoformat()
        with open(path, "w") as f: json.dump(s, f, ensure_ascii=False, indent=2)

def get_stats():
    today = date.today().isoformat()
    db, use_fb = get_db()
    if use_fb:
        doc = db.collection("stats").document("visits").get()
        if doc.exists:
            d = doc.to_dict()
            return {"total": d.get("total",0), "today": d.get("daily",{}).get(today,0),
                    "last_visit": d.get("last_visit","—"), "daily": d.get("daily",{})}
    try:
        with open(STATS_FILE) as f: s = json.load(f)
        return {"total": s["total"], "today": s["daily"].get(today,0),
                "last_visit": s.get("last_visit","—"), "daily": s.get("daily",{})}
    except Exception:
        return {"total": 0, "today": 0, "last_visit": "—", "daily": {}}


# ══════════════════════════════════════════════════════════════════════════════
# RENDU HTML
# ══════════════════════════════════════════════════════════════════════════════
def _e(s): return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def _cd(valid_until):
    if not valid_until: return ""
    try:
        diff = datetime.fromisoformat(valid_until) - datetime.now()
        if diff.total_seconds() <= 0:
            return '<div class="countdown"><span style="color:#8899bb;font-size:.73rem">⏱</span><span class="countdown-v urgent">EXPIRÉ</span></div>'
        d, h = diff.days, diff.seconds // 3600
        m = (diff.seconds % 3600) // 60
        txt = f"{d}j {h}h {m}m" if d > 0 else f"{h}h {m}m"
        cls = " urgent" if diff.total_seconds() < 3600 else ""
        return f'<div class="countdown"><span style="color:#556080;font-size:.73rem">⏱ Expire</span><span class="countdown-v{cls}">{txt}</span></div>'
    except: return ""

def card_html(p):
    op  = p.get("operator","telecel")
    seg = p.get("segment","b2c")
    c   = COLORS.get(op,"#6366f1")
    hl  = " highlight" if p.get("highlight") else ""
    b   = f'<span class="badge badge-{op}">{_e(OP_NAMES.get(op,""))}</span>'
    b  += '<span class="badge badge-b2c">B2C</span>' if seg == "b2c" else \
          '<span class="badge badge-b2b">B2B</span>' if seg == "b2b" else \
          '<span class="badge badge-b2c">B2C</span><span class="badge badge-b2b">B2B</span>'
    if p.get("isNew"): b += '<span class="badge badge-new">🆕 NOUVEAU</span>'
    if p.get("isHot"): b += '<span class="badge badge-hot">🔥 HOT</span>'
    src = p.get("source","generated")
    src_badge = f'<span class="badge badge-src-{src}">{"🌐 Scraped" if src=="scraped" else "⚙️ Auto"}</span>'
    feats = "".join(f"<li>{_e(f)}</li>" for f in (p.get("features") or [])[:4])
    contact = (f'<div class="b2b-contact"><strong>📞 Contact B2B</strong>{_e(p["contact"])}</div>'
               if p.get("contact") and seg in ("b2b","both") else "")
    wa = f"📡 *{OP_NAMES.get(op,op).upper()}* — {p.get('title','')}\n"
    if p.get("price"):    wa += f"💰 {p['price']}" + (f" / {p['validity']}" if p.get("validity") else "") + "\n"
    for f in p.get("features") or []: wa += f"• {f}\n"
    if p.get("desc"):     wa += p["desc"] + "\n"
    wa += "\n🔗 PromoTélécom Mali — par Sayoba GANSANE"
    wa_link = "https://wa.me/?text=" + urllib.parse.quote(wa)
    return f"""
<div class="pcard {op}{hl}">
  <div class="pcard-head"><div class="pcard-badges">{b}{src_badge}</div></div>
  <div class="pcard-body">
    <div class="pcard-cat">{CAT_LABELS.get(p.get("category",""),"")}</div>
    <div class="pcard-title">{_e(p.get("title",""))}</div>
    {f'<div class="pcard-desc">{_e(p.get("desc",""))}</div>' if p.get("desc") else ""}
    {f'<div class="pcard-price" style="color:{c}">{_e(p.get("price",""))}</div>' if p.get("price") else ""}
    {f'<div class="pcard-validity">📅 {_e(p.get("validity",""))}</div>' if p.get("validity") else ""}
    {f'<ul class="features">{feats}</ul>' if feats else ""}
    {contact}
    {_cd(p.get("validUntil"))}
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
        +'</span>'
        for p in promos[:14]
    )
    st.markdown(f"""<div class="ticker-wrap">
  <div class="ticker-live"><span class="live-dot"></span>LIVE</div>
  <div class="ticker-scroll"><div class="ticker-inner">{items*2}</div></div>
</div>""", unsafe_allow_html=True)

def render_status(status, scraped_at, next_update):
    chips = ""
    for op, s in status.items():
        src  = s.get("source","?")
        cnt  = s.get("count",0)
        dot  = "sc-scraped" if src=="scraped" else ("sc-generated" if src=="generated" else "sc-error")
        lbl  = "🌐 Scraped" if src=="scraped" else "⚙️ Généré" if src=="generated" else "❌ Erreur"
        color= COLORS.get(op,"#fff")
        chips += f'<div class="status-chip"><span class="sc-dot {dot}"></span><span style="color:{color};font-weight:700">{OP_EMOJI.get(op,"")} {OP_NAMES.get(op,op)}</span> — {lbl} ({cnt} offres)</div>'
    try:
        sa = datetime.fromisoformat(scraped_at).strftime("%d/%m %H:%M")
        nu = datetime.fromisoformat(next_update).strftime("%d/%m %H:%M")
    except Exception:
        sa = nu = "—"
    st.markdown(f"""
<div class="update-banner">
  <div style="display:flex;flex-wrap:wrap;gap:10px">{chips}</div>
  <div style="font-size:.72rem;color:#556080">Mis à jour : {sa} &nbsp;·&nbsp; Prochain : {nu}</div>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    inject_css()
    count_visit()

    # ── SCRAPING AUTOMATIQUE ──
    with st.spinner("🔄 Actualisation des offres…"):
        result = auto_scrape()
    promos    = result["promos"]
    status    = result.get("status", {})
    scraped_at  = result.get("scraped_at","")
    next_update = result.get("next_update","")

    stats   = get_stats()
    _, use_fb = get_db()

    # ── SIDEBAR ──
    with st.sidebar:
        st.markdown("## 📡 PromoTélécom Mali")
        st.caption("Mise à jour automatique toutes les heures")
        st.divider()

        # Compteur de visites
        st.markdown(f"""<div class="visit-box">
  <div class="visit-total">{stats['total']:,}</div>
  <div class="visit-lbl">Visites totales</div>
  <div class="visit-today">{stats['today']:,}</div>
  <div class="visit-lbl">Aujourd'hui</div>
</div>""", unsafe_allow_html=True)

        # Graphique 7 jours
        if stats.get("daily"):
            import pandas as pd
            days = [(date.today()-timedelta(days=i)).isoformat() for i in range(6,-1,-1)]
            df = pd.DataFrame({"J":[d[-5:] for d in days],
                               "V":[stats["daily"].get(d,0) for d in days]}).set_index("J")
            st.caption("📈 Visites — 7 jours")
            st.bar_chart(df, height=110, color="#6366f1")

        st.divider()
        st.markdown("**🔍 Filtres**")
        search  = st.text_input("", placeholder="Rechercher…", label_visibility="collapsed")
        op_f    = st.radio("Opérateur", ["Tous","Telecel Mali","Orange Mali","Moov Africa Malitel"], label_visibility="collapsed")
        seg_f   = st.radio("Segment",   ["Tous","👤 B2C","🏢 B2B"], label_visibility="collapsed")
        cat_ops = ["Toutes"]+list(CAT_LABELS.values())
        cat_f   = st.selectbox("Catégorie", cat_ops, label_visibility="collapsed")

        op_sel  = {"Tous":"all","Telecel Mali":"telecel","Orange Mali":"orange","Moov Africa Malitel":"moov"}[op_f]
        seg_sel = {"Tous":"all","👤 B2C":"b2c","🏢 B2B":"b2b"}[seg_f]
        cat_rev = {v:k for k,v in CAT_LABELS.items()}
        cat_sel = cat_rev.get(cat_f,"all") if cat_f != "Toutes" else "all"

        st.divider()
        fb_ico = "🟢 Firebase" if use_fb else "🟡 Local JSON"
        st.caption(f"**Mode :** {fb_ico}")
        st.caption(f"**Auto-refresh :** toutes les 60s")
        if st.button("🔄 Forcer mise à jour", use_container_width=True):
            st.cache_data.clear(); st.rerun()

        st.divider()
        st.caption("Développé par **Sayoba GANSANE** © 2025")

    # ── HEADER ──
    total = len(promos)
    st.markdown(f"""<div class="ptm-header">
  <div>
    <p class="ptm-title">📡 PromoTélécom Mali</p>
    <p class="ptm-sub">Promotions 100% automatisées — Telecel · Orange · Moov</p>
  </div>
  <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
    <span class="live-pill"><span class="live-dot"></span>DIRECT</span>
    <span style="background:#161d2e;border:1px solid #1e2a42;border-radius:20px;padding:5px 14px;font-size:.75rem;color:#8899bb">{total} offres</span>
    <span style="background:#161d2e;border:1px solid #1e2a42;border-radius:20px;padding:5px 14px;font-size:.75rem;color:#8899bb">👥 {stats['total']:,} visites</span>
  </div>
</div>""", unsafe_allow_html=True)

    # ── STATUT SCRAPING ──
    render_status(status, scraped_at, next_update)

    # ── TICKER ──
    render_ticker(promos)

    # ── MÉTRIQUES ──
    m1,m2,m3,m4,m5,m6 = st.columns(6)
    m1.metric("🔴 Telecel", sum(1 for p in promos if p.get("operator")=="telecel"))
    m2.metric("🟠 Orange",  sum(1 for p in promos if p.get("operator")=="orange"))
    m3.metric("🔵 Moov",    sum(1 for p in promos if p.get("operator")=="moov"))
    m4.metric("👤 B2C",     sum(1 for p in promos if p.get("segment") in ("b2c","both")))
    m5.metric("🏢 B2B",     sum(1 for p in promos if p.get("segment") in ("b2b","both")))
    scraped_n = sum(1 for p in promos if p.get("source")=="scraped")
    m6.metric("🌐 Scraped", scraped_n)

    # ── FILTRAGE ──
    def filt(lst):
        r = lst
        if op_sel  != "all": r = [p for p in r if p.get("operator")==op_sel]
        if seg_sel != "all": r = [p for p in r if p.get("segment") in (seg_sel,"both")]
        if cat_sel != "all": r = [p for p in r if p.get("category")==cat_sel]
        if search:
            q = search.lower()
            r = [p for p in r if q in (p.get("title") or "").lower()
                              or q in (p.get("desc") or "").lower()]
        return r
    filtered = filt(promos)

    # ── ONGLETS ──
    tabs = st.tabs(["🌐 Vue d'ensemble","👤 B2C — Grand public","🏢 B2B — Entreprises"])

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
            st.info("📭 Aucune offre trouvée.")

    with tabs[1]:
        lst = [p for p in filtered if p.get("segment") in ("b2c","both")]
        st.markdown(f'<div class="sec-title">👤 Grand Public ({len(lst)} offres)</div>', unsafe_allow_html=True)
        render_grid(lst)

    with tabs[2]:
        lst = [p for p in filtered if p.get("segment") in ("b2b","both")]
        st.markdown(f'<div class="sec-title">🏢 Entreprises ({len(lst)} offres)</div>', unsafe_allow_html=True)
        render_grid(lst)

    # ── FOOTER ──
    last_v = stats.get("last_visit","—")
    if last_v and last_v != "—":
        try: last_v = datetime.fromisoformat(last_v).strftime("%d/%m/%Y à %H:%M")
        except: pass
    try:
        sa_fmt = datetime.fromisoformat(scraped_at).strftime("%d/%m/%Y à %H:%M") if scraped_at else "—"
    except: sa_fmt = "—"
    st.markdown(f"""<div class="ptm-footer">
  <p>📡 <strong>PromoTélécom Mali</strong> — Suivi automatisé des promotions télécom au Mali</p>
  <p>Développé avec ❤️ par <strong>Sayoba GANSANE</strong> &nbsp;|&nbsp; © 2025</p>
  <p style="margin-top:6px;font-size:.71rem">
    Telecel Mali &nbsp;·&nbsp; Orange Mali &nbsp;·&nbsp; Moov Africa Malitel<br>
    Dernier scraping : {sa_fmt} &nbsp;·&nbsp; {stats['total']:,} visites totales &nbsp;·&nbsp; Dernière visite : {last_v}
  </p>
</div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
