"""
Gestion de l'état de conversation et de souscription
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal, List
from datetime import datetime
from uuid import UUID


# ============================================================================
# CONVERSATION STATE
# ============================================================================

class ConversationState(BaseModel):
    """
    État de la conversation stocké dans Redis
    """
    # Identification
    session_id: str
    user_phone: str
    client_id: Optional[UUID] = None
    souscription_id: Optional[UUID] = None

    # Workflow state
    current_step: Literal[
        "greeting",           # Accueil initial
        "product_discovery",  # Découverte du produit
        "info_collection",    # Collecte d'informations
        "quotation",          # Présentation des tarifs
        "payment",            # Processus de paiement
        "confirmation",       # Confirmation finale
        "completed"           # Souscription terminée
    ] = "greeting"

    # Product context
    product_type: Optional[Literal["auto", "voyage", "iac", "mrh"]] = None

    # Collected data (temporary storage)
    collected_data: Dict[str, Any] = Field(default_factory=dict)

    # Quotation data
    quotation_result: Optional[Dict[str, Any]] = None
    selected_coverage: Optional[str] = None  # "3M", "6M", "12M"

    # Payment
    payment_initiated: bool = False
    payment_reference: Optional[str] = None
    payment_provider: Optional[Literal["momo", "airtel"]] = None

    # Code Promo
    code_promo: Optional[str] = None
    promo_applied: bool = False

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_message: Optional[str] = None

    # Conversation history (for context)
    message_history: List[Dict[str, str]] = Field(default_factory=list)

    def add_message(self, role: str, content: str):
        """Ajoute un message à l'historique"""
        self.message_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.last_message = content
        self.updated_at = datetime.utcnow()

    def update_step(self, new_step: str):
        """Met à jour l'étape courante"""
        self.current_step = new_step
        self.updated_at = datetime.utcnow()

    def update_data(self, key: str, value: Any):
        """Met à jour les données collectées"""
        self.collected_data[key] = value
        self.updated_at = datetime.utcnow()

    def get_data(self, key: str, default: Any = None) -> Any:
        """Récupère une donnée collectée"""
        return self.collected_data.get(key, default)

    def to_redis_dict(self) -> dict:
        """Convertit en dictionnaire pour Redis"""
        return self.model_dump(mode='json')

    @classmethod
    def from_redis_dict(cls, data: dict) -> "ConversationState":
        """Crée une instance depuis un dictionnaire Redis"""
        return cls(**data)


# ============================================================================
# SOUSCRIPTION STATE (Contexte métier)
# ============================================================================

class SouscriptionContext(BaseModel):
    """
    Contexte métier de la souscription
    Utilisé par les agents pour prendre des décisions
    """
    # IDs
    souscription_id: Optional[UUID] = None
    client_id: Optional[UUID] = None

    # Product
    product_type: Literal["auto", "voyage", "iac", "mrh"]

    # Statut
    status: Literal["draft", "validated", "payment_pending", "paid", "completed", "cancelled"] = "draft"

    # Data validation status
    has_identity_document: bool = False
    has_product_document: bool = False  # Carte grise pour auto, passeport pour voyage
    identity_extracted: bool = False
    product_data_extracted: bool = False

    # Quotation
    quotation_generated: bool = False
    quotation_data: Optional[Dict[str, Any]] = None
    selected_offer: Optional[str] = None  # "OFFRE_3_MOIS", "OFFRE_6_MOIS", "OFFRE_12_MOIS"
    final_amount: Optional[float] = None

    # Documents URLs
    identity_doc_url: Optional[str] = None
    product_doc_url: Optional[str] = None
    receipt_pdf_url: Optional[str] = None
    attestation_pdf_url: Optional[str] = None

    # Payment
    payment_initiated: bool = False
    payment_completed: bool = False
    payment_reference: Optional[str] = None
    transaction_id: Optional[str] = None

    # Code Promo
    code_promo: Optional[str] = None
    discount_applied: Optional[float] = None

    # Next required action
    next_action: Optional[str] = None

    def is_ready_for_quotation(self) -> bool:
        """Vérifie si toutes les données sont prêtes pour la quotation"""
        return (
            self.product_data_extracted and
            (self.identity_extracted or self.has_identity_document)
        )

    def is_ready_for_payment(self) -> bool:
        """Vérifie si la souscription est prête pour le paiement"""
        return (
            self.quotation_generated and
            self.selected_offer is not None and
            self.final_amount is not None
        )

    def can_generate_receipt(self) -> bool:
        """Vérifie si on peut générer le reçu"""
        return self.payment_completed and self.souscription_id is not None


# ============================================================================
# AGENT RESPONSE FORMAT
# ============================================================================

class AgentResponse(BaseModel):
    """
    Format de réponse standardisé pour tous les agents
    """
    agent_name: str
    success: bool
    message: str  # Message à envoyer à l'utilisateur
    data: Optional[Dict[str, Any]] = None
    next_step: Optional[str] = None
    next_agent: Optional[str] = None
    error: Optional[str] = None
    requires_user_action: bool = False
    action_type: Optional[Literal["upload_document", "choose_option", "confirm_payment"]] = None
    options: Optional[List[str]] = None  # Pour les choix multiples


# ============================================================================
# SUPERVISOR DECISION
# ============================================================================

class SupervisorDecision(BaseModel):
    """
    Décision du Supervisor sur le prochain agent à appeler
    """
    next_agent: Literal[
        "vision",
        "product",
        "quotation",
        "database",
        "payment",
        "receipt",
        "supervisor"  # Continue avec le supervisor
    ]
    reason: str
    context_update: Optional[Dict[str, Any]] = None
    immediate_response: Optional[str] = None  # Réponse immédiate avant de déléguer
