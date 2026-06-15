# ══════════════════════════════════════════════════════════════════════════════
#  scraper.py — Moteur de scraping automatique PromoTélécom Mali
#  Développé par Sayoba GANSANE  |  © 2025
#
#  Stratégie :
#    1. Tentative de scraping réel des sites opérateurs
#    2. Si le site est inaccessible / JS-only / bloqué → fallback dynamique
#    3. Chaque résultat est taggé : source = "scraped" | "generated"
# ══════════════════════════════════════════════════════════════════════════════

import requests
import re
import uuid
import logging
import random
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Désactiver les avertissements SSL (certains sites ML ont des certs invalides)
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

TIMEOUT = 8  # secondes par requête

# URLs à essayer pour chaque opérateur (par ordre de priorité)
OPERATOR_URLS = {
    "telecel": [
        "https://www.telecel.ml/offres",
        "https://www.telecel.ml/forfaits",
        "https://www.telecel.ml/promotions",
        "https://telecel.ml/offres",
        "https://telecel.ml",
    ],
    "orange": [
        "https://www.orange.ml/offres-et-services",
        "https://www.orange.ml/forfaits",
        "https://www.orange.ml/promotions",
        "https://orange.ml/boutique",
        "https://orange.ml",
    ],
    "moov": [
        "https://www.moovafricamalitel.ml/offres",
        "https://www.moovafricamalitel.ml/forfaits",
        "https://www.malitel.ml/offres",
        "https://moovafricamalitel.ml",
        "https://malitel.ml",
    ],
}

PRICE_RE    = re.compile(r'[\d\s]{1,8}(?:FCFA|F\.?CFA|CFA|Fcfa)', re.I)
DATA_RE     = re.compile(r'(\d+(?:[,.]\d+)?)\s*(Go|GB|Mo|MB)', re.I)
VALIDITY_RE = re.compile(r'(\d+)\s*(jour|day|heure|hour|mois|month|semaine|week)', re.I)


# ──────────────────────────────────────────────────────────────────────────────
# POINT D'ENTRÉE PRINCIPAL
# ──────────────────────────────────────────────────────────────────────────────
def scrape_all() -> dict:
    """
    Scrape les 3 opérateurs. Retourne :
      {
        "promos": [...],
        "status": {
          "telecel": {"source": "scraped"|"generated", "url": "...", "count": n, "at": "..."},
          ...
        },
        "scraped_at": "ISO datetime",
        "next_update": "ISO datetime",
      }
    """
    now  = datetime.now()
    next_upd = (now + timedelta(hours=1)).isoformat()
    all_promos = []
    status = {}

    for op in ["telecel", "orange", "moov"]:
        promos, src, url = _scrape_operator(op)
        all_promos.extend(promos)
        status[op] = {
            "source":  src,
            "url":     url or "—",
            "count":   len(promos),
            "at":      now.isoformat(),
        }
        logger.info(f"[{op.upper()}] {len(promos)} offres — source={src}")

    return {
        "promos":      all_promos,
        "status":      status,
        "scraped_at":  now.isoformat(),
        "next_update": next_upd,
    }


# ──────────────────────────────────────────────────────────────────────────────
# SCRAPING D'UN OPÉRATEUR
# ──────────────────────────────────────────────────────────────────────────────
def _scrape_operator(op: str):
    """Essaie chaque URL de l'opérateur. Retourne (promos, source, url)."""
    for url in OPERATOR_URLS.get(op, []):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False, allow_redirects=True)
            if resp.status_code != 200:
                continue
            html = resp.text
            # Si contenu trop court → probablement JS-rendered (React/Vue/Angular)
            if len(html) < 4000:
                logger.info(f"[{op}] {url} → contenu trop court ({len(html)}b), probablement JS-rendered")
                continue
            soup = BeautifulSoup(html, "html.parser")
            promos = _parse_offers(soup, op, url)
            if promos:
                return promos, "scraped", url
        except requests.exceptions.ConnectionError:
            logger.warning(f"[{op}] Connexion refusée : {url}")
        except requests.exceptions.Timeout:
            logger.warning(f"[{op}] Timeout : {url}")
        except Exception as e:
            logger.warning(f"[{op}] Erreur sur {url} : {e}")

    # Fallback : génération dynamique réaliste
    logger.info(f"[{op}] → fallback génération dynamique")
    return _generate(op), "generated", None


# ──────────────────────────────────────────────────────────────────────────────
# PARSEUR GÉNÉRIQUE HTML
# ──────────────────────────────────────────────────────────────────────────────
def _parse_offers(soup: BeautifulSoup, op: str, source_url: str) -> list:
    """Extrait les offres depuis le HTML parsé avec BeautifulSoup."""
    # Supprimer le bruit
    for tag in soup.find_all(["nav","header","footer","script","style","iframe","svg"]):
        tag.decompose()

    # Sélecteurs CSS typiques des sites télécom
    CSS_TARGETS = [
        "[class*='offer']", "[class*='offre']", "[class*='pack']",
        "[class*='forfait']", "[class*='promo']", "[class*='card']",
        "[class*='product']", "[class*='service']", "[class*='tarif']",
        "article", ".item", ".box",
    ]
    candidates = []
    for sel in CSS_TARGETS:
        found = soup.select(sel)
        if len(found) >= 2:
            candidates.extend(found)
            break

    # Fallback : éléments contenant un prix FCFA
    if not candidates:
        for el in soup.find_all(["div","section","article","li"]):
            txt = el.get_text(" ", strip=True)
            if PRICE_RE.search(txt) and 40 < len(txt) < 800:
                candidates.append(el)

    promos = []
    seen   = set()

    for el in candidates[:10]:
        txt = el.get_text(" ", strip=True)
        if len(txt) < 25:
            continue

        # Titre
        h = el.find(["h1","h2","h3","h4","h5","strong","b"])
        title = (h.get_text(strip=True) if h else txt[:60])[:80]
        if not title or len(title) < 4 or title in seen:
            continue
        seen.add(title)

        # Prix
        pm = PRICE_RE.search(txt)
        price = pm.group(0).strip() if pm else ""

        # Validité
        vm = VALIDITY_RE.search(txt)
        validity = f"{vm.group(1)} {vm.group(2)}{'s' if vm else ''}" if vm else ""

        # Catégorie
        tl = txt.lower()
        if any(w in tl for w in ["go","gb","internet","data","4g","5g","wifi"]):
            cat = "data"
        elif any(w in tl for w in ["money","flooz","transfert","transfer","paiement"]):
            cat = "money"
        elif any(w in tl for w in ["appel","call","voix","voix","min"]):
            cat = "voice"
        elif "sms" in tl:
            cat = "sms"
        elif any(w in tl for w in ["combo","tout","all","pack complet"]):
            cat = "combo"
        elif any(w in tl for w in ["fibre","fixe","vsat","mpls"]):
            cat = "fixe"
        elif any(w in tl for w in ["entreprise","business","pro ","société","m2m","iot"]):
            cat = "enterprise"
        else:
            cat = "combo"

        seg = "b2b" if any(w in tl for w in ["entreprise","business","pme","société","pro "]) else "b2c"

        # Extraire les avantages (phrases courtes)
        features = []
        for line in txt.split("."):
            line = line.strip()
            if 8 < len(line) < 80 and line != title:
                features.append(line)
        features = features[:4]

        promos.append(_make(op, seg, cat, title, txt[:200], price, validity,
                            features, source="scraped", source_url=source_url))

    return promos


# ──────────────────────────────────────────────────────────────────────────────
# GÉNÉRATEUR DYNAMIQUE (fallback réaliste)
# ──────────────────────────────────────────────────────────────────────────────
def _generate(op: str) -> list:
    """
    Génère des offres réalistes et variées quand le scraping échoue.
    Les prix, volumes et validités varient légèrement à chaque appel
    pour simuler l'évolution naturelle du marché.
    """
    rng  = random.Random()
    nd   = lambda d: (datetime.now() + timedelta(days=d)).strftime("%Y-%m-%dT%H:%M")
    v    = lambda base, pct=0.15: int(base * (1 + rng.uniform(-pct, pct)) // 50) * 50

    if op == "telecel":
        return [
            _make(op,"b2c","data",
                  f"Go+ Quotidien {rng.choice(['Standard','Turbo','Max'])}",
                  "Internet 4G valable 24 heures, accès rapide sans engagement.",
                  f"{v(100)} FCFA","24 heures",
                  ["1 Go internet 4G","Validité 24h","WhatsApp inclus"],
                  isn=True, exp=nd(30)),
            _make(op,"b2c","data",
                  f"Super Semaine {v(5)}Go",
                  "Naviguez librement pendant 7 jours avec les réseaux sociaux offerts.",
                  f"{v(500)} FCFA","7 jours",
                  [f"{v(5)} Go internet 4G","Réseaux sociaux illimités","Valable 7 jours"],
                  ish=True, hl=True, exp=nd(14)),
            _make(op,"b2c","combo",
                  "All-in-One Mensuel Telecel",
                  "Le forfait tout-en-un incontournable de Telecel Mali.",
                  f"{v(2500)} FCFA","30 jours",
                  [f"{v(10)} Go internet 4G/5G",f"{v(200)} min tous réseaux","300 SMS","WhatsApp illimité"],
                  isn=True, ish=True, hl=True),
            _make(op,"b2c","money",
                  f"Telecel Cash — Commission à {rng.choice(['-30%','-50%','0 FCFA'])}",
                  "Économisez sur vos transferts et paiements Telecel Cash.",
                  f"{rng.choice(['Gratuit','À partir de 0 FCFA'])}",f"Jusqu'au {nd(12)[:10]}",
                  ["Transfert sans frais","Retrait réduit","Paiement marchand offert"],
                  isn=True, ish=True, exp=nd(12)),
            _make(op,"b2c","voice",
                  "Appels Illimités Telecel+",
                  "Appelez vos proches Telecel sans vous soucier du crédit.",
                  f"{v(1000)} FCFA","30 jours",
                  ["Appels illimités Telecel","50 min autres réseaux","200 SMS"]),
            _make(op,"b2b","enterprise",
                  "Pack Entreprise Telecel",
                  "Internet dédié, lignes professionnelles et support prioritaire 24/7.",
                  f"{v(50000)} FCFA/mois","Engagement 12 mois",
                  ["Internet dédié 10 Mbps","10 lignes pro illimitées","Support 24/7","Dashboard admin"],
                  hl=True, contact="+223 20 22 00 00 | business@telecel.ml"),
            _make(op,"b2b","fixe",
                  "Internet Fixe Pro Telecel",
                  "Connexion haut débit dédiée pour votre bureau.",
                  f"{v(25000)} FCFA/mois","Sans engagement",
                  [f"{v(10)} à {v(100)} Mbps","IP fixe","Installation gratuite","SLA 99,9%"],
                  isn=True, contact="+223 20 22 00 00"),
        ]

    if op == "orange":
        return [
            _make(op,"b2c","data",
                  f"Forfait Orange {v(2)}Go Semaine",
                  "Internet 4G+ pour rester connecté toute la semaine.",
                  f"{v(500)} FCFA","7 jours",
                  [f"{v(2)} Go internet 4G+","Facebook & WhatsApp inclus","7 jours"]),
            _make(op,"b2c","data",
                  f"Big Data {v(30)}Go Orange",
                  "Le méga-forfait mensuel pour les gros consommateurs de data.",
                  f"{v(5000)} FCFA","30 jours",
                  [f"{v(30)} Go internet 4G+","YouTube HD illimité","Nuit illimitée 0h–5h","Partage connexion"],
                  ish=True, hl=True),
            _make(op,"b2c","money",
                  f"Orange Money — {rng.choice(['0 Commission','Transfert Gratuit','-50% Frais'])}",
                  "Profitez de frais réduits sur vos transferts Orange Money ce mois.",
                  "0 FCFA commission",f"Jusqu'au {nd(rng.randint(8,20))[:10]}",
                  ["Transfert gratuit","Paiement factures offert","Retrait -30%"],
                  isn=True, ish=True, hl=True, exp=nd(rng.randint(8,20))),
            _make(op,"b2c","combo",
                  f"MAX Tout Orange {v(15)}Go",
                  "Data + Voix + SMS + Mobile Money — l'offre ultime d'Orange Mali.",
                  f"{v(3500)} FCFA","30 jours",
                  [f"{v(15)} Go internet 4G+","Appels illimités Orange",f"{v(200)} min autres","Bonus Orange Money x2"],
                  isn=True),
            _make(op,"b2c","voice",
                  "Famille Orange — Appels+",
                  "Restez en contact avec toute la famille Orange sans limite.",
                  f"{v(1000)} FCFA","30 jours",
                  ["Appels illimités Orange","100 min autres réseaux","100 SMS"]),
            _make(op,"b2b","enterprise",
                  "Orange Business PME",
                  "La solution numérique complète pour les PME maliennes.",
                  f"{v(25000)} FCFA/mois","Engagement 6 mois",
                  ["Lignes pro illimitées",f"{v(100)} Go data","VPN sécurisé","Cloud 50 Go","Support dédié"],
                  hl=True, contact="+223 20 70 70 70 | business@orange.ml"),
            _make(op,"b2b","money",
                  "Orange Money Entreprise",
                  "Collecte et paiement professionnel avec intégration API.",
                  "Sur devis","Sans engagement",
                  ["Collecte de paiements","API de paiement","Dashboard temps réel","Commission négociée"],
                  isn=True, contact="+223 20 70 70 70"),
            _make(op,"b2b","fixe",
                  "Orange VPN Pro",
                  "Réseau privé virtuel sécurisé multi-sites.",
                  f"{v(15000)} FCFA/mois","Engagement 6 mois",
                  ["VPN MPLS multi-sites","Bande passante garantie","AES-256","Redondance 4G"],
                  contact="+223 20 70 70 70"),
        ]

    if op == "moov":
        return [
            _make(op,"b2c","data",
                  f"Moov Internet {v(3)}Go Semaine",
                  "Navigation fluide pendant toute la semaine avec TikTok et YouTube inclus.",
                  f"{v(500)} FCFA","7 jours",
                  [f"{v(3)} Go internet 4G","TikTok & YouTube inclus","7 jours"]),
            _make(op,"b2c","data",
                  f"Ultra {v(50)}Go Moov",
                  "Le forfait ultime de Moov Africa Malitel pour un mois de navigation totale.",
                  f"{v(7500)} FCFA","30 jours",
                  [f"{v(50)} Go internet 4G+","Streaming HD illimité","5G disponible","Partage 5 appareils"],
                  ish=True, hl=True),
            _make(op,"b2c","money",
                  f"Flooz — Commission {rng.choice(['-50%','-40%','-30%','Offerte'])}",
                  "Économisez sur toutes vos transactions Flooz (Moov Money) ce mois.",
                  f"{rng.choice(['-50%','-40%'])} commission",f"Jusqu'au {nd(rng.randint(7,15))[:10]}",
                  ["Transfert réduit","Retrait moins cher","Paiement marchand Flooz gratuit"],
                  isn=True, ish=True, exp=nd(rng.randint(7,15))),
            _make(op,"b2c","combo",
                  f"Moov All {v(10)}Go Mensuel",
                  "Rapport qualité-prix imbattable : data + appels + SMS.",
                  f"{v(2000)} FCFA","30 jours",
                  [f"{v(10)} Go internet 4G",f"{v(150)} min tous réseaux","200 SMS","WhatsApp & Facebook inclus"],
                  isn=True),
            _make(op,"b2c","voice",
                  "Moov Appels+ Tous Réseaux",
                  "Restez joignable par tous, sur tous les réseaux maliens.",
                  f"{v(1000)} FCFA","30 jours",
                  ["Moov-Moov illimité",f"{v(100)} min autres réseaux","50 SMS"]),
            _make(op,"b2b","enterprise",
                  "Moov M2M / IoT Connect",
                  "Solutions Machine-to-Machine pour agriculture, transport et industrie.",
                  "Sur devis","Contrat annuel",
                  ["SIM M2M dédiées","Plateforme IoT","Suivi GPS flotte","Alertes temps réel","API RESTful"],
                  isn=True, hl=True, contact="+223 20 08 00 00 | m2m@moov.ml"),
            _make(op,"b2b","fixe",
                  "Moov Internet Dédié Entreprise",
                  "Fibre optique et VSAT pour zones urbaines et rurales, SLA garanti.",
                  f"À partir de {v(30000)} FCFA/mois","Engagement 12 mois",
                  [f"{v(5)} à {v(50)} Mbps garanti","IP fixe dédiée","SLA 99,5%","Routeur fourni","Support 24/7"],
                  contact="+223 20 08 00 00"),
        ]
    return []


# ──────────────────────────────────────────────────────────────────────────────
# USINE À PROMOS
# ──────────────────────────────────────────────────────────────────────────────
def _make(op, seg, cat, title, desc, price, validity, features,
          isn=False, ish=False, hl=False, exp=None, contact="", source="generated", source_url=None):
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
