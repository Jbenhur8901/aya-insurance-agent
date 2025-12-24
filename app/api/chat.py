"""
API Endpoint pour l'interaction avec l'orchestrateur AYA
Endpoint générique pour n'importe quel client (WhatsApp, Web, Mobile, etc.)

Utilise le système agentique basé sur OpenAI Agent SDK pour gérer
automatiquement tout le processus de souscription.
"""
from fastapi import APIRouter, HTTPException, Form, File, UploadFile
from app.models.schemas import InferenceResponse
from app.agents.orchestrator import aya_orchestrator
from typing import Optional
import logging
import base64

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=InferenceResponse)
async def chat_endpoint(
    msg: str = Form(..., description="Message de l'utilisateur"),
    session_id: str = Form(..., description="ID de session pour l'historique de conversation"),
    user_phone: str = Form(..., description="Numéro de téléphone de l'utilisateur"),
    message_type: str = Form("text", description="Type de message (text, image, audio, document)"),
    media_url: Optional[str] = Form(None, description="URL du média si applicable"),
    media: Optional[UploadFile] = File(None, description="Fichier média uploadé"),
    model: str = Form("gpt-4o-mini", description="Modèle à utiliser"),
    timeline: int = Form(3600, description="Durée de vie de la session en secondes"),
    temperature: float = Form(0.0, description="Température pour la génération")
):
    """
    Endpoint principal pour communiquer avec l'orchestrateur AYA

    Cet endpoint est générique et peut être utilisé par n'importe quel client:
    - Application Web
    - Application Mobile
    - Chat Widget
    - API directe
    - Intégrations tierces

    Args:
        msg: Message de l'utilisateur
        session_id: ID de session pour l'historique
        user_phone: Numéro de téléphone de l'utilisateur
        message_type: Type de message (text, image, etc.)
        media_url: URL du média si applicable
        model: Modèle à utiliser (par défaut: gpt-4o-mini)
        timeline: Durée de vie de la session en secondes
        temperature: Température pour la génération

    Returns:
        InferenceResponse avec la réponse de l'agent
    """
    try:
        logger.info(f"📨 Message reçu - Session: {session_id}, Type: {message_type}")
        logger.info(f"🔧 Config: Model={model}, Timeline={timeline}s, Temp={temperature}")

        # Utiliser l'orchestrateur AYA pour traiter le message
        # L'orchestrateur gère automatiquement:
        # - L'analyse de documents (cartes grises, passeports, etc.)
        # - Le calcul des quotations
        # - La création client et souscription
        # - L'initiation des paiements
        # - Tout le workflow de A à Z
        response = await aya_orchestrator.process_conversation(
            user_message=msg,
            session_id=session_id,
            user_phone=user_phone,
            media_url=media_url
        )

        logger.info(f"✅ Réponse générée pour session {session_id}")

        # Construire la réponse
        return InferenceResponse(
            reply=response,
            session_id=session_id,
            metadata={
                "model": model,
                "temperature": temperature,
                "timeline": timeline,
                "system": "openai-agent-sdk",
                "orchestrator": "aya"
            }
        )

    except Exception as e:
        logger.error(f"❌ Erreur chat endpoint: {e}", exc_info=True)
        return InferenceResponse(
            reply="Désolée, j'ai rencontré une erreur. Pouvez-vous réessayer?",
            session_id=session_id,
            metadata={"error": str(e)}
        )


@router.get("/session/{session_id}")
async def get_session_state(session_id: str):
    """
    Récupère l'état d'une session

    Args:
        session_id: ID de la session

    Returns:
        État de la session avec l'historique de conversation
    """
    try:
        from app.services.redis_client import redis_service

        state = await redis_service.get_conversation_state(session_id)

        if state is None:
            raise HTTPException(status_code=404, detail="Session non trouvée")

        return {
            "session_id": state.session_id,
            "user_phone": state.user_phone,
            "current_step": state.current_step,
            "product_type": state.product_type,
            "quotation_generated": state.quotation_result is not None,
            "payment_initiated": state.payment_initiated,
            "message_count": len(state.message_history),
            "last_messages": state.message_history[-5:] if state.message_history else [],
            "system": "openai-agent-sdk"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Supprime une session (réinitialisation complète)

    Args:
        session_id: ID de la session

    Returns:
        Confirmation de suppression
    """
    try:
        from app.services.redis_client import redis_service

        success = await redis_service.delete_conversation_state(session_id)

        if success:
            return {
                "message": "Session supprimée avec succès",
                "session_id": session_id,
                "system": "openai-agent-sdk"
            }
        else:
            raise HTTPException(status_code=404, detail="Session non trouvée")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur suppression session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
