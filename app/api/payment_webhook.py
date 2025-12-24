"""
Webhooks pour les callbacks de paiement (MoMo et Airtel)

Reçoit les notifications de paiement des providers et met à jour le statut.
"""
from fastapi import APIRouter, Request, BackgroundTasks
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/callback/momo")
async def momo_payment_callback(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Callback pour les paiements MTN Mobile Money

    Args:
        request: Requête HTTP avec les données de callback
        background_tasks: Tâches en arrière-plan

    Returns:
        Acknowledgment
    """
    try:
        # Récupérer les données du callback
        data = await request.json()
        logger.info(f"Callback MoMo reçu: {data}")

        # Extraire les informations importantes
        transaction_reference = data.get("transaction_reference") or data.get("reference")
        status = data.get("status", "unknown")

        if not transaction_reference:
            logger.error("Callback MoMo sans référence de transaction")
            return {"status": "error", "message": "Missing transaction_reference"}

        # Traiter le callback en arrière-plan
        background_tasks.add_task(
            _process_payment_callback,
            transaction_reference=transaction_reference,
            status=status,
            provider="momo",
            raw_data=data
        )

        return {"status": "ok", "message": "Callback reçu"}

    except Exception as e:
        logger.error(f"Erreur callback MoMo: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/callback/airtel")
async def airtel_payment_callback(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Callback pour les paiements Airtel Money

    Args:
        request: Requête HTTP avec les données de callback
        background_tasks: Tâches en arrière-plan

    Returns:
        Acknowledgment
    """
    try:
        # Récupérer les données du callback
        data = await request.json()
        logger.info(f"Callback Airtel reçu: {data}")

        # Extraire les informations importantes
        transaction_reference = data.get("transaction_reference") or data.get("reference")
        status = data.get("status", "unknown")

        if not transaction_reference:
            logger.error("Callback Airtel sans référence de transaction")
            return {"status": "error", "message": "Missing transaction_reference"}

        # Traiter le callback en arrière-plan
        background_tasks.add_task(
            _process_payment_callback,
            transaction_reference=transaction_reference,
            status=status,
            provider="airtel",
            raw_data=data
        )

        return {"status": "ok", "message": "Callback reçu"}

    except Exception as e:
        logger.error(f"Erreur callback Airtel: {e}")
        return {"status": "error", "message": str(e)}


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
        status: Statut du paiement
        provider: momo ou airtel
        raw_data: Données brutes du callback
    """
    try:
        logger.info(f"Traitement callback {provider}: {transaction_reference}, Status: {status}")

        # Mettre à jour le statut de la transaction dans la DB
        from app.services.supabase_client import supabase_service
        await supabase_service.update_transaction_status(transaction_reference, status)

        # TODO: Récupérer la session associée via la transaction_reference
        # Pour l'instant, le statut est mis à jour dans la DB
        # Le prochain message du client déclenchera la génération du reçu

        # Stocker un flag dans Redis pour indiquer que le paiement est confirmé
        # Format: payment_confirmed:{transaction_reference} = {status}
        if status == "success":
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
