# 🚀 Démarrage Rapide - Système Agentique AYA

## ⚡ Installation en 3 étapes

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

**Nouvelle dépendance clé :** `openai-agents==0.6.4`

### 2. Configurer les variables d'environnement

Copiez `.env.example` vers `.env` et remplissez :

```env
# OBLIGATOIRE
OPENAI_API_KEY=sk-your-key-here
GEMINI_API_KEY=your-gemini-key

# Base de données et mémoire
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key
REDIS_URL=https://your-redis.upstash.io
REDIS_TOKEN=your-token

# Paiements
EPAY_API_KEY=your-epay-key
```

### 3. Démarrer le serveur

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Accédez à : http://localhost:8000/docs

---

## 🎯 Test rapide

### Message simple

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -F "msg=Bonjour" \
  -F "session_id=test_001" \
  -F "user_phone=+242066123456"
```

### Workflow complet AUTO

1. **Accueil:**
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -F "msg=Bonjour" \
  -F "session_id=auto_test" \
  -F "user_phone=+242066111111"
```

2. **Choisir AUTO:**
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -F "msg=1" \
  -F "session_id=auto_test" \
  -F "user_phone=+242066111111"
```

3. **Envoyer carte grise:**
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -F "msg=Voici ma carte grise" \
  -F "session_id=auto_test" \
  -F "user_phone=+242066111111" \
  -F "message_type=image" \
  -F "media_url=https://example.com/carte_grise.jpg"
```

L'agent va **automatiquement** :
- ✅ Analyser la carte grise
- ✅ Calculer les 3 tarifs (3M, 6M, 12M)
- ✅ Présenter les offres

4. **Choisir période:**
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -F "msg=12M" \
  -F "session_id=auto_test" \
  -F "user_phone=+242066111111"
```

L'agent va **automatiquement** :
- ✅ Créer/récupérer le client
- ✅ Créer la souscription
- ✅ Demander le mode de paiement

5. **Choisir paiement:**
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -F "msg=1" \
  -F "session_id=auto_test" \
  -F "user_phone=+242066111111"
```

L'agent va **automatiquement** :
- ✅ Initier le paiement MTN MoMo
- ✅ Générer la référence
- ✅ Enregistrer la transaction
- ✅ Donner les instructions USSD

---

## 📁 Fichiers créés/modifiés

### Nouveaux fichiers

1. **`app/tools/agent_tools.py`**
   - 10 function_tools pour vision, quotation, database, payment
   - ~600 lignes de code

2. **`app/agents/orchestrator.py`**
   - Orchestrateur principal AYA
   - Instructions complètes pour l'agent
   - Gestion automatique du workflow
   - ~350 lignes

3. **`SYSTEME_AGENTIQUE.md`**
   - Documentation complète du système
   - Architecture, outils, workflow
   - ~500 lignes

4. **`OPENAI_AGENT_USAGE.md`**
   - Guide d'utilisation de l'OpenAI Agent SDK
   - Exemples d'utilisation
   - ~400 lignes

### Fichiers modifiés

1. **`app/api/chat.py`**
   - Simplifié de 300+ lignes → ~160 lignes
   - Utilise maintenant l'orchestrateur
   - Logique beaucoup plus simple

2. **`requirements.txt`**
   - Ajouté `openai-agents==0.6.4`

---

## 🎯 Avantages du nouveau système

| Avant | Après |
|-------|-------|
| Logique hardcodée dans l'endpoint | Orchestrateur intelligent autonome |
| 300+ lignes de if/else | 30 lignes simples |
| Difficile à maintenir | Facile à étendre |
| Workflow rigide | Workflow flexible |
| Pas de mémoire contextuelle optimale | Mémoire gérée par le SDK |

---

## 📚 Documentation complète

- **Architecture système** : `SYSTEME_AGENTIQUE.md`
- **Guide OpenAI SDK** : `OPENAI_AGENT_USAGE.md`
- **README principal** : `README.md`

---

## 🆘 Dépannage

### Le module 'agents' n'est pas trouvé

```bash
pip install openai-agents==0.6.4
```

### Erreur OPENAI_API_KEY

Vérifiez que la clé est dans `.env` :
```env
OPENAI_API_KEY=sk-proj-...
```

### Erreur Gemini Vision

Vérifiez que la clé Gemini est configurée :
```env
GEMINI_API_KEY=your-gemini-key
```

---

**🎉 Prêt à démarrer ! Bonne chance !**
