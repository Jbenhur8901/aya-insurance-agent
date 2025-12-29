"""
Schémas Pydantic pour l'application AYA
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from uuid import UUID


# ============================================================================
# MESSAGE SCHEMAS (GENERIC)
# ============================================================================

class IncomingMessage(BaseModel):
    """Message entrant (générique)"""
    session_id: str
    user_phone: str
    message_type: Literal["text", "image", "audio", "document"] = "text"
    content: str
    media_url: Optional[str] = None
    timestamp: Optional[datetime] = None


class OutgoingMessage(BaseModel):
    """Réponse sortante (générique)"""
    message: str
    media_url: Optional[str] = None
    media_type: Optional[Literal["image", "document", "audio"]] = None
    session_id: str
    metadata: Optional[Dict[str, Any]] = None


class InferenceResponse(BaseModel):
    """Réponse de l'agent (format inference)"""
    reply: str
    session_id: str
    metadata: Optional[Dict[str, Any]] = None
    media_url: Optional[str] = None
    media_type: Optional[Literal["image", "document", "audio"]] = None


# ============================================================================
# CLIENT SCHEMAS
# ============================================================================

class ClientBase(BaseModel):
    """Base client information"""
    whatsappnumber: str
    fullname: Optional[str] = None
    dateofbirth: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    profession: Optional[str] = None


class ClientCreate(ClientBase):
    """Client creation schema"""
    username: Optional[str] = None
    status: str = "active"


class ClientInDB(ClientBase):
    """Client from database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: Optional[str] = None
    username: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# SOUSCRIPTION SCHEMAS
# ============================================================================

class SouscriptionBase(BaseModel):
    """Base souscription information"""
    producttype: Literal["NSIA AUTO", "NSIA VOYAGE", "NSIA INDIVIDUEL ACCIDENTS", "NSIA MULTIRISQUE HABITATION"]
    prime_ttc: Optional[float] = None
    coverage_duration: Optional[str] = None
    codepromo: Optional[str] = None
    source: str = "whatsapp"


class SouscriptionCreate(SouscriptionBase):
    """Souscription creation"""
    client_id: UUID
    status: str = "en_cours"


class SouscriptionInDB(SouscriptionBase):
    """Souscription from database"""
    id: UUID
    client_id: UUID
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# PRODUCT-SPECIFIC SCHEMAS
# ============================================================================

class AutoData(BaseModel):
    """Données pour souscription AUTO"""
    fullname: str
    immatriculation: str
    power: str
    seat_number: int
    fuel_type: str
    brand: str
    chassis_number: Optional[str] = None
    phone: str
    model: Optional[str] = None
    address: Optional[str] = None
    profession: Optional[str] = None
    prime_ttc: int
    coverage: str  # "3M", "6M", "12M"
    quotation: Dict[str, Any]
    documentUrl: Optional[str] = None


class VoyageData(BaseModel):
    """Données pour souscription VOYAGE"""
    full_name: str
    passport_number: str
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None
    place_of_birth: Optional[str] = None
    sex: Optional[str] = None
    profession: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    place_of_issue: Optional[str] = None
    country_code: Optional[str] = None
    type: Optional[str] = None
    prime_ttc: str
    coverage: str
    documentUrl: Optional[str] = None


class IACData(BaseModel):
    """Données pour souscription IAC (Individuelle Accident)"""
    fullname: str
    statutPro: str  # "Commerçant", "Travailleur Indépendant", "Entrepreneur"
    secteurActivite: str
    lieuTravail: str
    prime_ttc: str
    coverage: str
    typeDocument: str  # "Passeport", "NIU", "CNI"
    documentUrl: Optional[str] = None
    extracted_infos: Optional[Dict[str, Any]] = None


class MRHData(BaseModel):
    """Données pour souscription MRH (Multirisque Habitation)"""
    fullname: str
    forfaitMrh: str
    prime_ttc: str
    coverage: str
    typeDocument: str
    documentUrl: Optional[str] = None
    extracted_infos: Optional[Dict[str, Any]] = None


# ============================================================================
# PAYMENT SCHEMAS
# ============================================================================

class PaymentRequest(BaseModel):
    """Requête de paiement"""
    amount: float
    phone: str
    provider: Literal["momo", "airtel"]
    reference: str
    description: Optional[str] = "Paiement assurance NSIA"


class PaymentResponse(BaseModel):
    """Réponse après initiation paiement"""
    status: str
    transaction_reference: str
    message: Optional[str] = None


class PaymentCallback(BaseModel):
    """Webhook callback de paiement"""
    transaction_id: str
    reference: str
    status: Literal["success", "failed", "pending"]
    amount: Optional[float] = None
    provider: str
    raw_data: Optional[Dict[str, Any]] = None


# ============================================================================
# QUOTATION SCHEMAS
# ============================================================================

class QuotationRequest(BaseModel):
    """Requête de quotation"""
    product_type: Literal["auto", "voyage", "iac", "mrh"]
    data: Dict[str, Any]


class QuotationResponse(BaseModel):
    """Réponse de quotation"""
    product_type: str
    offers: Dict[str, Any]  # OFFRE_3_MOIS, OFFRE_6_MOIS, OFFRE_12_MOIS
    informations: Dict[str, Any]


# ============================================================================
# DOCUMENT SCHEMAS
# ============================================================================

class DocumentUpload(BaseModel):
    """Upload de document"""
    souscription_id: UUID
    document_url: str
    type: str
    nom: Optional[str] = None


class DocumentInDB(BaseModel):
    """Document depuis la DB"""
    id: UUID
    souscription_id: UUID
    document_url: str
    pdf_url: Optional[str] = None
    type: Optional[str] = None
    nom: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CODE PROMO SCHEMAS
# ============================================================================

class CodePromoValidation(BaseModel):
    """Validation de code promo"""
    code: str


class CodePromoInDB(BaseModel):
    """Code promo depuis la DB"""
    id: int
    code: str
    Agent_ID: Optional[UUID] = None
    Agent: Optional[str] = None
    Type_Reduction: Optional[str] = None
    Valeur: Optional[float] = None
    Expiration: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
