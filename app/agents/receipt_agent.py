"""
RECEIPT AGENT - Génération des documents (reçus, attestations)
"""
from app.tools.receipts import generate_receipt_from_pricing, generate_product_receipt_pdf
from app.services.supabase_client import supabase_service
from app.models.state import AgentResponse, ConversationState
from app.models.schemas import DocumentUpload
import os
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)


class ReceiptAgent:
    """Agent de génération de documents"""

    def __init__(self):
        """Initialise Receipt Agent"""
        self.db = supabase_service
        logger.info("Receipt Agent initialisé")

    async def generate_and_send_receipt(
        self,
        state: ConversationState
    ) -> AgentResponse:
        """
        Génère le reçu + attestation

        Args:
            state: État de conversation avec toutes les données

        Returns:
            AgentResponse avec l'URL du PDF généré
        """
        try:
            if not state.souscription_id:
                return AgentResponse(
                    agent_name="receipt",
                    success=False,
                    message="Impossible de générer le reçu - souscription manquante.",
                    error="No souscription_id"
                )

            # Générer le PDF
            pdf_path = await self._generate_pdf(state)

            if not pdf_path:
                return AgentResponse(
                    agent_name="receipt",
                    success=False,
                    message="Erreur génération du reçu.",
                    error="PDF generation failed"
                )

            # Upload vers Supabase Storage
            pdf_url = await self._upload_pdf(pdf_path, state.souscription_id)

            if not pdf_url:
                return AgentResponse(
                    agent_name="receipt",
                    success=False,
                    message="Erreur upload du reçu.",
                    error="PDF upload failed"
                )

            # Sauvegarder dans la DB
            await self.db.save_document(
                DocumentUpload(
                    souscription_id=state.souscription_id,
                    document_url=pdf_url,
                    type="recu",
                    nom=f"Recu_{state.souscription_id}.pdf"
                )
            )

            # Message final avec URL du PDF
            message = f"""🎉 **Souscription terminée avec succès!**

✅ Votre reçu de paiement est prêt!

📄 [Télécharger votre reçu]({pdf_url})

🙏 Merci d'avoir choisi NSIA Assurances!

Pour toute question, contactez le service client NSIA au +242 06 XXX XX XX.

---
💚 AYA - Votre conseillère digitale NSIA"""

            state.update_step("completed")

            return AgentResponse(
                agent_name="receipt",
                success=True,
                message=message,
                data={
                    "pdf_url": pdf_url,
                    "media_url": pdf_url,
                    "media_type": "document"
                },
                next_agent="supervisor"
            )

        except Exception as e:
            logger.error(f"Erreur generate_and_send_receipt: {e}")
            return AgentResponse(
                agent_name="receipt",
                success=False,
                message="Erreur lors de la génération des documents.",
                error=str(e)
            )

    async def _generate_pdf(self, state: ConversationState) -> Optional[str]:
        """Génère le PDF du reçu"""
        try:
            # Nom du fichier temporaire
            filename = f"/tmp/recu_{state.souscription_id}.pdf"

            if state.product_type == "auto":
                # Récupérer les données
                carte_grise = state.get_data("carte_grise_data")
                quotation = state.quotation_result
                periode = state.selected_coverage

                # Générer le reçu AUTO
                success = generate_receipt_from_pricing(
                    output_filename=filename,
                    pricing_data=quotation,
                    periode=periode,
                    nom_complet=carte_grise.get("fullname", "N/A"),
                    telephone=state.user_phone,
                    ville=carte_grise.get("address", "N/A"),
                    vehicule_brand=f"{carte_grise.get('brand', 'N/A')} {carte_grise.get('model', '')}",
                    immatriculation=carte_grise.get("immatriculation", "N/A"),
                    promo_code=state.code_promo,
                    is_paid=True
                )

            elif state.product_type == "voyage":
                # Générer le reçu VOYAGE
                passport = state.get_data("passeport_data")
                tarif = state.quotation_result.get("tarif_ttc", 0)

                success = generate_product_receipt_pdf(
                    output_filename=filename,
                    nom_complet=passport.get("full_name", "N/A"),
                    telephone=state.user_phone,
                    ville=passport.get("place_of_birth", "N/A"),
                    product_type="VOYAGE",
                    prime_a_payer_ttc=str(tarif),
                    promo_code=state.code_promo,
                    couverture=state.selected_coverage,
                    product_name="Assurance Voyage"
                )

            else:
                # TODO: Implémenter IAC et MRH
                success = False

            if success and os.path.exists(filename):
                return filename

            return None

        except Exception as e:
            logger.error(f"Erreur génération PDF: {e}")
            return None

    async def _upload_pdf(self, pdf_path: str, souscription_id) -> Optional[str]:
        """Upload le PDF vers Supabase Storage"""
        try:
            # Lire le fichier
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()

            # Upload vers Supabase
            file_path = f"receipts/{souscription_id}.pdf"
            url = await self.db.upload_file("receipts", file_path, pdf_data)

            # Supprimer le fichier temporaire
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

            return url

        except Exception as e:
            logger.error(f"Erreur upload PDF: {e}")
            return None


# Instance globale
receipt_agent = ReceiptAgent()
