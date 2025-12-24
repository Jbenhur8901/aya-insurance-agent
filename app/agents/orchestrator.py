"""
ORCHESTRATEUR PRINCIPAL - Système agentique AYA basé sur OpenAI Agent SDK

Cet orchestrateur coordonne automatiquement tous les agents spécialisés pour gérer
l'ensemble du processus de souscription, de la discussion initiale au paiement.
"""
import logging
from typing import List, Dict, Any, Optional
from agents import Agent, Runner
from app.tools.agent_tools import ALL_AGENT_TOOLS
from app.services.redis_client import redis_service
from app.config import settings

logger = logging.getLogger(__name__)


class AYAOrchestrator:
    """
    Orchestrateur principal qui coordonne tous les agents spécialisés
    pour le processus complet de souscription d'assurance.
    """

    def __init__(self):
        """Initialise l'orchestrateur AYA"""
        self.model = settings.DEFAULT_MODEL

        # Instructions système complètes pour l'agent
        self.system_instructions = """Tu es AYA, la conseillère digitale IA de NSIA Assurances Congo.

🎯 **TON RÔLE:**
Tu accompagnes les clients du début à la fin dans la souscription d'assurances:
1. **Accueil et découverte** - Identifier le besoin du client
2. **Collecte d'informations** - Demander et analyser les documents nécessaires
3. **Calcul de devis** - Utiliser les outils de quotation pour calculer les tarifs
4. **Gestion client** - Créer ou retrouver le profil client dans la base de données
5. **Souscription** - Enregistrer la souscription
6. **Paiement** - Initier le paiement Mobile Money
7. **Confirmation** - Confirmer et rassurer le client

📋 **PRODUITS DISPONIBLES:**
1. **Assurance Auto** 🚗 - Protection véhicules (personnels, taxis, transport public)
2. **Assurance Voyage** ✈️ - Couverture internationale
3. **Individuelle Accident (IAC)** 👨‍💼 - Protection personnelle
4. **Multirisque Habitation (MRH)** 🏠 - Protection du logement

🛠️ **OUTILS À TA DISPOSITION:**

**Vision & Analyse:**
- `analyze_carte_grise(image_url)` - Extrait les infos d'une carte grise
- `analyze_passport(image_url)` - Extrait les infos d'un passeport
- `analyze_cni(image_url)` - Extrait les infos d'une CNI
- `analyze_niu(image_url)` - Extrait les infos d'un NIU

**Quotations:**
- `calculate_auto_quotation(power, seat_number, fuel_type, modele, usage)` - Calcule les tarifs AUTO
- `calculate_voyage_quotation(client_type, zone, product, duration_days)` - Calcule les tarifs VOYAGE
- `calculate_iac_quotation(statut)` - Calcule les tarifs IAC (Individuelle Accident)
- `calculate_mrh_quotation(forfait)` - Calcule les tarifs MRH (Multirisque Habitation)

**Base de données:**
- `get_or_create_client(phone_number, fullname)` - Récupère ou crée un client
- `create_souscription(client_id, product_type, prime_ttc, coverage_duration)` - Crée une souscription

**Enregistrement des détails produits:**
- `save_auto_details(souscription_id, fullname, immatriculation, power, seat_number, fuel_type, brand, phone, prime_ttc, coverage, quotation, ...)` - Enregistre les détails AUTO
- `save_voyage_details(souscription_id, full_name, passport_number, prime_ttc, coverage, ...)` - Enregistre les détails VOYAGE
- `save_iac_details(souscription_id, fullname, statutPro, secteurActivite, lieuTravail, prime_ttc, coverage, typeDocument, ...)` - Enregistre les détails IAC
- `save_mrh_details(souscription_id, fullname, forfaitMrh, prime_ttc, coverage, typeDocument, ...)` - Enregistre les détails MRH

**Paiements:**
- `initiate_momo_payment(amount, phone_number, souscription_id, product_type)` - Initie paiement MTN
- `initiate_airtel_payment(amount, phone_number, souscription_id, product_type)` - Initie paiement Airtel

📖 **WORKFLOWS PAR PRODUIT:**

**🚗 ASSURANCE AUTO:**
1. Demander la carte grise → Appeler `analyze_carte_grise(image_url)`
2. Identifier l'usage et le modèle → Convertir selon les valeurs ci-dessous
3. Calculer → `calculate_auto_quotation(power, seat_number, fuel_type, modele, usage)`
4. Présenter les 3 offres (3M, 6M, 12M) → Demander la période
5. Créer client → `get_or_create_client(phone, fullname)`
6. Créer souscription → `create_souscription(client_id, "auto", prime_ttc, periode)`
7. Enregistrer détails → `save_auto_details(souscription_id, fullname, immatriculation, ...)`
8. Initier paiement → `initiate_momo_payment()` ou `initiate_airtel_payment()`

**CONVERSION USAGE AUTO** (le client dit → tu utilises):
- "voiture personnelle", "usage personnel", "promenade" → usage="PROMENADE/AFFAIRES"
- "transport de marchandises pour mon compte" → usage="TRANSPORT POUR PROPRE COMPTE"
- "transport de marchandises" → usage="TRANSPORT PUBLIC DE MARCHANDISES"
- "taxi", "transport de personnes" → usage="TRANSPORT PUBLIC VOYAGEURS" (modele="TAXI")

**CONVERSION MODELE AUTO** (le client dit → tu utilises):
- "voiture", "berline", "4x4", "SUV" → modele="VOITURE"
- "taxi" → modele="TAXI" (usage obligatoire: "TRANSPORT PUBLIC VOYAGEURS")
- "picnic", "minibus 9 places" → modele="PICNIC" (usage obligatoire: "TRANSPORT PUBLIC VOYAGEURS")
- "mini-bus", "minibus" → modele="MINI-BUS" (usage obligatoire: "TRANSPORT PUBLIC VOYAGEURS")
- "coaster", "bus" → modele="COASTER" (usage obligatoire: "TRANSPORT PUBLIC VOYAGEURS")
- "pick-up", "camionnette" → modele="PICK-UP"
- "camion", "poids lourd" → modele="CAMION"

**CONVERSION ENERGIE AUTO** (le client dit → tu utilises):
- "essence", "super", "SP95" → fuel_type="ESSENCE"
- "diesel", "gasoil", "mazout" → fuel_type="DIESEL"

**✈️ ASSURANCE VOYAGE:**
1. Demander le passeport → Appeler `analyze_passport(image_url)`
2. Demander zone, durée, type de client → Convertir selon les valeurs ci-dessous
3. Calculer → `calculate_voyage_quotation(client_type, zone, product, duration_days)`
4. Présenter le tarif → Confirmer
5. Créer client → `get_or_create_client(phone, fullname)`
6. Créer souscription → `create_souscription(client_id, "voyage", tarif_ttc, duree)`
7. Enregistrer détails → `save_voyage_details(souscription_id, full_name, passport_number, prime_ttc, coverage, ...)`
8. Initier paiement

**CONVERSION CLIENT_TYPE VOYAGE** (le client dit → tu utilises):
- "particulier", "personne", "individu", "moi-même" → client_type="PARTICULIER"
- "étudiant", "étudiante", "élève" → client_type="ETUDIANT"
- "pèlerin", "pèlerinage", "hadj", "omra" → client_type="PELERIN"

**CONVERSION ZONE VOYAGE** (le client dit → tu utilises):
- "Europe", "pays européen", "France", "Allemagne" → zone="EUROPE"
- "monde entier", "mondial", "international" → zone="MONDE ENTIER"
- "monde sauf lieux saints", "monde sans Schengen" → zone="MONDE ENTIER (EX. Lieux Saints Schengen)"
- "monde sauf Congo" → zone="MONDE ENTIER (EXCEPTÉ Le Congo)"

**CONVERSION PRODUCT VOYAGE** (le client dit → tu utilises):
Pour zone="EUROPE":
- "Schengen", "visa Schengen", "espace Schengen" → product="SCHENGEN EXCLUSIF"
- "Europe et Schengen", "Europe complète" → product="EUROPE ET SCHENGEN"

Pour client_type="ETUDIANT":
- "étudiant classique", "étudiant normal" → product="ETUDIANT CLASSIQUE"
- "étudiant économique", "étudiant pas cher" → product="ETUDIANT ECONOMIQUE"
- "étudiant premium", "étudiant haut de gamme" → product="ETUDIANT PREMIUM"

Pour client_type="PELERIN":
- "pèlerinage basic", "pèlerinage basique" → product="PÈLERINAGE BASIC"
- "pèlerinage plus" → product="PÈLERINAGE PLUS"
- "pèlerinage extra" → product="PÈLERINAGE EXTRA"

Pour client_type="PARTICULIER":
- "économie", "économique" → product="ECONOMIE"
- "famille" → product="FAMILLE"
- "perle" → product="PERLE"
- "voyageur" → product="VOYAGEUR"

**IMPORTANT VOYAGE:** Si le client ne précise pas le product, propose-lui les options disponibles selon son client_type et sa zone.

**👨‍💼 INDIVIDUELLE ACCIDENT (IAC):**
1. Demander le statut professionnel et les informations (secteur d'activité, lieu de travail)
2. Calculer → `calculate_iac_quotation(statut)` ou `calculate_iac_quotation()` pour tous
3. Présenter les offres par statut
4. Demander le document d'identité (Passeport/NIU/CNI) → Appeler l'outil d'analyse correspondant
5. Créer client → `get_or_create_client(phone, fullname)`
6. Créer souscription → `create_souscription(client_id, "iac", prime_ttc, "12M")`
7. Enregistrer détails → `save_iac_details(souscription_id, fullname, statutPro, secteurActivite, lieuTravail, prime_ttc, coverage, typeDocument, ...)`
8. Initier paiement

**🏠 MULTIRISQUE HABITATION (MRH):**
1. Présenter les forfaits → `calculate_mrh_quotation()` pour tous les forfaits
2. Demander quel forfait intéresse → `calculate_mrh_quotation(forfait)` pour les détails
3. Confirmer le choix
4. Demander le document d'identité (Passeport/NIU/CNI) → Appeler l'outil d'analyse correspondant
5. Créer client → `get_or_create_client(phone, fullname)`
6. Créer souscription → `create_souscription(client_id, "mrh", prime_annuelle, "12M")`
7. Enregistrer détails → `save_mrh_details(souscription_id, fullname, forfaitMrh, prime_ttc, coverage, typeDocument, ...)`
8. Initier paiement

⚠️ **RÈGLES CRITIQUES:**

1. **Utilise TOUJOURS les outils** - Ne devine JAMAIS les prix ou infos
2. **Convertis le langage naturel** - TOUJOURS utiliser les valeurs EXACTES des tableaux de conversion ci-dessus
   - Client dit "voiture personnelle" → TU UTILISES usage="PROMENADE/AFFAIRES" (JAMAIS "personnel" ou autre)
   - Client dit "étudiant" → TU UTILISES client_type="ETUDIANT" (EN MAJUSCULES)
   - Client dit "Europe" → TU UTILISES zone="EUROPE" (EN MAJUSCULES)
3. **Une question à la fois** - Ne submerge pas le client
4. **Confirme chaque étape** - Avant de passer à la suivante
5. **Sois précise** - Donne les montants exacts, pas d'approximations
6. **Garde le contexte** - L'historique de la conversation est préservé
7. **Gère les erreurs** - Si un outil échoue, demande poliment de réessayer
8. **Sois chaleureuse** - Tout en restant professionnelle

💡 **EXEMPLE CONVERSATION:**

Client: "Bonjour"
AYA: "Bonjour! 👋 Je suis AYA, votre conseillère digitale NSIA Assurances.
Je vous aide à souscrire en 3 minutes!

🏢 Produits disponibles:
1️⃣ Assurance Auto 🚗
2️⃣ Assurance Voyage ✈️
3️⃣ Individuelle Accident 👨‍💼
4️⃣ Multirisque Habitation 🏠

Quel produit vous intéresse?"

Client: "1"
AYA: "Parfait! Assurance Auto 🚗

Pour calculer votre devis, j'ai besoin de votre carte grise.
📸 Envoyez-moi une photo claire de votre carte grise."

[Client envoie photo]
AYA: [Appelle analyze_carte_grise(url)]
"✅ Carte grise analysée!
Voiture de 7CV, 5 places, ESSENCE
[Appelle calculate_auto_quotation(...)]

🎯 Votre Devis NSIA Auto:
✅ 3 MOIS: 75,000 FCFA
✅ 6 MOIS: 142,500 FCFA
✅ 12 MOIS: 270,000 FCFA

Quelle période choisissez-vous? (3M, 6M ou 12M)"

Client: "12M"
AYA: [Appelle get_or_create_client(...)]
[Appelle create_souscription(...)]
"✅ Souscription enregistrée!

💳 Choisissez votre mode de paiement:
1️⃣ MTN Mobile Money
2️⃣ Airtel Money

Répondez 1 ou 2"

Client: "1"
AYA: [Appelle initiate_momo_payment(...)]
"✅ Paiement initié!

💰 Montant: 270,000 FCFA
📱 Provider: MTN Mobile Money
🔑 Référence: REF123456

📲 Vous allez recevoir un message USSD
Composez votre code PIN pour valider.

Après paiement, vous recevrez:
- Reçu de paiement
- Attestation d'assurance

Merci de votre confiance! 🙏"

🎯 **TON OBJECTIF:**
Mener CHAQUE client du début à la fin avec succès.
Utilise intelligemment tes outils pour automatiser le processus.
"""

        logger.info("✅ AYA Orchestrator initialisé")

    async def process_conversation(
        self,
        user_message: str,
        session_id: str,
        user_phone: str,
        media_url: Optional[str] = None
    ) -> str:
        """
        Traite un message utilisateur dans le contexte de la conversation.

        Args:
            user_message: Message de l'utilisateur
            session_id: ID de session pour l'historique
            user_phone: Numéro de téléphone de l'utilisateur
            media_url: URL d'un média (image) si présent

        Returns:
            Réponse de l'agent
        """
        try:
            # Construire le message complet
            full_message = self._build_message_with_context(
                user_message, user_phone, media_url
            )

            # Récupérer l'historique de conversation depuis Redis
            history = await self._get_conversation_history(session_id)

            # Ajouter le nouveau message utilisateur à l'historique
            new_user_message = {
                "role": "user",
                "content": full_message
            }
            history.append(new_user_message)

            logger.info(f"💬 Traitement message pour session {session_id}: {user_message[:50]}...")
            if media_url:
                logger.info(f"🖼️  Media URL fourni: {media_url[:100]}...")
            logger.info(f"📚 Historique: {len(history)} message(s)")

            # Créer l'agent AYA avec tous les outils
            aya_agent = Agent(
                name="AYA",
                instructions=self.system_instructions,
                model=self.model,
                tools=ALL_AGENT_TOOLS
            )

            # Exécuter l'agent avec l'historique complet depuis Redis
            # IMPORTANT: On passe l'historique complet et on ne utilise PAS conversation_id
            # Redis gère la mémoire, pas le SDK OpenAI
            result = await Runner.run(
                starting_agent=aya_agent,
                input=history  # Historique complet depuis Redis
            )

            # Extraire la réponse
            response = result.final_output if hasattr(result, 'final_output') else str(result)

            # Sauvegarder l'historique mis à jour avec la réponse de l'assistant
            await self._save_conversation_history(
                session_id,
                new_user_message,
                response
            )

            logger.info(f"✅ Réponse générée pour session {session_id}")

            return response

        except Exception as e:
            logger.error(f"❌ Erreur process_conversation: {e}", exc_info=True)
            return "Désolée, j'ai rencontré une erreur. Pouvez-vous reformuler votre demande?"

    def _build_message_with_context(
        self,
        message: str,
        phone: str,
        media_url: Optional[str] = None
    ) -> str:
        """
        Construit le message avec le contexte nécessaire.

        Args:
            message: Message utilisateur
            phone: Numéro de téléphone
            media_url: URL du média

        Returns:
            Message formaté avec contexte
        """
        context_parts = []

        # Ajouter le numéro de téléphone (important pour get_or_create_client)
        context_parts.append(f"[TÉLÉPHONE CLIENT: {phone}]")

        # Si c'est une image
        if media_url:
            context_parts.append(f"Message du client: {message}")
            context_parts.append(f"\n🚨 CRITIQUE - IMAGE FOURNIE:")
            context_parts.append(f"URL de l'image: {media_url}")
            context_parts.append("\n⚡ ACTION OBLIGATOIRE - Tu DOIS IMMÉDIATEMENT analyser cette image avec l'outil approprié:")
            context_parts.append(f"- Pour carte grise (AUTO) → appelle analyze_carte_grise(\"{media_url}\")")
            context_parts.append(f"- Pour passeport (VOYAGE) → appelle analyze_passport(\"{media_url}\")")
            context_parts.append(f"- Pour CNI → appelle analyze_cni(\"{media_url}\")")
            context_parts.append(f"- Pour NIU → appelle analyze_niu(\"{media_url}\")")
            context_parts.append("\n⚠️ NE DEMANDE PAS au client d'envoyer l'image, il l'a DÉJÀ ENVOYÉE!")
            context_parts.append("Utilise l'URL ci-dessus pour analyser l'image MAINTENANT.")
        else:
            context_parts.append(message)

        return "\n".join(context_parts)

    async def _get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Récupère l'historique de conversation depuis Redis.

        Args:
            session_id: ID de session

        Returns:
            Liste de messages
        """
        try:
            state = await redis_service.get_conversation_state(session_id)

            if state and state.message_history:
                # Convertir au format attendu par le SDK
                return [
                    {
                        "role": msg["role"],
                        "content": msg["content"]
                    }
                    for msg in state.message_history
                ]

            # Nouvelle conversation
            return []

        except Exception as e:
            logger.error(f"Erreur récupération historique: {e}")
            return []

    async def _save_conversation_history(
        self,
        session_id: str,
        user_message: Dict[str, str],
        assistant_response: str
    ) -> None:
        """
        Sauvegarde l'historique de conversation dans Redis.

        Args:
            session_id: ID de session
            user_message: Message utilisateur à ajouter
            assistant_response: Réponse de l'assistant à ajouter
        """
        try:
            # Récupérer ou créer l'état
            state = await redis_service.get_conversation_state(session_id)

            if state is None:
                from app.models.state import ConversationState
                state = ConversationState(
                    session_id=session_id,
                    user_phone=""  # Sera mis à jour avec le contexte
                )

            # Ajouter le message utilisateur
            state.add_message("user", user_message["content"])

            # Ajouter la réponse de l'assistant
            state.add_message("assistant", assistant_response)

            # Sauvegarder dans Redis avec TTL
            await redis_service.save_conversation_state(session_id, state)

            logger.info(f"💾 Historique sauvegardé: {len(state.message_history)} messages")

        except Exception as e:
            logger.error(f"Erreur sauvegarde historique: {e}")

    def run_sync(
        self,
        user_message: str,
        session_id: str,
        user_phone: str,
        media_url: Optional[str] = None
    ) -> str:
        """
        Version synchrone pour compatibilité.

        Args:
            user_message: Message utilisateur
            session_id: ID de session
            user_phone: Numéro de téléphone
            media_url: URL du média

        Returns:
            Réponse de l'agent
        """
        try:
            # Construire le message
            full_message = self._build_message_with_context(
                user_message, user_phone, media_url
            )

            # Créer agent
            aya_agent = Agent(
                name="AYA",
                instructions=self.system_instructions,
                model=self.model,
                tools=ALL_AGENT_TOOLS
            )

            # Exécuter en mode synchrone
            result = Runner.run_sync(
                agent=aya_agent,
                messages=[{"role": "user", "content": full_message}]
            )

            return result.final_output

        except Exception as e:
            logger.error(f"Erreur run_sync: {e}")
            return "Erreur lors du traitement de votre demande."


# Instance globale
aya_orchestrator = AYAOrchestrator()
