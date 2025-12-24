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
        callback_url: Optional[str] = None,
        webhook_externe: Optional[str] = None
    ) -> PaymentResponse:
        """
        Initie un paiement MTN Mobile Money

        Args:
            amount: Montant du paiement
            phone: Numéro de téléphone (format: 242XXXXXXXXX)
            reference: Référence unique de la transaction
            payer_message: Message pour le payeur
            callback_url: URL de callback (optionnel)
            webhook_externe: URL webhook externe (optionnel)

        Returns:
            PaymentResponse avec le statut et la référence de transaction
        """
        try:
            # Préparer les données en form-urlencoded
            data = {
                "amount": str(amount),
                "phone": phone,
                "payer_message": payer_message
            }

            if callback_url:
                data["callback_url"] = callback_url

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
        webhook_externe: Optional[str] = None
    ) -> PaymentResponse:
        """
        Initie un paiement Airtel Money

        Args:
            amount: Montant du paiement
            msisdn: Numéro de téléphone (format: 242XXXXXXXXX)
            reference: Référence unique de la transaction
            description: Description de la transaction
            webhook_externe: URL webhook externe (optionnel)

        Returns:
            PaymentResponse avec le statut et la référence de transaction
        """
        try:
            # Préparer les données
            data = {
                "amount": str(amount),
                "msisdn": msisdn,
                "reference": reference,
                "description": description
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
        # Générer l'URL de webhook si configurée
        webhook_url = None
        if settings.BASE_WEBHOOK_URL:
            webhook_url = f"{settings.BASE_WEBHOOK_URL}/api/payment/callback/{payment_request.provider}"

        if payment_request.provider == "momo":
            return await self.request_momo_payment(
                amount=payment_request.amount,
                phone=payment_request.phone,
                reference=payment_request.reference,
                payer_message=payment_request.description,
                webhook_externe=webhook_url
            )

        elif payment_request.provider == "airtel":
            return await self.request_airtel_payment(
                amount=payment_request.amount,
                msisdn=payment_request.phone,
                reference=payment_request.reference,
                description=payment_request.description,
                webhook_externe=webhook_url
            )

        else:
            logger.error(f"Provider inconnu: {payment_request.provider}")
            return PaymentResponse(
                status="error",
                transaction_reference=payment_request.reference,
                message=f"Provider inconnu: {payment_request.provider}"
            )

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

        # S'assurer qu'il commence par 242
        if not phone.startswith("242"):
            phone = f"242{phone}"

        return phone

    def generate_reference(self, souscription_id: str) -> str:
        """
        Génère une référence unique pour la transaction

        Args:
            souscription_id: ID de la souscription

        Returns:
            Référence unique
        """
        import uuid
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
        logger.warning("check_payment_status pas encore implémenté")
        return {
            "status": "unknown",
            "message": "Vérification de statut non disponible"
        }


# Instance globale
mobile_money_service = MobileMoneyService()
