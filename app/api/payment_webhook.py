"""
Webhooks pour les callbacks de paiement (MoMo et Airtel)

Reçoit les notifications de paiement des providers et met à jour le statut.
"""
from fastapi import APIRouter, Request, BackgroundTasks
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Mapping des statuts API epay vers enums DB
PAYMENT_STATUS_MAPPING = {
    "success": "valide",
    "succeeded": "valide",
    "completed": "valide",
    "failed": "annulée",
    "cancelled": "annulée",
    "canceled": "annulée",
    "pending": "en_attente",
    "processing": "en_cours",
    "unknown": "en_attente"
}


def map_payment_status_to_db(api_status: str) -> str:
    """
    Convertit le statut de l'API epay vers les enums de la DB

    Args:
        api_status: Statut de l'API (success, failed, pending, etc.)

    Returns:
        Statut DB (en_cours, valide, expirée, annulée, en_attente)
    """
    normalized_status = api_status.lower().strip()
    return PAYMENT_STATUS_MAPPING.get(normalized_status, "en_attente")


@router.post("/callback/payment-notification")
async def payment_notification_callback(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Callback unifié pour les paiements Mobile Money (MTN MoMo et Airtel Money)

    URL: https://epay.nodes-hub.com/callback/payment-notification
    Compatible avec MTN Mobile Money et Airtel Money

    Args:
        request: Requête HTTP avec les données de callback
        background_tasks: Tâches en arrière-plan

    Returns:
        Acknowledgment
    """
    try:
        # Récupérer les données du callback
        data = await request.json()
        logger.info(f"📲 Callback paiement reçu: {data}")

        # Extraire les informations importantes
        transaction_reference = data.get("transaction_reference") or data.get("reference")
        status = data.get("status", "unknown")

        # Identifier le provider depuis les données du callback
        # L'API epay peut fournir cette info dans le callback
        provider = data.get("provider", "").lower()

        # Si provider n'est pas dans les données, essayer de deviner depuis d'autres champs
        if not provider:
            if "momo" in str(data).lower() or "mtn" in str(data).lower():
                provider = "momo"
            elif "airtel" in str(data).lower():
                provider = "airtel"
            else:
                provider = "unknown"

        if not transaction_reference:
            logger.error("❌ Callback sans référence de transaction")
            return {"status": "error", "message": "Missing transaction_reference"}

        logger.info(f"🔍 Transaction: {transaction_reference}, Status: {status}, Provider: {provider}")

        # Traiter le callback en arrière-plan
        background_tasks.add_task(
            _process_payment_callback,
            transaction_reference=transaction_reference,
            status=status,
            provider=provider,
            raw_data=data
        )

        return {"status": "ok", "message": "Callback reçu"}

    except Exception as e:
        logger.error(f"❌ Erreur callback paiement: {e}")
        return {"status": "error", "message": str(e)}


# Endpoints legacy pour compatibilité (au cas où)
@router.post("/callback/momo")
async def momo_payment_callback_legacy(request: Request, background_tasks: BackgroundTasks):
    """Endpoint legacy - redirige vers payment-notification"""
    return await payment_notification_callback(request, background_tasks)


@router.post("/callback/airtel")
async def airtel_payment_callback_legacy(request: Request, background_tasks: BackgroundTasks):
    """Endpoint legacy - redirige vers payment-notification"""
    return await payment_notification_callback(request, background_tasks)


async def _process_payment_callback(
    transaction_reference: str,
    status: str,
    provider: str,
    raw_data: Dict[str, Any]
):
    """
    Traite le callback de paiement en arrière-plan

    Args:
        transaction_reference: Référence de la transaction
        status: Statut du paiement (de l'API epay)
        provider: momo ou airtel
        raw_data: Données brutes du callback
    """
    try:
        logger.info(f"Traitement callback {provider}: {transaction_reference}, Status API: {status}")

        # Convertir le statut API vers l'enum DB
        db_status = map_payment_status_to_db(status)
        logger.info(f"Statut converti: {status} → {db_status}")

        # Mettre à jour le statut de la transaction dans la DB
        from app.services.supabase_client import supabase_service
        await supabase_service.update_transaction_status(transaction_reference, db_status)

        # Si paiement validé, mettre à jour le statut de la souscription
        if db_status == "valide":
            # Récupérer la souscription_id depuis la transaction
            transaction = await supabase_service.get_transaction_by_reference(transaction_reference)
            if transaction and transaction.get("souscription_id"):
                # Mettre à jour le statut de la souscription
                await supabase_service.update_souscription_status(
                    transaction["souscription_id"],
                    "valide"
                )
                logger.info(f"✅ Souscription {transaction['souscription_id']} validée")

        # Stocker un flag dans Redis pour indiquer que le paiement est confirmé
        # Format: payment_confirmed:{transaction_reference} = {status}
        if db_status == "valide":
            from app.services.redis_client import redis_service
            redis_service.client.set(
                f"payment_confirmed:{transaction_reference}",
                status,
                ex=3600  # Expire après 1 heure
            )
            logger.info(f"✅ Paiement confirmé stocké dans Redis: {transaction_reference}")

        logger.info(f"Callback {provider} traité avec succès")

    except Exception as e:
        logger.error(f"Erreur traitement callback: {e}")
