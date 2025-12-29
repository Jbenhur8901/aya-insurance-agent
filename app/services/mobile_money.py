"""
Service Mobile Money pour les paiements (MoMo et Airtel)
API: https://epay.nodes-hub.com
"""
import httpx
from app.config import settings
from app.models.schemas import PaymentRequest, PaymentResponse
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MobileMoneyService:
    """Service de gestion des paiements Mobile Money"""

    def __init__(self):
        """Initialise le service Mobile Money"""
        self.base_url = settings.EPAY_BASE_URL
        self.api_key = settings.EPAY_API_KEY
        self.headers = {
            "x-api-key": self.api_key
        }
        logger.info("Mobile Money Service initialisé")

    async def request_momo_payment(
        self,
        amount: float,
        phone: str,
        reference: str,
        payer_message: str = "Paiement assurance NSIA",
        callback_url: str = "https://epay.nodes-hub.com/callback/payment-notification",
        webhook_externe: Optional[str] = None
    ) -> PaymentResponse:
        """
        Initie un paiement MTN Mobile Money

        Args:
            amount: Montant du paiement
            phone: Numéro de téléphone (format: 06XXXXXXX)
            reference: Référence unique de la transaction
            payer_message: Message pour le payeur
            callback_url: URL de callback (défaut: https://epay.nodes-hub.com/callback/payment-notification)
            webhook_externe: URL webhook externe (optionnel, défaut: None)

        Returns:
            PaymentResponse avec le statut et la référence de transaction
        """
        try:
            # Préparer les données en form-urlencoded
            data = {
                "amount": str(amount),
                "phone": phone,
                "payer_message": payer_message,
                "callback_url": callback_url  # Toujours inclus avec valeur par défaut
            }

            if webhook_externe:
                data["webhook_externe"] = webhook_externe

            # Faire la requête
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/momo/collection/request-to-pay",
                    headers=self.headers,
                    data=data,  # form-urlencoded
                    timeout=30.0
                )

                response.raise_for_status()
                result = response.json()

                logger.info(f"Paiement MoMo initié: {reference}, Response: {result}")

                # Extraire le statut et la référence de transaction
                return PaymentResponse(
                    status=result.get("status", "unknown"),
                    transaction_reference=result.get("transaction_reference", reference),
                    message=result.get("message", "Paiement initié")
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"Erreur HTTP paiement MoMo: {e.response.status_code} - {e.response.text}")
            return PaymentResponse(
                status="error",
                transaction_reference=reference,
                message=f"Erreur HTTP: {e.response.status_code}"
            )

        except Exception as e:
            logger.error(f"Erreur paiement MoMo: {e}")
            return PaymentResponse(
                status="error",
                transaction_reference=reference,
                message=str(e)
            )

    async def request_airtel_payment(
        self,
        amount: float,
        msisdn: str,
        reference: str,
        description: str = "Paiement assurance NSIA",
        callback_url: str = "https://epay.nodes-hub.com/callback/payment-notification",
        webhook_externe: Optional[str] = None
    ) -> PaymentResponse:
        """
        Initie un paiement Airtel Money

        Args:
            amount: Montant du paiement
            msisdn: Numéro de téléphone (format: 05XXXXXXX)
            reference: Référence unique de la transaction
            description: Description de la transaction
            callback_url: URL de callback (défaut: https://epay.nodes-hub.com/callback/payment-notification)
            webhook_externe: URL webhook externe (optionnel, défaut: None)

        Returns:
            PaymentResponse avec le statut et la référence de transaction
        """
        try:
            # Préparer les données
            data = {
                "amount": str(amount),
                "msisdn": msisdn,
                "reference": reference,
                "description": description,
                "callback_url": callback_url  # Toujours inclus avec valeur par défaut
            }

            if webhook_externe:
                data["webhook_externe"] = webhook_externe

            # Faire la requête
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/airtel/collection/payment",
                    headers=self.headers,
                    data=data,  # form-urlencoded ou json selon l'API
                    timeout=30.0
                )

                response.raise_for_status()
                result = response.json()

                logger.info(f"Paiement Airtel initié: {reference}, Response: {result}")

                return PaymentResponse(
                    status=result.get("status", "unknown"),
                    transaction_reference=result.get("transaction_reference", reference),
                    message=result.get("message", "Paiement initié")
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"Erreur HTTP paiement Airtel: {e.response.status_code} - {e.response.text}")
            return PaymentResponse(
                status="error",
                transaction_reference=reference,
                message=f"Erreur HTTP: {e.response.status_code}"
            )

        except Exception as e:
            logger.error(f"Erreur paiement Airtel: {e}")
            return PaymentResponse(
                status="error",
                transaction_reference=reference,
                message=str(e)
            )

    async def initiate_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """
        Point d'entrée unifié pour initier un paiement

        Args:
            payment_request: Requête de paiement avec provider (momo ou airtel)

        Returns:
            PaymentResponse
        """
        # Le callback_url par défaut est déjà configuré dans les fonctions
        # webhook_externe reste à None sauf si configuré

        if payment_request.provider == "momo":
            return await self.request_momo_payment(
                amount=payment_request.amount,
                phone=payment_request.phone,
                reference=payment_request.reference,
                payer_message=payment_request.description
                # callback_url utilise la valeur par défaut
                # webhook_externe reste None
            )

        elif payment_request.provider == "airtel":
            return await self.request_airtel_payment(
                amount=payment_request.amount,
                msisdn=payment_request.phone,
                reference=payment_request.reference,
                description=payment_request.description
                # callback_url utilise la valeur par défaut
                # webhook_externe reste None
            )

        else:
            logger.error(f"Provider inconnu: {payment_request.provider}")
            return PaymentResponse(
                status="error",
                transaction_reference=payment_request.reference,
                message=f"Provider inconnu: {payment_request.provider}"
            )

    # ========================================================================
    # PAIEMENT HORS LIGNE - Sans Mobile Money
    # ========================================================================

    async def process_pay_on_delivery(
        self,
        souscription_id: str,
        client_name: str,
        client_phone: str,
        product_type: str,
        amount: float
    ) -> Dict[str, Any]:
        """
        Traite un paiement à la livraison (PAY_ON_DELIVERY).

        Étapes:
        1. Génère une référence unique
        2. Enregistre la transaction dans la DB
        3. Génère la proposition d'assurance PDF
        4. Upload le PDF dans Supabase Storage (bucket: receipts)
        5. Enregistre le document dans la table documents
        6. Retourne l'URL du PDF

        Args:
            souscription_id: ID de la souscription
            client_name: Nom complet du client
            client_phone: Téléphone du client
            product_type: Type de produit
            amount: Montant en FCFA

        Returns:
            Dict avec success, pdf_url, reference, message
        """
        try:
            from datetime import datetime
            from uuid import UUID
            import os

            logger.info("=" * 60)
            logger.info("🚀 DÉBUT PROCESS PAY_ON_DELIVERY")
            logger.info("=" * 60)

            # ÉTAPE 0: Valider le souscription_id
            logger.info(f"🔍 Validation du souscription_id: {souscription_id}")
            try:
                souscription_uuid = UUID(souscription_id)
                logger.info(f"✅ UUID valide: {souscription_uuid}")
            except (ValueError, AttributeError) as e:
                logger.error(f"❌ UUID invalide: {souscription_id}")
                return {
                    "success": False,
                    "error": f"UUID invalide: {souscription_id}",
                    "message": f"Le souscription_id doit être un UUID valide, reçu: {souscription_id}"
                }

            # ÉTAPE 1: Générer la référence
            logger.info("📋 ÉTAPE 1/5: Génération de la référence unique")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            # Utiliser les 8 premiers caractères du UUID (sans les tirets)
            uuid_short = str(souscription_uuid).replace("-", "")[:8]
            reference = f"NSIA-DELIVERY-{timestamp}-{uuid_short}"
            logger.info(f"✅ Référence générée: {reference}")

            # ÉTAPE 2: Enregistrer la transaction
            logger.info("💾 ÉTAPE 2/5: Enregistrement de la transaction dans la DB")
            from app.services.supabase_client import supabase_service

            transaction = await supabase_service.create_transaction(
                souscription_id=souscription_uuid,
                amount=amount,
                reference=reference,
                payment_method="PAY_ON_DELIVERY",
                status="en_attente"
            )
            logger.info(f"✅ Transaction enregistrée: ID={transaction['id'] if transaction else 'None'}")

            # Mettre à jour le statut de la souscription
            await supabase_service.update_souscription_status(str(souscription_uuid), "en_attente")
            logger.info(f"✅ Souscription {souscription_id} mise à jour: status=en_attente")

            # ÉTAPE 3: Générer le PDF de proposition
            logger.info("📄 ÉTAPE 3/5: Génération du PDF de proposition")
            from app.tools.receipts import generate_product_receipt_pdf

            filename = f"/tmp/proposition_delivery_{souscription_uuid}.pdf"

            try:
                success = generate_product_receipt_pdf(
                    output_filename=filename,
                    nom_complet=client_name,
                    telephone=client_phone,
                    ville="N/A",
                    product_type=product_type,
                    prime_a_payer_ttc=str(int(amount)),
                    receipt_number=reference,
                    template_path="product_proposal.txt",
                    product_name=product_type
                )
            except Exception as pdf_error:
                logger.error(f"❌ Erreur lors de la génération PDF: {pdf_error}")
                logger.warning("⚠️ Tentative de génération d'un document texte simple...")

                # Créer un fichier texte simple en fallback
                txt_content = f"""
PROPOSITION D'ASSURANCE - NSIA
{'='*50}

Client: {client_name}
Téléphone: {client_phone}
Produit: {product_type}
Montant: {amount:,.0f} FCFA
Référence: {reference}
Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Mode de paiement: Paiement à la livraison

Cette proposition sera validée après paiement.

Pour toute question, contactez NSIA Assurances.
{'='*50}
"""
                txt_filename = f"/tmp/proposition_delivery_{souscription_uuid}.txt"
                with open(txt_filename, 'w', encoding='utf-8') as f:
                    f.write(txt_content)

                logger.info(f"✅ Document texte généré: {txt_filename}")
                filename = txt_filename
                success = True

            if not success or not os.path.exists(filename):
                logger.error("❌ Échec génération document")
                return {
                    "success": False,
                    "error": "Génération document échouée",
                    "reference": reference
                }

            logger.info(f"✅ Document généré: {filename}")

            # ÉTAPE 4: Upload vers Supabase Storage
            logger.info("☁️  ÉTAPE 4/5: Upload du PDF vers Supabase Storage (bucket: receipts)")
            with open(filename, "rb") as f:
                pdf_data = f.read()

            file_path = f"proposals/{souscription_id}_{reference}.pdf"
            pdf_url = await supabase_service.upload_file("receipts", file_path, pdf_data)

            # Supprimer le fichier temporaire
            if os.path.exists(filename):
                os.remove(filename)
                logger.info(f"🗑️  Fichier temporaire supprimé: {filename}")

            if not pdf_url:
                logger.error("❌ Échec upload PDF vers Supabase")
                return {
                    "success": False,
                    "error": "Upload PDF échoué",
                    "reference": reference
                }

            logger.info(f"✅ PDF uploadé: {pdf_url}")

            # ÉTAPE 5: Enregistrer dans la table documents
            logger.info("💾 ÉTAPE 5/5: Enregistrement dans la table documents")
            from app.models.schemas import DocumentUpload

            doc = await supabase_service.save_document(
                DocumentUpload(
                    souscription_id=souscription_uuid,
                    document_url=pdf_url,
                    type="proposition",
                    nom=f"Proposition_Delivery_{souscription_uuid}.pdf"
                )
            )
            logger.info(f"✅ Document enregistré: ID={doc['id'] if doc else 'None'}")

            logger.info("=" * 60)
            logger.info("✅ FIN PROCESS PAY_ON_DELIVERY - SUCCÈS")
            logger.info("=" * 60)

            return {
                "success": True,
                "pdf_url": pdf_url,
                "reference": reference,
                "amount": amount,
                "payment_method": "PAY_ON_DELIVERY",
                "message": f"""✅ Souscription enregistrée!

💰 Montant: {amount:,} FCFA
📦 Mode: Paiement à la livraison
🔑 Référence: {reference}

📄 Votre proposition d'assurance a été générée.

Vous recevrez votre attestation d'assurance lors de la livraison.
Le paiement de {amount:,} FCFA sera à effectuer au livreur.

📞 Notre équipe vous contactera sous peu pour organiser la livraison.

Merci d'avoir choisi NSIA Assurances! 🙏"""
            }

        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"❌ ERREUR PROCESS PAY_ON_DELIVERY: {e}")
            logger.error("=" * 60)
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "message": "Erreur lors du traitement du paiement à la livraison"
            }

    async def process_pay_on_agency(
        self,
        souscription_id: str,
        client_name: str,
        client_phone: str,
        product_type: str,
        amount: float
    ) -> Dict[str, Any]:
        """
        Traite un paiement en agence (PAY_ON_AGENCY).

        Étapes:
        1. Génère une référence unique
        2. Enregistre la transaction dans la DB
        3. Génère la proposition d'assurance PDF
        4. Upload le PDF dans Supabase Storage (bucket: receipts)
        5. Enregistre le document dans la table documents
        6. Retourne l'URL du PDF

        Args:
            souscription_id: ID de la souscription
            client_name: Nom complet du client
            client_phone: Téléphone du client
            product_type: Type de produit
            amount: Montant en FCFA

        Returns:
            Dict avec success, pdf_url, reference, message
        """
        try:
            from datetime import datetime
            from uuid import UUID
            import os

            logger.info("=" * 60)
            logger.info("🚀 DÉBUT PROCESS PAY_ON_AGENCY")
            logger.info("=" * 60)

            # ÉTAPE 0: Valider le souscription_id
            logger.info(f"🔍 Validation du souscription_id: {souscription_id}")
            try:
                souscription_uuid = UUID(souscription_id)
                logger.info(f"✅ UUID valide: {souscription_uuid}")
            except (ValueError, AttributeError) as e:
                logger.error(f"❌ UUID invalide: {souscription_id}")
                return {
                    "success": False,
                    "error": f"UUID invalide: {souscription_id}",
                    "message": f"Le souscription_id doit être un UUID valide, reçu: {souscription_id}"
                }

            # ÉTAPE 1: Générer la référence
            logger.info("📋 ÉTAPE 1/5: Génération de la référence unique")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            # Utiliser les 8 premiers caractères du UUID (sans les tirets)
            uuid_short = str(souscription_uuid).replace("-", "")[:8]
            reference = f"NSIA-AGENCY-{timestamp}-{uuid_short}"
            logger.info(f"✅ Référence générée: {reference}")

            # ÉTAPE 2: Enregistrer la transaction
            logger.info("💾 ÉTAPE 2/5: Enregistrement de la transaction dans la DB")
            from app.services.supabase_client import supabase_service

            transaction = await supabase_service.create_transaction(
                souscription_id=souscription_uuid,
                amount=amount,
                reference=reference,
                payment_method="PAY_ON_AGENCY",
                status="en_attente"
            )
            logger.info(f"✅ Transaction enregistrée: ID={transaction['id'] if transaction else 'None'}")

            # Mettre à jour le statut de la souscription
            await supabase_service.update_souscription_status(str(souscription_uuid), "en_attente")
            logger.info(f"✅ Souscription {souscription_id} mise à jour: status=en_attente")

            # ÉTAPE 3: Générer le PDF de proposition
            logger.info("📄 ÉTAPE 3/5: Génération du PDF de proposition")
            from app.tools.receipts import generate_product_receipt_pdf

            filename = f"/tmp/proposition_agency_{souscription_uuid}.pdf"

            try:
                success = generate_product_receipt_pdf(
                    output_filename=filename,
                    nom_complet=client_name,
                    telephone=client_phone,
                    ville="N/A",
                    product_type=product_type,
                    prime_a_payer_ttc=str(int(amount)),
                    receipt_number=reference,
                    template_path="product_proposal.txt",
                    product_name=product_type
                )
            except Exception as pdf_error:
                logger.error(f"❌ Erreur lors de la génération PDF: {pdf_error}")
                logger.warning("⚠️ Tentative de génération d'un document texte simple...")

                # Créer un fichier texte simple en fallback
                txt_content = f"""
PROPOSITION D'ASSURANCE - NSIA
{'='*50}

Client: {client_name}
Téléphone: {client_phone}
Produit: {product_type}
Montant: {amount:,.0f} FCFA
Référence: {reference}
Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Mode de paiement: Paiement en agence

Pour finaliser votre souscription:
1. Rendez-vous dans l'une de nos agences NSIA
2. Présentez votre référence: {reference}
3. Effectuez le paiement de {amount:,.0f} FCFA
4. Recevez immédiatement votre attestation d'assurance

Nos agences NSIA:
- Brazzaville: Avenue de l'Indépendance
- Pointe-Noire: Centre-Ville

Merci d'avoir choisi NSIA Assurances!
{'='*50}
"""
                txt_filename = f"/tmp/proposition_agency_{souscription_uuid}.txt"
                with open(txt_filename, 'w', encoding='utf-8') as f:
                    f.write(txt_content)

                logger.info(f"✅ Document texte généré: {txt_filename}")
                filename = txt_filename
                success = True

            if not success or not os.path.exists(filename):
                logger.error("❌ Échec génération document")
                return {
                    "success": False,
                    "error": "Génération document échouée",
                    "reference": reference
                }

            logger.info(f"✅ Document généré: {filename}")

            # ÉTAPE 4: Upload vers Supabase Storage
            logger.info("☁️  ÉTAPE 4/5: Upload du PDF vers Supabase Storage (bucket: receipts)")
            with open(filename, "rb") as f:
                pdf_data = f.read()

            file_path = f"proposals/{souscription_id}_{reference}.pdf"
            pdf_url = await supabase_service.upload_file("receipts", file_path, pdf_data)

            # Supprimer le fichier temporaire
            if os.path.exists(filename):
                os.remove(filename)
                logger.info(f"🗑️  Fichier temporaire supprimé: {filename}")

            if not pdf_url:
                logger.error("❌ Échec upload PDF vers Supabase")
                return {
                    "success": False,
                    "error": "Upload PDF échoué",
                    "reference": reference
                }

            logger.info(f"✅ PDF uploadé: {pdf_url}")

            # ÉTAPE 5: Enregistrer dans la table documents
            logger.info("💾 ÉTAPE 5/5: Enregistrement dans la table documents")
            from app.models.schemas import DocumentUpload

            doc = await supabase_service.save_document(
                DocumentUpload(
                    souscription_id=souscription_uuid,
                    document_url=pdf_url,
                    type="proposition",
                    nom=f"Proposition_Agency_{souscription_uuid}.pdf"
                )
            )
            logger.info(f"✅ Document enregistré: ID={doc['id'] if doc else 'None'}")

            logger.info("=" * 60)
            logger.info("✅ FIN PROCESS PAY_ON_AGENCY - SUCCÈS")
            logger.info("=" * 60)

            return {
                "success": True,
                "pdf_url": pdf_url,
                "reference": reference,
                "amount": amount,
                "payment_method": "PAY_ON_AGENCY",
                "message": f"""✅ Souscription enregistrée!

💰 Montant: {amount:,} FCFA
🏢 Mode: Paiement en agence
🔑 Référence: {reference}

📄 Votre proposition d'assurance a été générée.

Pour finaliser votre souscription:
1. Rendez-vous dans l'une de nos agences NSIA
2. Présentez votre référence: {reference}
3. Effectuez le paiement de {amount:,} FCFA
4. Recevez immédiatement votre attestation d'assurance

📍 Nos agences NSIA:
- Brazzaville: Avenue de l'Indépendance
- Pointe-Noire: Centre-Ville

Merci d'avoir choisi NSIA Assurances! 🙏"""
            }

        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"❌ ERREUR PROCESS PAY_ON_AGENCY: {e}")
            logger.error("=" * 60)
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "message": "Erreur lors du traitement du paiement en agence"
            }

    # ========================================================================
    # MÉTHODES UTILITAIRES
    # ========================================================================

    def format_phone_number(self, phone: str) -> str:
        """
        Formate le numéro de téléphone pour l'API
        Convertit +242XXXXXXXXX en 242XXXXXXXXX

        Args:
            phone: Numéro de téléphone

        Returns:
            Numéro formaté
        """
        # Supprimer les espaces et le +
        phone = phone.replace(" ", "").replace("+", "")

        return phone

    def generate_reference(self, souscription_id: str) -> str:
        """
        Génère une référence unique pour la transaction

        Args:
            souscription_id: ID de la souscription

        Returns:
            Référence unique
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"NSIA-{timestamp}-{souscription_id[:8]}"

    async def check_payment_status(self, transaction_reference: str, provider: str) -> Dict[str, Any]:
        """
        Vérifie le statut d'un paiement (si l'API le supporte)

        Args:
            transaction_reference: Référence de la transaction
            provider: momo ou airtel

        Returns:
            Dictionnaire avec le statut
        """
        # TODO: Implémenter si l'API epay supporte la vérification de statut
        logger.warning(f"check_payment_status pas encore implémenté pour {provider}, ref: {transaction_reference}")
        return {
            "status": "unknown",
            "message": "Vérification de statut non disponible"
        }


# Instance globale
mobile_money_service = MobileMoneyService()
