"""
Client Redis/Upstash pour la gestion de la mémoire de conversation
"""
from redis import Redis
from app.config import settings
from app.models.state import ConversationState
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)


class RedisService:
    """Service de gestion Redis pour la mémoire de conversation"""

    def __init__(self):
        """Initialise le client Redis/Upstash"""
        try:
            redis_url = settings.REDIS_URL

            # Convertir l'URL Upstash (https://) en format Redis standard (rediss://)
            if redis_url and redis_url.startswith('https://'):
                redis_url = redis_url.replace('https://', 'rediss://')
                logger.info(f"Converted Upstash URL to Redis URL format")

            # Pour Upstash Redis, on utilise from_url avec le token dans l'URL
            # ou en utilisant les headers appropriés
            if hasattr(settings, 'REDIS_TOKEN') and settings.REDIS_TOKEN:
                # Upstash Redis avec token
                self.client = Redis.from_url(
                    redis_url,
                    decode_responses=True,
                    password=settings.REDIS_TOKEN
                )
            else:
                # Redis standard
                self.client = Redis.from_url(
                    redis_url,
                    decode_responses=True
                )
            logger.info("Redis client initialisé")
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}. Running without Redis cache.")
            self.client = None

    def _get_session_key(self, session_id: str) -> str:
        """Génère la clé Redis pour une session"""
        return f"session:{session_id}"

    async def get_conversation_state(self, session_id: str) -> Optional[ConversationState]:
        """
        Récupère l'état de conversation depuis Redis

        Args:
            session_id: ID de la session

        Returns:
            ConversationState ou None si pas trouvé
        """
        if self.client is None:
            logger.warning("Redis client not available. Returning None for conversation state.")
            return None

        try:
            key = self._get_session_key(session_id)
            data = self.client.get(key)

            if data:
                state_dict = json.loads(data)
                return ConversationState.from_redis_dict(state_dict)

            # Nouvelle session
            logger.info(f"Nouvelle session: {session_id}")
            return None

        except Exception as e:
            logger.error(f"Erreur récupération state Redis: {e}")
            return None

    async def save_conversation_state(
        self,
        session_id: str,
        state: ConversationState,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Sauvegarde l'état de conversation dans Redis

        Args:
            session_id: ID de la session
            state: État de conversation
            ttl: Time to live en secondes (défaut: settings.SESSION_TTL)

        Returns:
            True si succès
        """
        if self.client is None:
            logger.warning("Redis client not available. Cannot save conversation state.")
            return False

        try:
            key = self._get_session_key(session_id)
            data = json.dumps(state.to_redis_dict())

            # Définir la valeur
            self.client.set(key, data)

            # Définir l'expiration
            ttl = ttl or settings.SESSION_TTL
            self.client.expire(key, ttl)

            logger.info(f"State sauvegardé pour session {session_id}, TTL: {ttl}s")
            return True

        except Exception as e:
            logger.error(f"Erreur sauvegarde state Redis: {e}")
            return False

    async def update_conversation_state(
        self,
        session_id: str,
        updates: dict,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Met à jour partiellement l'état de conversation

        Args:
            session_id: ID de la session
            updates: Dictionnaire des champs à mettre à jour
            ttl: Time to live en secondes

        Returns:
            True si succès
        """
        try:
            # Récupérer l'état actuel
            state = await self.get_conversation_state(session_id)

            if not state:
                logger.warning(f"Impossible de mettre à jour - session introuvable: {session_id}")
                return False

            # Appliquer les mises à jour
            for key, value in updates.items():
                if hasattr(state, key):
                    setattr(state, key, value)

            # Sauvegarder
            return await self.save_conversation_state(session_id, state, ttl)

        except Exception as e:
            logger.error(f"Erreur mise à jour state Redis: {e}")
            return False

    async def delete_conversation_state(self, session_id: str) -> bool:
        """
        Supprime l'état de conversation

        Args:
            session_id: ID de la session

        Returns:
            True si succès
        """
        try:
            key = self._get_session_key(session_id)
            self.client.delete(key)
            logger.info(f"Session supprimée: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Erreur suppression state Redis: {e}")
            return False

    async def extend_session_ttl(self, session_id: str, ttl: Optional[int] = None) -> bool:
        """
        Prolonge la durée de vie d'une session

        Args:
            session_id: ID de la session
            ttl: Nouvelle durée de vie en secondes

        Returns:
            True si succès
        """
        try:
            key = self._get_session_key(session_id)
            ttl = ttl or settings.SESSION_TTL
            self.client.expire(key, ttl)
            return True

        except Exception as e:
            logger.error(f"Erreur extension TTL: {e}")
            return False

    async def session_exists(self, session_id: str) -> bool:
        """
        Vérifie si une session existe

        Args:
            session_id: ID de la session

        Returns:
            True si existe
        """
        try:
            key = self._get_session_key(session_id)
            return self.client.exists(key) > 0

        except Exception as e:
            logger.error(f"Erreur vérification session: {e}")
            return False

    # ========================================================================
    # MÉTHODES UTILITAIRES POUR MESSAGE HISTORY
    # ========================================================================

    async def add_message_to_history(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> bool:
        """
        Ajoute un message à l'historique de conversation

        Args:
            session_id: ID de la session
            role: Rôle (user, assistant, system)
            content: Contenu du message

        Returns:
            True si succès
        """
        try:
            state = await self.get_conversation_state(session_id)
            if state:
                state.add_message(role, content)
                return await self.save_conversation_state(session_id, state)
            return False

        except Exception as e:
            logger.error(f"Erreur ajout message: {e}")
            return False

    async def get_message_history(self, session_id: str, limit: int = 10) -> list:
        """
        Récupère l'historique des messages

        Args:
            session_id: ID de la session
            limit: Nombre maximum de messages à retourner

        Returns:
            Liste des messages
        """
        try:
            state = await self.get_conversation_state(session_id)
            if state and state.message_history:
                return state.message_history[-limit:]
            return []

        except Exception as e:
            logger.error(f"Erreur récupération historique: {e}")
            return []


# Instance globale
redis_service = RedisService()
