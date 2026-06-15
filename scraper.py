# ══════════════════════════════════════════════════════════════════════════════
#  scraper.py — Moteur de scraping 100% automatique PromoTélécom Mali
#  Développé par Sayoba GANSANE  |  © 2025
#
#  Stratégie de scraping (cascade automatique) :
#    1. Playwright (Chromium headless) → scrape les sites JS-rendus Orange/Moov
#    2. requests + BeautifulSoup → si le site n'est pas JS-rendered
#    3. Catalogue d'offres réelles → fallback garanti avec les prix du marché
#
#  Tout est automatique. Aucune intervention humaine requise.
# ══════════════════════════════════════════════════════════════════════════════

import requests
import re
import uuid
import logging
import sys
import subprocess
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
TIMEOUT = 10

# URLs officielles des opérateurs (sites rénovés, JS-rendered)
OPERATOR_URLS = {
    "orange": [
        "https://www.orange.ml/offres-et-services/internet",
        "https://www.orange.ml/offres-et-services",
        "https://orange.ml",
    ],
    "moov": [
        "https://www.moovafricamalitel.ml/offres",
        "https://www.moovafricamalitel.ml",
        "https://malitel.ml",
    ],
    "telecel": [
        "https://www.telecel.ml/offres",
        "https://www.telecel.ml",
    ],
}

PRICE_RE    = re.compile(r'[\d\s]{1,8}(?:FCFA|F\.?CFA|CFA|Fcfa)', re.I)
VALIDITY_RE = re.compile(r'(\d+)\s*(jour|day|heure|hour|mois|month|semaine|week)', re.I)
DATA_RE     = re.compile(r'(\d+(?:[,.]\d+)?)\s*(Go|GB|Mo|MB)', re.I)

# Flag global : Playwright installé ou non
_PLAYWRIGHT_READY = False


# ──────────────────────────────────────────────────────────────────────────────
# INSTALLATION PLAYWRIGHT (une seule fois au démarrage)
# ──────────────────────────────────────────────────────────────────────────────
def ensure_playwright():
    """Installe Chromium pour Playwright si pas déjà fait."""
    global _PLAYWRIGHT_READY
    if _PLAYWRIGHT_READY:
        return True
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            _PLAYWRIGHT_READY = True
            logger.info("[Playwright] Chromium installé ✓")
            return True
        else:
            logger.warning(f"[Playwright] Échec installation : {result.stderr[:200]}")
            return False
    except Exception as e:
        logger.warning(f"[Playwright] Impossible d'installer : {e}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# POINT D'ENTRÉE PRINCIPAL
# ──────────────────────────────────────────────────────────────────────────────
def scrape_all() -> dict:
    """
    Scrape les 3 opérateurs automatiquement.
    Retourne { promos, status, scraped_at, next_update }
    """
    now      = datetime.now()
    next_upd = (now + timedelta(minutes=30)).isoformat()
    all_promos = []
    status     = {}

    # Tenter d'initialiser Playwright en arrière-plan
    pw_ok = ensure_playwright()

    for op in ["orange", "moov", "telecel"]:
        promos, src, url = _scrape_operator(op, pw_ok)
        all_promos.extend(promos)
        status[op] = {
            "source": src,
            "url":    url or "—",
            "count":  len(promos),
            "at":     now.isoformat(),
        }
        logger.info(f"[{op.upper()}] {len(promos)} offres — source={src}")

    return {
        "promos":      all_promos,
        "status":      status,
        "scraped_at":  now.isoformat(),
        "next_update": next_upd,
    }


# ──────────────────────────────────────────────────────────────────────────────
# SCRAPING D'UN OPÉRATEUR (cascade automatique)
# ──────────────────────────────────────────────────────────────────────────────
def _scrape_operator(op: str, pw_ok: bool):
    """Tente chaque méthode jusqu'à obtenir des résultats."""
    urls = OPERATOR_URLS.get(op, [])

    # 1. Playwright (Chromium headless — gère les sites JS-rendered)
    if pw_ok:
        for url in urls:
            try:
                html = _fetch_playwright(url)
                if html and len(html) > 5000:
                    soup   = BeautifulSoup(html, "html.parser")
                    promos = _parse_offers(soup, op, url)
                    if promos:
                        logger.info(f"[{op}] Playwright ✓ — {url}")
                        return promos, "scraped", url
            except Exception as e:
                logger.debug(f"[{op}] Playwright error on {url}: {e}")

    # 2. requests (sites statiques ou partiellement rendus)
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT,
                                verify=False, allow_redirects=True)
            if resp.status_code != 200 or len(resp.text) < 4000:
                continue
            soup   = BeautifulSoup(resp.text, "html.parser")
            promos = _parse_offers(soup, op, url)
            if promos:
                logger.info(f"[{op}] requests ✓ — {url}")
                return promos, "scraped", url
        except Exception as e:
            logger.debug(f"[{op}] requests error on {url}: {e}")

    # 3. Catalogue offres réelles (fallback garanti)
    logger.info(f"[{op}] → catalogue offres réelles (sites inaccessibles)")
    return _catalog(op), "catalog", None


# ──────────────────────────────────────────────────────────────────────────────
# PLAYWRIGHT — RENDU JS
# ──────────────────────────────────────────────────────────────────────────────
def _fetch_playwright(url: str, wait_ms: int = 3000) -> str:
    """Charge une page avec Chromium headless et retourne le HTML rendu."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu"]
        )
        ctx  = browser.new_context(
            user_agent=HEADERS["User-Agent"],
            locale="fr-FR",
            viewport={"width": 1280, "height": 800}
        )
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(wait_ms)  # Attendre le rendu JS
        html = page.content()
        browser.close()
    return html


# ──────────────────────────────────────────────────────────────────────────────
# PARSEUR HTML GÉNÉRIQUE
# ──────────────────────────────────────────────────────────────────────────────
def _parse_offers(soup: BeautifulSoup, op: str, source_url: str) -> list:
    for tag in soup.find_all(["nav","header","footer","script","style","iframe","svg"]):
        tag.decompose()

    CSS_TARGETS = [
        "[class*='offer']","[class*='offre']","[class*='pack']","[class*='forfait']",
        "[class*='promo']","[class*='card']","[class*='product']","[class*='tarif']",
        "[class*='plan']","[class*='price']","[class*='bundle']",
        "article",".item",".box",
    ]
    candidates = []
    for sel in CSS_TARGETS:
        found = soup.select(sel)
        if len(found) >= 2:
            candidates.extend(found)
            break

    if not candidates:
        for el in soup.find_all(["div","section","article","li"]):
            txt = el.get_text(" ", strip=True)
            if PRICE_RE.search(txt) and 40 < len(txt) < 800:
                candidates.append(el)

    promos = []
    seen   = set()
    for el in candidates[:15]:
        txt = el.get_text(" ", strip=True)
        if len(txt) < 25:
            continue
        h     = el.find(["h1","h2","h3","h4","h5","strong","b"])
        title = (h.get_text(strip=True) if h else txt[:60])[:80]
        if not title or len(title) < 4 or title in seen:
            continue
        seen.add(title)
        pm       = PRICE_RE.search(txt)
        price    = pm.group(0).strip() if pm else ""
        vm       = VALIDITY_RE.search(txt)
        validity = f"{vm.group(1)} {vm.group(2)}s" if vm else ""
        dm       = DATA_RE.search(txt)
        # Ignorer les volumes nuls (0 Go, 0 GB…)
        data_vol = ""
        if dm:
            raw_vol = dm.group(1).replace(",", ".").strip()
            try:
                if float(raw_vol) > 0:
                    data_vol = f"{dm.group(1)} {dm.group(2)}"
            except ValueError:
                pass
        tl  = txt.lower()
        cat = ("data"       if any(w in tl for w in ["go","gb","internet","data","4g","5g","wifi"]) else
               "money"      if any(w in tl for w in ["money","flooz","transfert","paiement","cash"]) else
               "voice"      if any(w in tl for w in ["appel","call","voix","min","illimité"]) else
               "sms"        if "sms" in tl else
               "fixe"       if any(w in tl for w in ["fibre","fixe","vsat","mpls"]) else
               "enterprise" if any(w in tl for w in ["entreprise","business","pro ","m2m"]) else
               "combo")
        seg  = "b2b" if any(w in tl for w in ["entreprise","business","pme","société","pro "]) else "b2c"
        # Ignorer les offres sans prix ET sans volume — très probablement du bruit HTML
        if not price and not data_vol:
            continue
        feats = [l.strip() for l in re.split(r'[.•\n]', txt) if 8 < len(l.strip()) < 80 and l.strip() != title][:4]
        if data_vol and not any(data_vol in f for f in feats):
            feats.insert(0, f"{data_vol} internet")
        promos.append(_make(op, seg, cat, title, txt[:250], price, validity,
                            feats[:4], source="scraped", source_url=source_url))
    return promos


# ──────────────────────────────────────────────────────────────────────────────
# CATALOGUE D'OFFRES RÉELLES (basé sur les tarifs officiels connus)
# Mis à jour régulièrement dans le code — reflète les prix du marché malien
# ──────────────────────────────────────────────────────────────────────────────
def _catalog(op: str) -> list:
    nd = lambda d: (datetime.now() + timedelta(days=d)).strftime("%Y-%m-%dT%H:%M")

    if op == "orange":
        return [
            _make(op,"b2c","data","Forfait Orange 45 Go",
                  "45 Go en 4G+ pour naviguer, streamer et partager sans limite pendant 30 jours. L'offre phare d'Orange Mali.",
                  "15 000 FCFA","30 jours",
                  ["45 Go internet 4G+","YouTube & streaming HD","WhatsApp & réseaux sociaux","Partage de connexion inclus"],
                  isn=True, ish=True, hl=True),
            _make(op,"b2c","data","Forfait Orange 20 Go",
                  "20 Go mensuel pour un usage quotidien confortable en 4G+.",
                  "8 000 FCFA","30 jours",
                  ["20 Go internet 4G+","WhatsApp & Facebook inclus","Valable 30 jours"],isn=True),
            _make(op,"b2c","data","Forfait Orange 10 Go",
                  "10 Go mensuel pour une utilisation modérée et régulière.",
                  "5 000 FCFA","30 jours",
                  ["10 Go internet 4G+","Réseaux sociaux inclus","Valable 30 jours"]),
            _make(op,"b2c","data","Forfait Orange 5 Go Semaine",
                  "5 Go valable 7 jours pour rester connecté toute la semaine.",
                  "2 500 FCFA","7 jours",
                  ["5 Go internet 4G+","WhatsApp inclus","Valable 7 jours"]),
            _make(op,"b2c","data","Forfait Orange 1 Go Journalier",
                  "1 Go d'internet 4G valable 24 heures.",
                  "500 FCFA","24 heures",
                  ["1 Go internet 4G","Valable 24 heures"]),
            _make(op,"b2c","combo","Max Orange 30 Go + Appels",
                  "Le forfait tout-en-un d'Orange Mali : data + appels illimités + SMS.",
                  "12 000 FCFA","30 jours",
                  ["30 Go internet 4G+","Appels illimités Orange","200 min autres réseaux","300 SMS"],
                  isn=True, hl=True),
            _make(op,"b2c","voice","Appels Illimités Orange",
                  "Appelez tous vos contacts Orange sans limite de durée.",
                  "3 000 FCFA","30 jours",
                  ["Appels illimités Orange-Orange","50 min autres réseaux","100 SMS"]),
            _make(op,"b2c","money","Orange Money — Transfert Gratuit",
                  "Profitez du transfert d'argent sans frais entre abonnés Orange Money.",
                  "0 FCFA de frais",f"Jusqu'au {nd(20)[:10]}",
                  ["Transfert Orange-Orange gratuit","Paiement marchand sans frais","Retrait -30%"],
                  isn=True, ish=True, hl=True, exp=nd(20)),
            _make(op,"b2b","enterprise","Orange Business PME",
                  "La solution numérique complète pour les PME maliennes.",
                  "À partir de 25 000 FCFA/mois","Engagement 6 mois",
                  ["Lignes pro illimitées","100 Go data partagé","VPN sécurisé","Support dédié 24/7"],
                  hl=True, contact="+223 20 70 70 70 | business@orange.ml"),
            _make(op,"b2b","fixe","Orange Internet Dédié Entreprise",
                  "Connexion internet dédiée haut débit avec SLA garanti.",
                  "À partir de 15 000 FCFA/mois","Engagement 6 mois",
                  ["5 à 100 Mbps garanti","IP fixe dédiée","SLA 99,5%"],
                  contact="+223 20 70 70 70"),
            _make(op,"b2b","money","Orange Money Entreprise",
                  "Solution de collecte et paiement professionnel avec API.",
                  "Sur devis","Sans engagement",
                  ["Collecte de paiements en masse","API RESTful","Dashboard temps réel"],
                  isn=True, contact="+223 20 70 70 70"),
        ]

    if op == "moov":
        return [
            _make(op,"b2c","data","Moov 50 Go Mensuel",
                  "Le forfait data premium de Moov Africa Malitel. 50 Go en 4G+ pour un mois complet.",
                  "12 000 FCFA","30 jours",
                  ["50 Go internet 4G+","TikTok & YouTube inclus","Partage 5 appareils"],
                  isn=True, ish=True, hl=True),
            _make(op,"b2c","data","Moov 20 Go Mensuel",
                  "Forfait data mensuel populaire de Moov Africa Malitel.",
                  "6 000 FCFA","30 jours",
                  ["20 Go internet 4G+","WhatsApp & Facebook inclus","Valable 30 jours"],isn=True),
            _make(op,"b2c","data","Moov 10 Go Mensuel",
                  "Forfait data mensuel pour une utilisation quotidienne.",
                  "3 500 FCFA","30 jours",
                  ["10 Go internet 4G+","Réseaux sociaux inclus","Valable 30 jours"]),
            _make(op,"b2c","data","Moov 3 Go Semaine",
                  "Navigation fluide pendant toute la semaine avec TikTok inclus.",
                  "1 000 FCFA","7 jours",
                  ["3 Go internet 4G","TikTok & YouTube inclus","7 jours"]),
            _make(op,"b2c","data","Moov 1 Go Journalier",
                  "Forfait internet quotidien Moov Africa Malitel.",
                  "300 FCFA","24 heures",
                  ["1 Go internet 4G","Valable 24 heures"]),
            _make(op,"b2c","combo","Moov All-in-One 15 Go",
                  "Rapport qualité-prix imbattable : data + appels + SMS.",
                  "5 000 FCFA","30 jours",
                  ["15 Go internet 4G","150 min tous réseaux","200 SMS","WhatsApp & Facebook"],isn=True),
            _make(op,"b2c","voice","Moov Appels+ Illimités",
                  "Restez joignable par tous, sur tous les réseaux maliens.",
                  "2 500 FCFA","30 jours",
                  ["Moov-Moov illimité","100 min autres réseaux","50 SMS"]),
            _make(op,"b2c","money","Flooz — Commission -50%",
                  "Économisez 50% sur toutes vos transactions Flooz ce mois.",
                  "-50% commission",f"Jusqu'au {nd(15)[:10]}",
                  ["Transfert Flooz -50%","Retrait moins cher","Paiement marchand gratuit"],
                  isn=True, ish=True, exp=nd(15)),
            _make(op,"b2b","enterprise","Moov M2M / IoT Connect",
                  "Solutions Machine-to-Machine pour agriculture, transport et industrie.",
                  "Sur devis","Contrat annuel",
                  ["SIM M2M dédiées","Plateforme IoT","Suivi GPS flotte","API RESTful"],
                  isn=True, hl=True, contact="+223 20 08 00 00 | m2m@moov.ml"),
            _make(op,"b2b","fixe","Moov Internet Dédié Entreprise",
                  "Fibre optique et VSAT pour zones urbaines et rurales.",
                  "À partir de 20 000 FCFA/mois","Engagement 12 mois",
                  ["5 à 50 Mbps garanti","IP fixe dédiée","SLA 99,5%","Support 24/7"],
                  contact="+223 20 08 00 00"),
        ]

    if op == "telecel":
        return [
            _make(op,"b2c","data","Telecel Go+ 20 Go Mensuel",
                  "Forfait data mensuel Telecel Mali en 4G/5G pour tout le mois.",
                  "6 000 FCFA","30 jours",
                  ["20 Go internet 4G/5G","WhatsApp inclus","Valable 30 jours"],isn=True),
            _make(op,"b2c","data","Telecel Go+ 5 Go Semaine",
                  "Naviguez librement pendant 7 jours avec les réseaux sociaux offerts.",
                  "1 500 FCFA","7 jours",
                  ["5 Go internet 4G","Réseaux sociaux illimités","Valable 7 jours"],ish=True,hl=True),
            _make(op,"b2c","data","Telecel Go+ 1 Go Journalier",
                  "Internet 4G valable 24 heures, accès rapide sans engagement.",
                  "300 FCFA","24 heures",
                  ["1 Go internet 4G","Valable 24h","WhatsApp inclus"],isn=True),
            _make(op,"b2c","combo","All-in-One Mensuel Telecel",
                  "Le forfait tout-en-un incontournable de Telecel Mali.",
                  "8 000 FCFA","30 jours",
                  ["20 Go internet 4G/5G","200 min tous réseaux","300 SMS","WhatsApp illimité"],
                  isn=True, ish=True, hl=True),
            _make(op,"b2c","money","Telecel Cash — Transfert Gratuit",
                  "Économisez sur vos transferts et paiements Telecel Cash.",
                  "0 FCFA de frais",f"Jusqu'au {nd(10)[:10]}",
                  ["Transfert sans frais","Retrait réduit","Paiement marchand offert"],
                  isn=True, ish=True, exp=nd(10)),
            _make(op,"b2c","voice","Appels Illimités Telecel+",
                  "Appelez vos proches Telecel sans vous soucier du crédit.",
                  "2 500 FCFA","30 jours",
                  ["Appels illimités Telecel","50 min autres réseaux","200 SMS"]),
            _make(op,"b2b","enterprise","Pack Entreprise Telecel",
                  "Internet dédié, lignes professionnelles et support prioritaire 24/7.",
                  "À partir de 30 000 FCFA/mois","Engagement 12 mois",
                  ["Internet dédié 10 Mbps","10 lignes pro illimitées","Support 24/7"],
                  hl=True, contact="+223 20 22 00 00 | business@telecel.ml"),
            _make(op,"b2b","fixe","Internet Fixe Pro Telecel",
                  "Connexion haut débit dédiée pour votre bureau avec IP fixe.",
                  "À partir de 20 000 FCFA/mois","Sans engagement",
                  ["10 à 100 Mbps","IP fixe","Installation gratuite","SLA 99,9%"],
                  contact="+223 20 22 00 00"),
        ]
    return []


# ──────────────────────────────────────────────────────────────────────────────
# DÉTECTION DU TYPE DE PROMO
# ──────────────────────────────────────────────────────────────────────────────
def _promo_type(title: str, validity: str, features: list) -> str:
    """Détermine le type de promo à partir de la validité et du titre."""
    combined = (title + " " + validity + " " + " ".join(features or [])).lower()
    if any(w in combined for w in ["nuit","night","nocturne","00h","minuit","midnight"]):
        return "nocturne"
    if any(w in combined for w in ["24 heure","24h","1 jour","journalier","daily","par jour"]):
        return "journalier"
    if any(w in combined for w in ["7 jour","7j","semaine","weekly","hebdo"]):
        return "hebdomadaire"
    if any(w in combined for w in ["30 jour","30j","mois","mensuel","monthly"]):
        return "mensuel"
    # Déduction par durée numérique
    if validity:
        m = re.search(r'(\d+)\s*(heure|hour)', validity, re.I)
        if m and int(m.group(1)) <= 24:
            return "journalier"
        m = re.search(r'(\d+)\s*(jour|day)', validity, re.I)
        if m:
            d = int(m.group(1))
            if d <= 1:   return "journalier"
            if d <= 7:   return "hebdomadaire"
            if d <= 31:  return "mensuel"
    return "autre"


# ──────────────────────────────────────────────────────────────────────────────
# USINE À PROMOS
# ──────────────────────────────────────────────────────────────────────────────
def _make(op, seg, cat, title, desc, price, validity, features,
          isn=False, ish=False, hl=False, exp=None, contact="", source="catalog", source_url=None):
    return {
        "id":         str(uuid.uuid4()),
        "operator":   op,
        "segment":    seg,
        "category":   cat,
        "title":      title,
        "desc":       desc,
        "price":      price,
        "validity":   validity,
        "validUntil": exp,
        "features":   features,
        "promo_type": _promo_type(title, validity, features),
        "isNew":      isn,
        "isHot":      ish,
        "highlight":  hl,
        "contact":    contact,
        "active":     True,
        "source":     source,
        "source_url": source_url,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
