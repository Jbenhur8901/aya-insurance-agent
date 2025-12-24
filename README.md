# 🤖 AYA Insurance Agent

**AYA** est une conseillère digitale basée sur l'intelligence artificielle qui facilite la souscription d'assurances NSIA directement depuis WhatsApp.

Développé par **Nodes Technology** pour **NSIA Assurances Congo**.

---

## 📋 Table des Matières

- [Caractéristiques](#-caractéristiques)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [API Endpoints](#-api-endpoints)
- [Déploiement](#-déploiement)
- [Licence](#-licence)

---

## ✨ Caractéristiques

### Fonctionnalités Principales

- 🤖 **Système Multi-Agent** : Architecture agentic avec 6 agents spécialisés
- 📸 **Vision AI** : Analyse automatique de documents (carte grise, passeport, CNI, NIU)
- 💰 **Calcul Tarifaire** : Quotations automatiques pour tous les produits
- 💳 **Paiement Mobile** : Intégration MTN MoMo et Airtel Money
- 📄 **Génération PDF** : Reçus et attestations automatiques
- 💬 **WhatsApp** : Expérience 100% conversationnelle
- 🗄️ **Base de Données** : Supabase PostgreSQL
- 🧠 **Mémoire Contextuelle** : Redis pour la gestion des sessions

### Produits Supportés

1. **Assurance Auto** 🚗 - Véhicules personnels et transport public
2. **Assurance Voyage** ✈️ - Couverture internationale
3. **Individuelle Accident** 👨‍💼 - Protection personnelle
4. **Multirisque Habitation** 🏠 - Protection du logement

### Performances

- ⚡ **96× plus rapide** que le processus traditionnel
- ⏱️ **3 minutes** pour une souscription complète
- 🌐 **Disponible 24/7**
- 📊 **5× plus de conversion**

---

## 🏗️ Architecture

### Vue d'ensemble

```
┌─────────────────────┐
│  UChat (WhatsApp)   │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   FastAPI Server    │
│  /webhook/uchat     │
└──────────┬──────────┘
           │
┌──────────▼───────────────────────────────┐
│       AYA SUPERVISOR AGENT               │
│  (Orchestrateur + Gestion du contexte)   │
└──────────┬───────────────────────────────┘
           │
    ┌──────┴──────┬─────────┬──────────┬─────────┬──────────┐
    │             │         │          │         │          │
┌───▼────┐  ┌────▼───┐ ┌───▼────┐ ┌──▼─────┐ ┌─▼──────┐ ┌─▼────────┐
│Vision  │  │Product │ │Quota-  │ │Database│ │Payment │ │ Receipt  │
│Agent   │  │Agent   │ │tion    │ │Agent   │ │Agent   │ │ Agent    │
│        │  │        │ │Agent   │ │        │ │        │ │          │
└────────┘  └────────┘ └────────┘ └────────┘ └────────┘ └──────────┘
```

### Les 6 Agents Spécialisés

| Agent | Rôle | Technologies |
|-------|------|--------------|
| **Supervisor** | Orchestration et routage | OpenAI GPT-4o-mini |
| **Vision** | Analyse de documents | Google Gemini 2.0 Flash |
| **Quotation** | Calcul des tarifs | Pandas, Excel |
| **Database** | Gestion BDD | Supabase PostgreSQL |
| **Payment** | Paiements Mobile Money | API epay.nodes-hub.com |
| **Receipt** | Génération de documents | WeasyPrint, Segno |

### Stack Technique

- **Backend**: FastAPI (Python 3.11+)
- **IA**: OpenAI GPT-4o-mini, Google Gemini 2.0
- **Base de Données**: Supabase (PostgreSQL)
- **Cache/Mémoire**: Redis (Upstash)
- **Messaging**: UChat (WhatsApp)
- **Paiements**: MTN MoMo, Airtel Money
- **PDF**: WeasyPrint, Segno (QR codes)

---

## 🚀 Installation

### Prérequis

- Python 3.11+
- Redis (ou compte Upstash)
- Compte Supabase
- Clés API (OpenAI, Gemini, UChat, epay)

### Installation

```bash
# Cloner le repository
git clone https://github.com/your-org/aya-insurance-agent.git
cd aya-insurance-agent

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### 1. Variables d'environnement

Copier `.env.example` vers `.env` et remplir les valeurs :

```bash
cp .env.example .env
```

Éditer `.env` :

```env
# OpenAI
OPENAI_API_KEY=sk-your-key-here

# Gemini
GEMINI_API_KEY=your-key-here

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Redis/Upstash
REDIS_URL=https://your-redis.upstash.io
REDIS_TOKEN=your-token

# Mobile Money
EPAY_API_KEY=your-epay-key

# UChat
UCHAT_API_KEY=your-uchat-key
UCHAT_BASE_URL=https://api.uchat.com.au

# Webhooks
BASE_WEBHOOK_URL=https://your-domain.com
```

### 2. Base de Données Supabase

Le schéma de base de données est fourni dans le manuel. Tables principales :

- `clients` - Informations clients
- `souscriptions` - Souscriptions principales
- `souscription_auto`, `souscription_voyage`, `souscription_iac`, `souscription_mrh` - Détails produits
- `transactions` - Transactions de paiement
- `documents` - Documents générés
- `code_promo` - Codes promotionnels

### 3. Fichiers de Données

Placer les fichiers dans le dossier `data/` :

- `tarification_nsia_auto.xlsx` - Grille tarifaire AUTO
- `voyage.csv` - Tarifs VOYAGE

---

## 💻 Utilisation

### Démarrer le serveur

```bash
# Mode développement (avec reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Mode production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Le serveur démarre sur `http://localhost:8000`

### Documentation API

- Swagger UI : `http://localhost:8000/docs`
- ReDoc : `http://localhost:8000/redoc`

---

## 📡 API Endpoints

### Webhooks

#### POST `/api/webhook/uchat`
Webhook principal pour recevoir les messages WhatsApp depuis UChat.

**Request Body:**
```json
{
  "session_id": "session_123",
  "user_phone": "+242066123456",
  "message_type": "text",
  "content": "Bonjour",
  "media_url": null,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Response:**
```json
{
  "reply": "Bonjour! Je suis AYA, votre conseillère digitale NSIA..."
}
```

#### POST `/api/payment/callback/momo`
Webhook pour les callbacks de paiement MTN Mobile Money.

#### POST `/api/payment/callback/airtel`
Webhook pour les callbacks de paiement Airtel Money.

### Utilitaires

#### GET `/`
Endpoint racine - Informations sur l'API.

#### GET `/api/health`
Health check - Vérification du statut de l'API.

---

## 🌐 Déploiement

### Déploiement sur Railway/Render/Fly.io

1. **Préparer les variables d'environnement** dans le dashboard

2. **Déployer depuis GitHub** :
   ```bash
   # Railway
   railway up

   # Render
   # Connecter le repo GitHub dans le dashboard

   # Fly.io
   fly deploy
   ```

3. **Configurer les webhooks** :
   - UChat webhook URL : `https://your-domain.com/api/webhook/uchat`
   - Payment webhooks : `https://your-domain.com/api/payment/callback/{provider}`

### Déploiement Docker (Optionnel)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build
docker build -t aya-insurance-agent .

# Run
docker run -p 8000:8000 --env-file .env aya-insurance-agent
```

---

## 🔧 Développement

### Structure du Projet

```
aya-insurance-agent/
├── app/
│   ├── agents/              # Les 6 agents spécialisés
│   │   ├── supervisor.py
│   │   ├── vision_agent.py
│   │   ├── quotation_agent.py
│   │   ├── database_agent.py
│   │   ├── payment_agent.py
│   │   └── receipt_agent.py
│   │
│   ├── api/                 # Endpoints FastAPI
│   │   ├── webhook.py
│   │   └── payment_webhook.py
│   │
│   ├── models/              # Modèles Pydantic
│   │   ├── schemas.py
│   │   └── state.py
│   │
│   ├── services/            # Services externes
│   │   ├── supabase_client.py
│   │   ├── redis_client.py
│   │   ├── mobile_money.py
│   │   └── uchat_client.py
│   │
│   ├── tools/               # Outils métier
│   │   ├── quotation.py
│   │   ├── receipts.py
│   │   └── agents.py
│   │
│   ├── config.py            # Configuration
│   └── main.py              # Application FastAPI
│
├── data/                    # Données tarifaires
├── templates/               # Templates HTML pour PDF
├── .env.example             # Exemple de configuration
├── requirements.txt         # Dépendances Python
└── README.md
```

### Tests

```bash
# Installer les dépendances de test
pip install pytest pytest-asyncio httpx

# Lancer les tests
pytest
```

---

## 📊 Monitoring & Logs

Les logs sont configurés au niveau INFO par défaut. Pour activer le mode DEBUG :

```env
DEBUG=True
```

Les logs incluent :
- Réception des messages
- Décisions du Supervisor
- Analyse de documents
- Calculs de quotation
- Initiations de paiement
- Génération de PDF

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Veuillez suivre ces étapes :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

## 📞 Support

Pour toute question ou support :

- **Email**: contact@nodes-hub.com
- **Téléphone**: +242 065 13 44 47 / +242 044 74 48 77
- **Site Web**: [nodes-hub.com](https://nodes-hub.com)

---

## 📄 Licence

© 2025 Nodes Technology & NSIA Assurances Congo. Tous droits réservés.

---

## 🙏 Remerciements

- **NSIA Assurances Congo** - Partenaire stratégique
- **Université Denis Sassou Nguesso** - Centre Africain de Recherche en IA
- **OpenAI** - Modèles GPT
- **Google** - Gemini Vision AI
- **Nodes Technology Team** - Développement et innovation

---

**Développé avec ❤️ par Nodes Technology**

*L'avenir de l'assurance en Afrique commence maintenant*
