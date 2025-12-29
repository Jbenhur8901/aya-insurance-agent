# 📲 Intégration Mobile Money - Configuration

## 🔧 Configuration requise

### 1. Variables d'environnement (`.env`)

```bash
# API ePay (Mobile Money)
EPAY_API_KEY=votre_cle_api_epay

# URL de base pour les webhooks
BASE_WEBHOOK_URL=https://votre-domaine.com
```

### 2. URL de Callback

**URL unique pour MTN Mobile Money ET Airtel Money:**
```
https://votre-domaine.com/api/payment/callback/payment-notification
```

Cette URL doit être configurée dans votre compte ePay pour recevoir les notifications de paiement.

## 📡 Endpoints disponibles

### Callback principal (recommandé)
- **POST** `/api/payment/callback/payment-notification`
- Compatible avec MTN MoMo et Airtel Money
- Format du callback:
```json
{
  "transaction_reference": "NSIA-20251229-abc123",
  "status": "success",
  "provider": "momo",
  "amount": 50000,
  ...
}
```

### Endpoints legacy (compatibilité)
- **POST** `/api/payment/callback/momo` (redirige vers payment-notification)
- **POST** `/api/payment/callback/airtel` (redirige vers payment-notification)

## 🔄 Flux de paiement

1. **Initiation du paiement:**
   ```
   Client → Agent AYA → API ePay
   ```
   - L'agent appelle `initiate_momo_payment()` ou `initiate_airtel_payment()`
   - Le webhook URL est automatiquement envoyé à l'API ePay

2. **Callback de notification:**
   ```
   API ePay → Notre serveur (/api/payment/callback/payment-notification)
   ```
   - Statut API converti vers enum DB
   - Transaction mise à jour
   - Si paiement validé → Souscription mise à jour automatiquement

3. **Mapping des statuts:**
   ```
   API ePay          →  DB Status
   "success"         →  "valide"
   "failed"          →  "annulée"
   "pending"         →  "en_attente"
   "processing"      →  "en_cours"
   ```

## 🗄️ Structure de la base de données

### Ordre de création (IMPORTANT):

1. **Client** (table `clients`)
2. **Souscription** (table `souscriptions`)
   - `status`: "en_cours", "valide", "expirée", "annulée", "en_attente"
   - `producttype`: "NSIA AUTO", "NSIA VOYAGE", etc.
3. **Détails produit** (table spécifique: `souscription_auto`, `souscription_voyage`, etc.)
   - ⚠️ Ces tables n'ont PAS de colonne `status`
4. **Transaction** (table `transactions`)
   - `payment_method`: "MTN_MOBILE_MONEY", "AIRTEL_MOBILE_MONEY", etc.
   - `status`: "en_cours", "valide", "expirée", "annulée", "en_attente"

### Relations:
```
clients
  ↓ (client_id FK)
souscriptions
  ↓ (souscription_id FK)
  ├─→ souscription_auto
  ├─→ souscription_voyage
  ├─→ souscription_iac
  ├─→ souscription_mrh
  └─→ transactions
```

## ✅ Checklist de déploiement

- [ ] Configurer `EPAY_API_KEY` dans les variables d'environnement
- [ ] Configurer `BASE_WEBHOOK_URL` avec l'URL publique du serveur
- [ ] Vérifier que le serveur est accessible depuis l'extérieur (pas localhost)
- [ ] Enregistrer l'URL de callback dans le portail ePay:
  ```
  https://votre-domaine.com/api/payment/callback/payment-notification
  ```
- [ ] Tester avec un paiement réel MTN MoMo
- [ ] Tester avec un paiement réel Airtel Money
- [ ] Vérifier les logs pour confirmer la réception des callbacks
- [ ] Vérifier que les statuts sont correctement mis à jour dans la DB

## 🧪 Test du callback (développement)

Pour tester localement avec ngrok:

```bash
# 1. Lancer ngrok
ngrok http 8000

# 2. Mettre à jour .env
BASE_WEBHOOK_URL=https://votre-url-ngrok.ngrok.io

# 3. Redémarrer le serveur
python -m uvicorn app.main:app --reload

# 4. Tester manuellement le callback
curl -X POST https://votre-url-ngrok.ngrok.io/api/payment/callback/payment-notification \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_reference": "NSIA-20251229-test123",
    "status": "success",
    "provider": "momo",
    "amount": 50000
  }'
```

## 📊 Logs importants

Lors d'un paiement réussi, vous devriez voir:

```
📲 Webhook URL configurée: https://votre-domaine.com/api/payment/callback/payment-notification
💳 Initiation paiement MTN MoMo: 50000 FCFA pour 242XXXXXXXXX
✅ Paiement MTN MoMo initié: NSIA-20251229-abc123
📲 Callback paiement reçu: {...}
🔍 Transaction: NSIA-20251229-abc123, Status: success, Provider: momo
Statut converti: success → valide
✅ Souscription abc-def-ghi validée
✅ Paiement confirmé stocké dans Redis: NSIA-20251229-abc123
```

## 🆘 Troubleshooting

### Le callback n'arrive jamais
- Vérifier que `BASE_WEBHOOK_URL` est une URL publique (pas localhost)
- Vérifier que l'URL est correctement enregistrée dans le portail ePay
- Vérifier les logs du serveur
- Vérifier le firewall/security groups

### Les statuts ne sont pas mis à jour
- Vérifier le mapping des statuts dans `payment_webhook.py`
- Vérifier les logs pour voir le statut reçu
- Vérifier que la transaction existe bien dans la DB

### Erreur "Could not find the 'status' column"
- ✅ **Résolu:** Les tables spécifiques (`souscription_auto`, etc.) n'ont PAS de colonne `status`
- Le `status` existe uniquement dans la table `souscriptions`
