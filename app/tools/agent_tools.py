"""
Outils pour le système agentique AYA basé sur OpenAI Agent SDK
Transforme les fonctionnalités existantes en function_tools
"""
import logging
from typing import Dict, Any, Optional, Literal
from agents import function_tool
from app.tools.quotation import (
    image_processor,
    Grey_card, PassportInfo, CNIInfo, NIUInfo,
    VISION_INSTRUCTION,
    ttcAuto_all, ttc_auto_cat4, voyage_api
)
from app.services.supabase_client import supabase_service
from app.services.mobile_money import mobile_money_service
from app.models.schemas import ClientCreate, SouscriptionCreate, PaymentRequest
from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# VISION TOOLS - Analyse de documents
# ============================================================================

@function_tool
async def analyze_carte_grise(image_url: str) -> Dict[str, Any]:
    """
    Analyse une carte grise et extrait toutes les informations nécessaires.

    Args:
        image_url: URL de l'image de la carte grise

    Returns:
        Dictionnaire contenant les informations extraites (fullname, immatriculation, power,
        seat_number, fuel_type, brand, chassis_number, phone, model, address, profession)
    """
    try:
        logger.info(f"🔧 [OUTIL APPELÉ] analyze_carte_grise")
        logger.info(f"🔍 Analyse carte grise: {image_url}")

        result = image_processor(
            image_path=image_url,
            vision_model=settings.VISION_MODEL,
            vision_instruction=VISION_INSTRUCTION,
            response_schema=Grey_card
        )

        logger.info(f"✅ Carte grise analysée avec succès")
        return result

    except Exception as e:
        logger.error(f"❌ Erreur analyse carte grise: {e}")
        return {
            "error": str(e),
            "content": "Impossible d'analyser l'image. Veuillez envoyer une photo plus claire."
        }


@function_tool
async def analyze_passport(image_url: str) -> Dict[str, Any]:
    """
    Analyse un passeport et extrait les informations d'identité.

    Args:
        image_url: URL de l'image du passeport

    Returns:
        Dictionnaire contenant les informations du passeport
    """
    try:
        logger.info(f"🔧 [OUTIL APPELÉ] analyze_passport")
        logger.info(f"🔍 Analyse passeport: {image_url}")

        result = image_processor(
            image_path=image_url,
            vision_model=settings.VISION_MODEL,
            vision_instruction="Extrait les informations du passeport",
            response_schema=PassportInfo
        )

        logger.info(f"✅ Passeport analysé avec succès")
        return result

    except Exception as e:
        logger.error(f"❌ Erreur analyse passeport: {e}")
        return {
            "error": str(e),
            "content": "Impossible d'analyser le passeport."
        }


@function_tool
async def analyze_cni(image_url: str) -> Dict[str, Any]:
    """
    Analyse une Carte Nationale d'Identité (CNI).

    Args:
        image_url: URL de l'image de la CNI

    Returns:
        Dictionnaire contenant les informations de la CNI
    """
    try:
        logger.info(f"🔍 Analyse CNI: {image_url}")

        result = image_processor(
            image_path=image_url,
            vision_model=settings.VISION_MODEL,
            vision_instruction="Extrait les informations de la CNI",
            response_schema=CNIInfo
        )

        logger.info(f"✅ CNI analysée avec succès")
        return result

    except Exception as e:
        logger.error(f"❌ Erreur analyse CNI: {e}")
        return {
            "error": str(e),
            "content": "Impossible d'analyser la CNI."
        }


@function_tool
async def analyze_niu(image_url: str) -> Dict[str, Any]:
    """
    Analyse un Numéro d'Identification Unique (NIU).

    Args:
        image_url: URL de l'image du NIU

    Returns:
        Dictionnaire contenant les informations du NIU
    """
    try:
        logger.info(f"🔍 Analyse NIU: {image_url}")

        result = image_processor(
            image_path=image_url,
            vision_model=settings.VISION_MODEL,
            vision_instruction="Extrait les informations du NIU",
            response_schema=NIUInfo
        )

        logger.info(f"✅ NIU analysé avec succès")
        return result

    except Exception as e:
        logger.error(f"❌ Erreur analyse NIU: {e}")
        return {
            "error": str(e),
            "content": "Impossible d'analyser le NIU."
        }


# ============================================================================
# QUOTATION TOOLS - Calcul des tarifs
# ============================================================================

@function_tool
async def calculate_auto_quotation(
    power: int,
    seat_number: int,
    fuel_type: str = "ESSENCE",
    modele: str = "VOITURE",
    usage: str = "PROMENADE/AFFAIRES"
) -> Dict[str, Any]:
    """
    Calcule les tarifs d'assurance AUTO pour les différentes périodes (3, 6, 12 mois).

    Args:
        power: Puissance fiscale du véhicule (en CV)
        seat_number: Nombre de places
        fuel_type: Type de carburant (ESSENCE ou DIESEL)
        modele: Modèle de véhicule (VOITURE, TAXI, PICNIC, MINI-BUS, COASTER)
        usage: Usage du véhicule (PROMENADE/AFFAIRES, etc.)

    Returns:
        Dictionnaire avec les offres pour 3, 6 et 12 mois (OFFRE_3_MOIS, OFFRE_6_MOIS, OFFRE_12_MOIS)
    """
    try:
        logger.info(f"🔧 [OUTIL APPELÉ] calculate_auto_quotation")
        logger.info(f"💰 Calcul quotation AUTO: {power}CV, {seat_number} places, {fuel_type}")

        # Déterminer la catégorie
        if modele in ["TAXI", "PICNIC", "MINI-BUS", "COASTER"]:
            # CAT 4 - Transport public
            pricing = ttc_auto_cat4(
                power=power,
                energy=fuel_type.upper(),
                modele=modele,
                place=seat_number
            )
        else:
            # CAT 1-3 - Véhicules particuliers
            pricing = ttcAuto_all(
                power=power,
                energy=fuel_type.upper(),
                place=seat_number,
                modele=modele,
                usage=usage
            )

        logger.info(f"✅ Quotation AUTO calculée: {pricing.get('OFFRE_12_MOIS', {}).get('PRIME_TOTALE', 0)} FCFA (12M)")
        return pricing

    except Exception as e:
        logger.error(f"❌ Erreur calcul quotation AUTO: {e}")
        return {
            "error": str(e),
            "message": "Erreur lors du calcul du devis AUTO."
        }


@function_tool
async def calculate_voyage_quotation(
    client_type: str,
    zone: str,
    product: str,
    duration_days: int
) -> Dict[str, Any]:
    """
    Calcule le tarif d'assurance VOYAGE.

    Args:
        client_type: Type de client (Particulier, Étudiant, Pèlerin)
        zone: Zone de destination (Europe, Monde, etc.)
        product: Produit voyage
        duration_days: Durée du séjour en jours

    Returns:
        Dictionnaire avec le tarif TTC
    """
    try:
        logger.info(f"🔧 [OUTIL APPELÉ] calculate_voyage_quotation")
        logger.info(f"💰 Calcul quotation VOYAGE: {zone}, {duration_days} jours")

        tarif_ttc = voyage_api(
            client=client_type,
            zone=zone,
            product=product,
            duration=duration_days
        )

        if tarif_ttc == 0:
            return {
                "error": "Aucun tarif trouvé",
                "message": "Aucun tarif disponible pour ces critères."
            }

        logger.info(f"✅ Quotation VOYAGE calculée: {tarif_ttc} FCFA")
        return {
            "tarif_ttc": tarif_ttc,
            "zone": zone,
            "duration": duration_days,
            "client_type": client_type
        }

    except Exception as e:
        logger.error(f"❌ Erreur calcul quotation VOYAGE: {e}")
        return {
            "error": str(e),
            "message": "Erreur lors du calcul du devis VOYAGE."
        }


@function_tool
async def calculate_iac_quotation(statut: Optional[str] = None) -> Dict[str, Any]:
    """
    Calcule le tarif d'assurance Individuelle Accident (IAC).

    Args:
        statut: Statut du client (particulier, salarie, etc.). Si None, retourne tous les tarifs.

    Returns:
        Dictionnaire avec les tarifs IAC
    """
    try:
        logger.info(f"🔧 [OUTIL APPELÉ] calculate_iac_quotation")
        logger.info(f"💰 Calcul quotation IAC: {statut or 'tous les statuts'}")

        from app.tools.quotation import get_iac_quotation

        quotation = get_iac_quotation(statut)

        logger.info(f"✅ Quotation IAC calculée")
        return quotation

    except Exception as e:
        logger.error(f"❌ Erreur calcul quotation IAC: {e}")
        return {
            "error": str(e),
            "message": "Erreur lors du calcul du devis IAC."
        }


@function_tool
async def calculate_mrh_quotation(forfait: Optional[str] = None) -> Dict[str, Any]:
    """
    Calcule le tarif d'assurance Multirisque Habitation (MRH).

    Args:
        forfait: Nom du forfait (standard, equilibre, confort, premium). Si None, retourne tous les forfaits.

    Returns:
        Dictionnaire avec les tarifs MRH
    """
    try:
        logger.info(f"🔧 [OUTIL APPELÉ] calculate_mrh_quotation")
        logger.info(f"💰 Calcul quotation MRH: {forfait or 'tous les forfaits'}")

        from app.tools.quotation import get_mrh_quotation

        quotation = get_mrh_quotation(forfait)

        logger.info(f"✅ Quotation MRH calculée")
        return quotation

    except Exception as e:
        logger.error(f"❌ Erreur calcul quotation MRH: {e}")
        return {
            "error": str(e),
            "message": "Erreur lors du calcul du devis MRH."
        }


# ============================================================================
# DATABASE TOOLS - Gestion BDD
# ============================================================================

@function_tool
async def get_or_create_client(phone_number: str, fullname: Optional[str] = None) -> Dict[str, Any]:
    """
    Récupère un client existant ou en crée un nouveau dans la base de données.

    Args:
        phone_number: Numéro de téléphone du client
        fullname: Nom complet du client (optionnel)

    Returns:
        Dictionnaire avec client_id et informations du client
    """
    try:
        logger.info(f"👤 Recherche/création client: {phone_number}")

        # Chercher client existant
        client = await supabase_service.get_client_by_phone(phone_number)

        if client:
            logger.info(f"✅ Client existant trouvé: {client.id}")
            return {
                "client_id": str(client.id),
                "fullname": client.fullname,
                "existing": True,
                "message": f"Bienvenue {client.fullname or 'cher client'}!"
            }

        # Créer nouveau client
        client_data = ClientCreate(
            whatsappnumber=phone_number,
            fullname=fullname,
            status="active"
        )

        new_client = await supabase_service.create_client(client_data)

        if new_client:
            logger.info(f"✅ Nouveau client créé: {new_client.id}")
            return {
                "client_id": str(new_client.id),
                "fullname": new_client.fullname,
                "existing": False,
                "message": "Profil créé avec succès!"
            }

        return {
            "error": "Échec création client",
            "message": "Impossible de créer le profil client."
        }

    except Exception as e:
        logger.error(f"❌ Erreur get_or_create_client: {e}")
        return {
            "error": str(e),
            "message": "Erreur lors de la gestion du client."
        }


@function_tool
async def create_souscription(
    client_id: str,
    product_type: Literal["NSIA AUTO", "NSIA VOYAGE", "NSIA INDIVIDUEL ACCIDENTS", "NSIA MULTIRISQUE HABITATION"],
    prime_ttc: float,
    coverage_duration: str
) -> Dict[str, Any]:
    """
    Crée une nouvelle souscription d'assurance dans la base de données.

    Args:
        client_id: ID du client (UUID)
        product_type: Type de produit - DOIT être exactement l'une des valeurs suivantes:
                     "NSIA AUTO", "NSIA VOYAGE", "NSIA INDIVIDUEL ACCIDENTS", "NSIA MULTIRISQUE HABITATION"
        prime_ttc: Prime TTC en FCFA
        coverage_duration: Durée de couverture (3M, 6M, 12M)

    Returns:
        Dictionnaire avec souscription_id
    """
    try:
        logger.info(f"📝 Création souscription: {product_type}, {prime_ttc} FCFA")

        from uuid import UUID

        # Valider et convertir client_id en UUID
        try:
            client_uuid = UUID(client_id)
        except (ValueError, AttributeError) as e:
            logger.error(f"❌ UUID invalide pour client_id: {client_id}")
            return {
                "error": "UUID invalide",
                "message": f"Le client_id fourni n'est pas un UUID valide: {client_id}"
            }

        # Vérifier que le client existe dans la DB
        client = await supabase_service.get_client_by_id(client_uuid)
        if not client:
            logger.error(f"❌ Client inexistant dans la DB: {client_id}")
            return {
                "error": "Client inexistant",
                "message": f"Le client avec l'ID {client_id} n'existe pas dans la base de données. Veuillez d'abord créer le client avec get_or_create_client."
            }

        logger.info(f"✅ Client validé: {client.id}")

        souscription_data = SouscriptionCreate(
            client_id=client_uuid,
            producttype=product_type,
            prime_ttc=prime_ttc,
            coverage_duration=coverage_duration,
            status="en_cours"
        )

        souscription = await supabase_service.create_souscription(souscription_data)

        if souscription:
            logger.info(f"✅ Souscription créée: {souscription.id}")
            return {
                "souscription_id": str(souscription.id),
                "product_type": product_type,
                "prime_ttc": prime_ttc,
                "coverage": coverage_duration,
                "message": "Souscription enregistrée avec succès!"
            }

        return {
            "error": "Échec création souscription",
            "message": "Impossible de créer la souscription."
        }

    except Exception as e:
        logger.error(f"❌ Erreur create_souscription: {e}")
        return {
            "error": str(e),
            "message": "Erreur lors de la création de la souscription."
        }


# ============================================================================
# PAYMENT TOOLS - Gestion paiements
# ============================================================================

@function_tool
async def save_auto_details(
    souscription_id: str,
    fullname: str,
    immatriculation: str,
    power: str,
    seat_number: int,
    fuel_type: str,
    brand: str,
    phone: str,
    prime_ttc: int,
    coverage: str,
    quotation_json: str,
    chassis_number: Optional[str] = None,
    model: Optional[str] = None,
    address: Optional[str] = None,
    profession: Optional[str] = None,
    document_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enregistre les détails d'une souscription AUTO dans souscription_auto.

    Args:
        souscription_id: ID de la souscription (UUID)
        fullname: Nom complet du propriétaire
        immatriculation: Numéro d'immatriculation
        power: Puissance fiscale
        seat_number: Nombre de places
        fuel_type: Type de carburant
        brand: Marque du véhicule
        phone: Numéro de téléphone
        prime_ttc: Prime TTC (int)
        coverage: Période de couverture (3M, 6M, 12M)
        quotation_json: Détails de la quotation en format JSON string
        chassis_number: Numéro de châssis (optionnel)
        model: Modèle du véhicule (optionnel)
        address: Adresse (optionnel)
        profession: Profession (optionnel)
        document_url: URL du document (carte grise) (optionnel)

    Returns:
        Dictionnaire avec le résultat de l'opération
    """
    try:
        logger.info(f"💾 Enregistrement détails AUTO pour souscription: {souscription_id}")

        from uuid import UUID
        from app.models.schemas import AutoData
        import json

        # Parser le JSON de quotation
        quotation = json.loads(quotation_json) if isinstance(quotation_json, str) else quotation_json

        auto_data = AutoData(
            fullname=fullname,
            immatriculation=immatriculation,
            power=power,
            seat_number=seat_number,
            fuel_type=fuel_type,
            brand=brand,
            chassis_number=chassis_number,
            phone=phone,
            model=model,
            address=address,
            profession=profession,
            prime_ttc=prime_ttc,
            coverage=coverage,
            quotation=quotation,
            documentUrl=document_url
        )

        success = await supabase_service.create_souscription_auto(
            data=auto_data,
            souscription_id=UUID(souscription_id)
        )

        if success:
            logger.info(f"✅ Détails AUTO enregistrés pour souscription: {souscription_id}")
            return {
                "success": True,
                "message": "Détails AUTO enregistrés avec succès!"
            }

        return {
            "success": False,
            "error": "Échec enregistrement détails AUTO",
            "message": "Impossible d'enregistrer les détails AUTO."
        }

    except Exception as e:
        logger.error(f"❌ Erreur save_auto_details: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Erreur lors de l'enregistrement des détails AUTO."
        }


@function_tool
async def save_voyage_details(
    souscription_id: str,
    full_name: str,
    passport_number: str,
    prime_ttc: str,
    coverage: str,
    nationality: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    place_of_birth: Optional[str] = None,
    sex: Optional[str] = None,
    profession: Optional[str] = None,
    issue_date: Optional[str] = None,
    expiry_date: Optional[str] = None,
    place_of_issue: Optional[str] = None,
    country_code: Optional[str] = None,
    type: Optional[str] = None,
    document_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enregistre les détails d'une souscription VOYAGE dans souscription_voyage.

    Args:
        souscription_id: ID de la souscription
        full_name: Nom complet
        passport_number: Numéro de passeport
        prime_ttc: Prime TTC (str car DB utilise text)
        coverage: Durée de couverture
        Autres champs du passeport (optionnels)

    Returns:
        Dictionnaire avec le résultat
    """
    try:
        logger.info(f"💾 Enregistrement détails VOYAGE pour souscription: {souscription_id}")

        from uuid import UUID
        from app.models.schemas import VoyageData

        voyage_data = VoyageData(
            full_name=full_name,
            passport_number=passport_number,
            nationality=nationality,
            date_of_birth=date_of_birth,
            place_of_birth=place_of_birth,
            sex=sex,
            profession=profession,
            issue_date=issue_date,
            expiry_date=expiry_date,
            place_of_issue=place_of_issue,
            country_code=country_code,
            type=type,
            prime_ttc=prime_ttc,
            coverage=coverage,
            documentUrl=document_url
        )

        success = await supabase_service.create_souscription_voyage(
            data=voyage_data,
            souscription_id=UUID(souscription_id)
        )

        if success:
            logger.info(f"✅ Détails VOYAGE enregistrés pour souscription: {souscription_id}")
            return {
                "success": True,
                "message": "Détails VOYAGE enregistrés avec succès!"
            }

        return {
            "success": False,
            "error": "Échec enregistrement détails VOYAGE"
        }

    except Exception as e:
        logger.error(f"❌ Erreur save_voyage_details: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@function_tool
async def save_iac_details(
    souscription_id: str,
    fullname: str,
    statutPro: str,
    secteurActivite: str,
    lieuTravail: str,
    prime_ttc: str,
    coverage: str,
    typeDocument: str,
    document_url: Optional[str] = None,
    extracted_infos_json: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enregistre les détails d'une souscription IAC dans souscription_iac.

    Args:
        souscription_id: ID de la souscription
        fullname: Nom complet
        statutPro: Statut professionnel
        secteurActivite: Secteur d'activité
        lieuTravail: Lieu de travail
        prime_ttc: Prime TTC (str)
        coverage: Période de couverture
        typeDocument: Type de document (Passeport, NIU, CNI)
        document_url: URL du document
        extracted_infos_json: Infos extraites du document en JSON string (optionnel)

    Returns:
        Dictionnaire avec le résultat
    """
    try:
        logger.info(f"💾 Enregistrement détails IAC pour souscription: {souscription_id}")

        from uuid import UUID
        from app.models.schemas import IACData
        import json

        # Parser le JSON des infos extraites si fourni
        extracted_infos = None
        if extracted_infos_json:
            extracted_infos = json.loads(extracted_infos_json) if isinstance(extracted_infos_json, str) else extracted_infos_json

        iac_data = IACData(
            fullname=fullname,
            statutPro=statutPro,
            secteurActivite=secteurActivite,
            lieuTravail=lieuTravail,
            prime_ttc=prime_ttc,
            coverage=coverage,
            typeDocument=typeDocument,
            documentUrl=document_url,
            extracted_infos=extracted_infos
        )

        success = await supabase_service.create_souscription_iac(
            data=iac_data,
            souscription_id=UUID(souscription_id)
        )

        if success:
            logger.info(f"✅ Détails IAC enregistrés pour souscription: {souscription_id}")
            return {
                "success": True,
                "message": "Détails IAC enregistrés avec succès!"
            }

        return {
            "success": False,
            "error": "Échec enregistrement détails IAC"
        }

    except Exception as e:
        logger.error(f"❌ Erreur save_iac_details: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@function_tool
async def save_mrh_details(
    souscription_id: str,
    fullname: str,
    forfaitMrh: str,
    prime_ttc: str,
    coverage: str,
    typeDocument: str,
    document_url: Optional[str] = None,
    extracted_infos_json: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enregistre les détails d'une souscription MRH dans souscription_mrh.

    Args:
        souscription_id: ID de la souscription
        fullname: Nom complet
        forfaitMrh: Forfait choisi
        prime_ttc: Prime TTC (str)
        coverage: Période de couverture
        typeDocument: Type de document
        document_url: URL du document
        extracted_infos_json: Infos extraites en JSON string (optionnel)

    Returns:
        Dictionnaire avec le résultat
    """
    try:
        logger.info(f"💾 Enregistrement détails MRH pour souscription: {souscription_id}")

        from uuid import UUID
        from app.models.schemas import MRHData
        import json

        # Parser le JSON des infos extraites si fourni
        extracted_infos = None
        if extracted_infos_json:
            extracted_infos = json.loads(extracted_infos_json) if isinstance(extracted_infos_json, str) else extracted_infos_json

        mrh_data = MRHData(
            fullname=fullname,
            forfaitMrh=forfaitMrh,
            prime_ttc=prime_ttc,
            coverage=coverage,
            typeDocument=typeDocument,
            documentUrl=document_url,
            extracted_infos=extracted_infos
        )

        success = await supabase_service.create_souscription_mrh(
            data=mrh_data,
            souscription_id=UUID(souscription_id)
        )

        if success:
            logger.info(f"✅ Détails MRH enregistrés pour souscription: {souscription_id}")
            return {
                "success": True,
                "message": "Détails MRH enregistrés avec succès!"
            }

        return {
            "success": False,
            "error": "Échec enregistrement détails MRH"
        }

    except Exception as e:
        logger.error(f"❌ Erreur save_mrh_details: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@function_tool
async def initiate_momo_payment(
    amount: float,
    phone_number: str,
    souscription_id: str,
    product_type: str
) -> Dict[str, Any]:
    """
    Initie un paiement MTN Mobile Money.

    Args:
        amount: Montant en FCFA
        phone_number: Numéro de téléphone du client
        souscription_id: ID de la souscription
        product_type: Type de produit (auto, voyage, etc.)

    Returns:
        Dictionnaire avec les détails du paiement initié
    """
    try:
        logger.info(f"💳 Initiation paiement MTN MoMo: {amount} FCFA pour {phone_number}")

        # Générer référence
        reference = mobile_money_service.generate_reference(souscription_id)

        # Formater numéro
        formatted_phone = mobile_money_service.format_phone_number(phone_number)

        # Créer requête
        payment_request = PaymentRequest(
            amount=amount,
            phone=formatted_phone,
            provider="momo",
            reference=reference,
            description=f"Assurance NSIA {product_type.upper()}"
        )

        # Initier paiement
        payment_response = await mobile_money_service.initiate_payment(payment_request)

        # Enregistrer transaction
        from uuid import UUID
        await supabase_service.create_transaction(
            souscription_id=UUID(souscription_id),
            amount=amount,
            reference=reference,
            payment_method="MTN_MOBILE_MONEY",
            status="en_attente"
        )

        logger.info(f"✅ Paiement MTN MoMo initié: {reference}")

        return {
            "success": True,
            "reference": reference,
            "amount": amount,
            "provider": "MTN Mobile Money",
            "phone": formatted_phone,
            "transaction_reference": payment_response.transaction_reference,
            "message": f"""✅ Paiement initié!

💰 Montant: {amount:,} FCFA
📱 Provider: MTN Mobile Money
🔑 Référence: {reference}

📲 Vous allez recevoir un message USSD sur {formatted_phone}
Composez votre code PIN pour valider le paiement."""
        }

    except Exception as e:
        logger.error(f"❌ Erreur initiation paiement MoMo: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Erreur lors de l'initiation du paiement MTN MoMo."
        }


@function_tool
async def initiate_airtel_payment(
    amount: float,
    phone_number: str,
    souscription_id: str,
    product_type: str
) -> Dict[str, Any]:
    """
    Initie un paiement Airtel Money.

    Args:
        amount: Montant en FCFA
        phone_number: Numéro de téléphone du client
        souscription_id: ID de la souscription
        product_type: Type de produit (auto, voyage, etc.)

    Returns:
        Dictionnaire avec les détails du paiement initié
    """
    try:
        logger.info(f"💳 Initiation paiement Airtel Money: {amount} FCFA pour {phone_number}")

        # Générer référence
        reference = mobile_money_service.generate_reference(souscription_id)

        # Formater numéro
        formatted_phone = mobile_money_service.format_phone_number(phone_number)

        # Créer requête
        payment_request = PaymentRequest(
            amount=amount,
            phone=formatted_phone,
            provider="airtel",
            reference=reference,
            description=f"Assurance NSIA {product_type.upper()}"
        )

        # Initier paiement
        payment_response = await mobile_money_service.initiate_payment(payment_request)

        # Enregistrer transaction
        from uuid import UUID
        await supabase_service.create_transaction(
            souscription_id=UUID(souscription_id),
            amount=amount,
            reference=reference,
            payment_method="AIRTEL_MOBILE_MONEY",
            status="en_attente"
        )

        logger.info(f"✅ Paiement Airtel Money initié: {reference}")

        return {
            "success": True,
            "reference": reference,
            "amount": amount,
            "provider": "Airtel Money",
            "phone": formatted_phone,
            "transaction_reference": payment_response.transaction_reference,
            "message": f"""✅ Paiement initié!

💰 Montant: {amount:,} FCFA
📱 Provider: Airtel Money
🔑 Référence: {reference}

📲 Vous allez recevoir un message USSD sur {formatted_phone}
Composez votre code PIN pour valider le paiement."""
        }

    except Exception as e:
        logger.error(f"❌ Erreur initiation paiement Airtel: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Erreur lors de l'initiation du paiement Airtel Money."
        }


# ============================================================================
# HELPER FUNCTIONS - Fonctions internes
# ============================================================================

async def _generate_proposal_internal(
    souscription_id: str,
    client_name: str,
    phone: str,
    product_type: str,
    amount: float,
    reference: str,
    is_paid: bool = False
) -> Dict[str, Any]:
    """
    Fonction interne pour générer une proposition d'assurance.
    Utilisée par initiate_pay_on_delivery et initiate_pay_on_agency.
    """
    try:
        from app.tools.receipts import generate_product_receipt_pdf
        import os

        logger.info(f"📄 Génération proposition pour {client_name}")

        # Nom du fichier temporaire
        filename = f"/tmp/proposition_{souscription_id}.pdf"

        # Générer la proposition
        success = generate_product_receipt_pdf(
            output_filename=filename,
            nom_complet=client_name,
            telephone=phone,
            ville="N/A",
            product_type=product_type,
            prime_a_payer_ttc=str(amount),
            receipt_number=reference,
            template_path="product_proposal.txt" if not is_paid else "paid_product_receipt.txt",
            product_name=product_type
        )

        if not success or not os.path.exists(filename):
            return {
                "success": False,
                "error": "Génération échouée"
            }

        # Upload vers Supabase Storage
        with open(filename, "rb") as f:
            pdf_data = f.read()

        file_path = f"proposals/{souscription_id}.pdf"
        pdf_url = await supabase_service.upload_file("receipts", file_path, pdf_data)

        # Supprimer le fichier temporaire
        if os.path.exists(filename):
            os.remove(filename)

        # Sauvegarder dans documents
        from app.models.schemas import DocumentUpload
        from uuid import UUID
        await supabase_service.save_document(
            DocumentUpload(
                souscription_id=UUID(souscription_id),
                document_url=pdf_url,
                type="proposition",
                nom=f"Proposition_{souscription_id}.pdf"
            )
        )

        logger.info(f"✅ Proposition générée: {pdf_url}")

        return {
            "success": True,
            "pdf_url": pdf_url,
            "message": "Proposition générée avec succès"
        }

    except Exception as e:
        logger.error(f"❌ Erreur génération proposition: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@function_tool
async def generate_insurance_proposal(
    souscription_id: str,
    client_name: str,
    phone: str,
    product_type: str,
    amount: float,
    reference: str,
    is_paid: bool = False
) -> Dict[str, Any]:
    """
    Génère une proposition d'assurance (document non-payé).

    Args:
        souscription_id: ID de la souscription
        client_name: Nom du client
        phone: Téléphone du client
        product_type: Type de produit
        amount: Montant
        reference: Référence de transaction
        is_paid: False pour proposition, True pour reçu final

    Returns:
        URL du PDF généré
    """
    return await _generate_proposal_internal(
        souscription_id=souscription_id,
        client_name=client_name,
        phone=phone,
        product_type=product_type,
        amount=amount,
        reference=reference,
        is_paid=is_paid
    )


@function_tool
async def initiate_pay_on_delivery(
    amount: float,
    souscription_id: str,
    product_type: str,
    client_name: str,
    client_phone: str
) -> Dict[str, Any]:
    """
    Enregistre un paiement à la livraison (PAY_ON_DELIVERY).

    Ce mode de paiement ne nécessite pas de paiement en ligne.
    La proposition d'assurance est envoyée immédiatement et le paiement
    sera effectué lors de la livraison du document.

    Args:
        amount: Montant en FCFA
        souscription_id: ID de la souscription
        product_type: Type de produit (auto, voyage, etc.)
        client_name: Nom du client
        client_phone: Téléphone du client

    Returns:
        Dictionnaire avec les détails du paiement et URL de la proposition
    """
    try:
        logger.info(f"📦 Initiation paiement à la livraison pour {client_name}")

        # Appeler le service Mobile Money pour traiter le paiement à la livraison
        from app.services.mobile_money import mobile_money_service

        result = await mobile_money_service.process_pay_on_delivery(
            souscription_id=souscription_id,
            client_name=client_name,
            client_phone=client_phone,
            product_type=product_type,
            amount=amount
        )

        return result

    except Exception as e:
        logger.error(f"❌ Erreur paiement à la livraison: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "message": "Erreur lors de l'enregistrement du paiement à la livraison."
        }


@function_tool
async def initiate_pay_on_agency(
    amount: float,
    souscription_id: str,
    product_type: str,
    client_name: str,
    client_phone: str
) -> Dict[str, Any]:
    """
    Enregistre un paiement en agence (PAY_ON_AGENCY).

    Ce mode de paiement ne nécessite pas de paiement en ligne.
    La proposition d'assurance est envoyée immédiatement et le paiement
    sera effectué directement en agence NSIA.

    Args:
        amount: Montant en FCFA
        souscription_id: ID de la souscription
        product_type: Type de produit (auto, voyage, etc.)
        client_name: Nom du client
        client_phone: Téléphone du client

    Returns:
        Dictionnaire avec les détails du paiement et URL de la proposition
    """
    try:
        logger.info(f"🏢 Initiation paiement en agence pour {client_name}")

        # Appeler le service Mobile Money pour traiter le paiement en agence
        from app.services.mobile_money import mobile_money_service

        result = await mobile_money_service.process_pay_on_agency(
            souscription_id=souscription_id,
            client_name=client_name,
            client_phone=client_phone,
            product_type=product_type,
            amount=amount
        )

        return result

    except Exception as e:
        logger.error(f"❌ Erreur paiement en agence: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "message": "Erreur lors de l'enregistrement du paiement en agence."
        }


# ============================================================================
# Liste des outils disponibles
# ============================================================================

ALL_AGENT_TOOLS = [
    # Vision tools
    analyze_carte_grise,
    analyze_passport,
    analyze_cni,
    analyze_niu,

    # Quotation tools
    calculate_auto_quotation,
    calculate_voyage_quotation,
    calculate_iac_quotation,
    calculate_mrh_quotation,

    # Database tools
    get_or_create_client,
    create_souscription,

    # Product-specific details tools
    save_auto_details,
    save_voyage_details,
    save_iac_details,
    save_mrh_details,

    # Payment tools
    initiate_momo_payment,
    initiate_airtel_payment,
    initiate_pay_on_delivery,
    initiate_pay_on_agency,
]
