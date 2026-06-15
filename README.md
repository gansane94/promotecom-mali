# 📡 PromoTélécom Mali — Automatisé 100%

> Suivi automatique des promotions télécom au Mali — B2C & B2B  
> **Développé par Sayoba GANSANE** · © 2025  
> Aucune intervention manuelle requise

---

## 🤖 Comment ça marche tout seul ?

```
┌─────────────────────────────────────────────────────────────┐
│  Toutes les heures (automatique)                            │
│                                                             │
│  scraper.py  ──►  Sites opérateurs  ──►  Firebase / JSON   │
│   • Telecel.ml        🌐 Scraped                            │
│   • Orange.ml         ⚙️ Généré si indisponible             │
│   • Moovafricamalitel.ml                                    │
└─────────────────────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Toutes les 60 secondes (automatique)                       │
│                                                             │
│  app.py → Streamlit → Affichage mis à jour                  │
│   • Ticker live défilant                                    │
│   • Cartes B2C & B2B                                        │
│   • Compteur de visites                                     │
│   • Statut scraping par opérateur                           │
└─────────────────────────────────────────────────────────────┘
```

**Stratégie du scraper :**
1. 🌐 **Tentative réelle** — `requests` + `BeautifulSoup` sur les sites opérateurs
2. ⚙️ **Fallback dynamique** — Si le site est JS-only/bloqué/hors ligne, génère des offres réalistes et variées
3. 🏷️ **Badge source** — Chaque offre indique si elle est `Scraped` ou `Auto-générée`

---

## 🚀 Lancement en 3 commandes

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer (aucune autre configuration requise)
streamlit run app.py

# 3. Ouvrir dans le navigateur
# → http://localhost:8501
```

✅ L'application scrape immédiatement les 3 opérateurs au démarrage.  
✅ Elle se met à jour toutes les heures automatiquement.  
✅ L'interface se rafraîchit toutes les 60 secondes.

---

## 🔥 Activer Firebase (sync temps réel multi-utilisateurs)

### Étape 1 — Créer un projet Firebase gratuit

1. Allez sur [console.firebase.google.com](https://console.firebase.google.com)
2. **Ajouter un projet** → nom : `promotecom-mali` → Créer
3. **Build** → **Firestore Database** → Créer → Mode production → `europe-west`

### Étape 2 — Règles Firestore

```js
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read: if true;
      allow write: if true;
    }
  }
}
```

### Étape 3 — Clé de service

1. ⚙️ **Paramètres du projet** → **Comptes de service**
2. **Générer une nouvelle clé privée** → télécharger le `.json`
3. Renommer en `firebase_service_account.json` et placer à la racine

### Étape 4 — Lancer

```bash
streamlit run app.py
```

🔥 Le scraper stocke maintenant dans Firestore.  
🔥 Tous les visiteurs voient les mêmes données en temps réel.

---

## ☁️ Déployer gratuitement sur Streamlit Cloud

1. Pushez le dossier sur **GitHub**
2. [share.streamlit.io](https://share.streamlit.io) → **New app** → sélectionner `app.py`
3. **Advanced settings** → **Secrets** → coller votre config Firebase :

```toml
[firebase]
type = "service_account"
project_id = "promotecom-mali"
private_key_id = "xxx"
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "firebase-adminsdk@promotecom-mali.iam.gserviceaccount.com"
client_id = "xxx"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

4. **Deploy** — l'URL est partageable avec tout le monde !

---

## 📁 Structure des fichiers

```
promotecom-mali-streamlit/
├── app.py                          ← Interface Streamlit (auto-refresh 60s)
├── scraper.py                      ← Moteur de scraping (auto toutes les heures)
├── requirements.txt                ← 8 dépendances Python
├── firebase_service_account.json   ← (À créer) Clé Firebase
├── .streamlit/
│   ├── config.toml                 ← Thème dark
│   └── secrets.toml.example        ← Template secrets Firebase
└── data/                           ← (Auto-créé) Cache local
    ├── promos.json                 ← Dernières offres scrapées
    ├── scrape_meta.json            ← Statut du dernier scraping
    └── stats.json                  ← Compteur de visites
```

---

## 🔬 Fonctionnement du scraper

Le fichier `scraper.py` essaie dans l'ordre :

| Étape | Action | Résultat |
|-------|--------|---------|
| 1 | GET sur les URLs de l'opérateur | HTML reçu ? |
| 2 | Contenu > 4 000 caractères ? | JS-rendered si non |
| 3 | BeautifulSoup → recherche de cartes offre | Offres trouvées ? |
| 4 | Extraction prix FCFA, titres, catégories | Structuré |
| 5 | Si tout échoue → générateur dynamique | Toujours des offres |

**Catégories détectées automatiquement :**
- 📶 Data (Go, GB, internet, 4G, 5G)
- 📞 Voix (appel, min, voix)
- 💳 Mobile Money (money, flooz, transfert)
- 💬 SMS
- 🎁 Combo (pack, tout, all)
- 🌐 Internet Fixe (fibre, vsat, mpls)
- 🏢 Solutions Pro (entreprise, business, m2m)

---

## 📊 Compteur de visites

Stocké dans **Firebase** (si configuré) ou **`data/stats.json`** (local) :
- Total des visites depuis le lancement
- Visites du jour
- Graphique des 7 derniers jours (sidebar)
- Horodatage de la dernière visite

---

## 👤 Auteur

**Sayoba GANSANE**  
Développeur · Mali  
📧 gansane94@gmail.com

---

## 📄 Licence

Projet open source — libre d'utilisation et de modification.  
Merci de créditer **Sayoba GANSANE** en cas de réutilisation.
