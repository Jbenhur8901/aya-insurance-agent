"""
Client Supabase pour la gestion de la base de données
"""
from supabase import create_client, Client
from app.config import settings
from app.models.schemas import (
    ClientCreate, ClientInDB,
    SouscriptionCreate, SouscriptionInDB,
    DocumentUpload,
    AutoData, VoyageData, IACData, MRHData
)
from typing import Optional, Dict, Any, List
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service de gestion Supabase"""

    def __init__(self):
        """Initialise le client Supabase"""
        # Utiliser la service_role key si disponible (pour bypass RLS)
        # Sinon utiliser la clé anon (moins de permissions)
        supabase_key = settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_KEY

        self.client: Client = create_client(
            settings.SUPABASE_URL,
            supabase_key
        )
        logger.info("Supabase client initialisé")

    # ========================================================================
    # CLIENTS
    # ========================================================================

    async def get_client_by_phone(self, phone: str) -> Optional[ClientInDB]:
        """Récupère un client par numéro WhatsApp"""
        try:
            response = self.client.table("clients").select("*").eq("whatsappnumber", phone).execute()
            if response.data and len(response.data) > 0:
                return ClientInDB(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Erreur récupération client: {e}")
            return None

    async def get_client_by_id(self, client_id: UUID) -> Optional[ClientInDB]:
        """Récupère un client par son ID"""
        try:
            response = self.client.table("clients").select("*").eq("id", str(client_id)).execute()
            if response.data and len(response.data) > 0:
                return ClientInDB(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Erreur récupération client par ID: {e}")
            return None

    async def create_client(self, client_data: ClientCreate) -> Optional[ClientInDB]:
        """Crée un nouveau client"""
        try:
            data = client_data.model_dump(exclude_none=True)
            response = self.client.table("clients").insert(data).execute()
            if response.data and len(response.data) > 0:
                logger.info(f"Client créé: {response.data[0]['id']}")
                return ClientInDB(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Erreur création client: {e}")
            return None

    async def update_client(self, client_id: UUID, updates: Dict[str, Any]) -> Optional[ClientInDB]:
        """Met à jour un client"""
        try:
            response = self.client.table("clients").update(updates).eq("id", str(client_id)).execute()
            if response.data and len(response.data) > 0:
                return ClientInDB(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Erreur mise à jour client: {e}")
            return None

    # ========================================================================
    # SOUSCRIPTIONS
    # ========================================================================

    async def create_souscription(self, souscription_data: SouscriptionCreate) -> Optional[SouscriptionInDB]:
        """Crée une nouvelle souscription"""
        try:
            data = souscription_data.model_dump(exclude_none=True)
            data["client_id"] = str(data["client_id"])

            response = self.client.table("souscriptions").insert(data).execute()
            if response.data and len(response.data) > 0:
                logger.info(f"Souscription créée: {response.data[0]['id']}")
                return SouscriptionInDB(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Erreur création souscription: {e}")
            raise

    async def update_souscription(self, souscription_id: UUID, updates: Dict[str, Any]) -> Optional[SouscriptionInDB]:
        """Met à jour une souscription"""
        try:
            response = self.client.table("souscriptions").update(updates).eq("id", str(souscription_id)).execute()
            if response.data and len(response.data) > 0:
                return SouscriptionInDB(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Erreur mise à jour souscription: {e}")
            return None

    async def get_souscription(self, souscription_id: UUID) -> Optional[SouscriptionInDB]:
        """Récupère une souscription"""
        try:
            response = self.client.table("souscriptions").select("*").eq("id", str(souscription_id)).execute()
            if response.data and len(response.data) > 0:
                return SouscriptionInDB(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Erreur récupération souscription: {e}")
            return None

    # ========================================================================
    # SOUSCRIPTIONS PRODUITS SPÉCIFIQUES
    # ========================================================================

    async def create_souscription_auto(self, data: AutoData, souscription_id: UUID) -> bool:
        """Crée une souscription AUTO"""
        try:
            payload = data.model_dump(exclude_none=True)
            payload["souscription_id"] = str(souscription_id)
            # Note: status est dans la table souscriptions, pas ici

            response = self.client.table("souscription_auto").insert(payload).execute()
            return response.data is not None and len(response.data) > 0
        except Exception as e:
            logger.error(f"Erreur création souscription_auto: {e}")
            return False

    async def create_souscription_voyage(self, data: VoyageData, souscription_id: UUID) -> bool:
        """Crée une souscription VOYAGE"""
        try:
            payload = data.model_dump(exclude_none=True)
            payload["souscription_id"] = str(souscription_id)
            # Note: status est dans la table souscriptions, pas ici

            response = self.client.table("souscription_voyage").insert(payload).execute()
            return response.data is not None and len(response.data) > 0
        except Exception as e:
            logger.error(f"Erreur création souscription_voyage: {e}")
            return False

    async def create_souscription_iac(self, data: IACData, souscription_id: UUID) -> bool:
        """Crée une souscription IAC"""
        try:
            payload = data.model_dump(exclude_none=True)
            payload["souscription_id"] = str(souscription_id)
            # Note: status est dans la table souscriptions, pas ici

            response = self.client.table("souscription_iac").insert(payload).execute()
            return response.data is not None and len(response.data) > 0
        except Exception as e:
            logger.error(f"Erreur création souscription_iac: {e}")
            return False

    async def create_souscription_mrh(self, data: MRHData, souscription_id: UUID) -> bool:
        """Crée une souscription MRH"""
        try:
            payload = data.model_dump(exclude_none=True)
            payload["souscription_id"] = str(souscription_id)
            # Note: status est dans la table souscriptions, pas ici

            response = self.client.table("souscription_mrh").insert(payload).execute()
            return response.data is not None and len(response.data) > 0
        except Exception as e:
            logger.error(f"Erreur création souscription_mrh: {e}")
            return False

    # ========================================================================
    # DOCUMENTS
    # ========================================================================

    async def save_document(self, doc_data: DocumentUpload) -> Optional[Dict[str, Any]]:
        """Enregistre un document

        Returns:
            Dict avec les données du document créé, ou None en cas d'erreur
        """
        try:
            payload = {
                "souscription_id": str(doc_data.souscription_id),
                "document_url": doc_data.document_url,
                "type": doc_data.type,
                "nom": doc_data.nom
            }
            response = self.client.table("documents").insert(payload).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Erreur enregistrement document: {e}")
            return None

    async def update_document_pdf(self, souscription_id: UUID, pdf_url: str) -> bool:
        """Met à jour l'URL du PDF généré"""
        try:
            response = self.client.table("documents").update({
                "pdf_url": pdf_url
            }).eq("souscription_id", str(souscription_id)).execute()
            return response.data is not None
        except Exception as e:
            logger.error(f"Erreur mise à jour document PDF: {e}")
            return False

    # ========================================================================
    # CODE PROMO
    # ========================================================================

    async def validate_code_promo(self, code: str) -> Optional[Dict[str, Any]]:
        """Valide un code promo"""
        try:
            response = self.client.table("code_promo").select("*").eq("code", code).execute()
            if response.data and len(response.data) > 0:
                promo = response.data[0]
                # Vérifier expiration si nécessaire
                return promo
            return None
        except Exception as e:
            logger.error(f"Erreur validation code promo: {e}")
            return None

    # ========================================================================
    # TRANSACTIONS
    # ========================================================================

    async def create_transaction(
        self,
        souscription_id: UUID,
        amount: float,
        reference: str,
        payment_method: str,
        status: str = "en_attente"
    ) -> Optional[Dict[str, Any]]:
        """Crée une transaction de paiement

        Args:
            status: Statut de la transaction (en_attente, en_cours, valide, expirée, annulée)
                   Défaut: en_attente

        Returns:
            Dict avec les données de la transaction créée, ou None en cas d'erreur
        """
        try:
            payload = {
                "souscription_id": str(souscription_id),
                "amount": int(amount),
                "reference": reference,
                "payment_method": payment_method,
                "status": status
            }
            response = self.client.table("transactions").insert(payload).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Erreur création transaction: {e}")
            return None

    async def update_transaction_status(self, reference: str, status: str) -> bool:
        """Met à jour le statut d'une transaction"""
        try:
            response = self.client.table("transactions").update({
                "status": status
            }).eq("reference", reference).execute()
            return response.data is not None
        except Exception as e:
            logger.error(f"Erreur mise à jour transaction: {e}")
            return False

    async def get_transaction_by_reference(self, reference: str) -> Optional[Dict[str, Any]]:
        """Récupère une transaction par sa référence"""
        try:
            response = self.client.table("transactions").select("*").eq("reference", reference).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Erreur récupération transaction: {e}")
            return None

    async def update_souscription_status(self, souscription_id: str, status: str) -> bool:
        """Met à jour le statut d'une souscription"""
        try:
            response = self.client.table("souscriptions").update({
                "status": status
            }).eq("id", souscription_id).execute()
            logger.info(f"Souscription {souscription_id} mise à jour: status={status}")
            return response.data is not None
        except Exception as e:
            logger.error(f"Erreur mise à jour souscription: {e}")
            return False

    # ========================================================================
    # STORAGE (pour upload fichiers)
    # ========================================================================

    async def upload_file(self, bucket: str, file_path: str, file_data: bytes) -> Optional[str]:
        """Upload un fichier vers Supabase Storage"""
        try:
            response = self.client.storage.from_(bucket).upload(file_path, file_data)
            if response:
                # Générer l'URL publique
                public_url = self.client.storage.from_(bucket).get_public_url(file_path)
                return public_url
            return None
        except Exception as e:
            logger.error(f"Erreur upload fichier: {e}")
            return None


# Instance globale
supabase_service = SupabaseService()
