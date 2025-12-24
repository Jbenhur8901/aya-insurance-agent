import os
import segno
from datetime import datetime
from weasyprint import HTML
import logging
import io
import base64
import uuid


# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Chemins relatifs depuis la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Racine du projet
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

def generate_qr_base64(data: str) -> str:
    """
    Génère un QR code à partir d'une chaîne et le retourne en base64 (format PNG).
    """
    try:
        # Créer le QR code
        qr = segno.make_qr(data)
        
        # Sauvegarder dans un buffer mémoire
        buffer = io.BytesIO()
        qr.save(buffer, kind='png', scale=10)
        buffer.seek(0)
        
        # Encoder en base64
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{base64_image}"
    
    except Exception as e:
        logging.error(f"Erreur génération QR code: {e}")


def generate_auto_receipt_pdf(
    output_filename: str,
    # Informations client
    nom_complet: str,
    telephone: str,
    ville: str,
    # Informations véhicule
    vehicule_categorie: str,
    vehicule_brand: str,
    immatriculation: str,
    # Composantes de la prime (détaillées)
    rc: str,
    sr_ic: str = None,  # Pour CAT 1-3 (Sécurité Routière / Incendie Collision)
    ind_chauf: str = None,  # Pour CAT 4 (Indemnité Chauffeur)
    gestion_pool: str = None,  # Pour CAT 4 uniquement
    police: str = "10000",
    taxes: str = None,
    timbre: str = "5000",
    carte_rose: str = "1500",
    total_amount: str = None,
    # Métadonnées
    categorie: int = None,  # 1, 2, 3 ou 4
    couverture: str = None,
    promo_code: str = None,
    receipt_number: str = None,
    generation_date: str = None,
    template_path: str = "paid_auto_receipt.html",
    is_paid: bool = True,
) -> bool:
    """
    Génère un reçu NSIA AUTO en PDF avec adaptation dynamique selon la catégorie
    
    Args:
        output_filename (str): Nom du fichier PDF de sortie
        
        # Informations client (obligatoires)
        nom_complet (str): Nom complet du client
        telephone (str): Numéro de téléphone
        ville (str): Ville du client
        
        # Informations véhicule (obligatoires)
        vehicule_categorie (str): Catégorie du véhicule
        vehicule_brand (str): Marque et modèle du véhicule
        immatriculation (str): Numéro d'immatriculation
        
        # Composantes de la prime (obligatoires selon catégorie)
        rc (str): Responsabilité Civile
        sr_ic (str): Sécurité Routière (CAT 1) ou Incendie/Collision (CAT 2-3)
        ind_chauf (str): Indemnité Chauffeur (CAT 4 uniquement)
        gestion_pool (str): Gestion Pool (CAT 4 uniquement)
        police (str): Frais de police (défaut: 10000)
        taxes (str): Taxes
        timbre (str): Timbre (défaut: 5000)
        carte_rose (str): Carte rose (défaut: 1500)
        total_amount (str): Total à payer
        
        # Métadonnées
        categorie (int): Catégorie du véhicule (1-4)
        couverture (str): Période de couverture
        promo_code (str): Code promo appliqué
        receipt_number (str): Numéro de reçu
        generation_date (str): Date de génération
        template_path (str): Nom du template (paid_auto_receipt.html ou proposition_auto_receipt.html)
        is_paid (bool): True pour reçu payé, False pour proposition
    
    Returns:
        bool: True si succès, False sinon
    
    Example CAT 1-3:
        generate_auto_receipt_pdf(
            output_filename="recu_auto_cat1.pdf",
            nom_complet="MBEMBA Pierre",
            telephone="+242 066 12 34 56",
            ville="Brazzaville",
            vehicule_categorie="CAT 1 - Promenade/Affaires",
            vehicule_brand="TOYOTA Corolla",
            immatriculation="CG-123-AB",
            rc="49204",
            sr_ic="19671",
            police="10000",
            taxes="11831",
            timbre="5000",
            carte_rose="1500",
            total_amount="97206",
            categorie=1,
            couverture="12 mois"
        )
    
    Example CAT 4:
        generate_auto_receipt_pdf(
            output_filename="recu_auto_cat4.pdf",
            nom_complet="KONGO Jean",
            telephone="+242 066 11 22 33",
            ville="Pointe-Noire",
            vehicule_categorie="CAT 4 - Transport Public de Voyageurs",
            vehicule_brand="TAXI - TOYOTA Corolla",
            immatriculation="CG-456-CD",
            rc="228716",
            ind_chauf="26100",
            gestion_pool="12740",
            police="10000",
            taxes="41633",
            timbre="5000",
            carte_rose="1500",
            total_amount="325689",
            categorie=4,
            couverture="12 mois"
        )
    """
    
    try:
        # Génération des valeurs par défaut
        if not receipt_number:
            receipt_number = f"NSIA-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        if not generation_date:
            generation_date = datetime.now().strftime("%d/%m/%Y - %H:%M")
        
        # Génération du code-barres et référence
        barcode_base64 = generate_qr_base64(receipt_number)
        reference_number = f"{receipt_number.replace('-', '')}{telephone.replace(' ', '').replace('+', '')[-6:]}"
        
        # Gestion du logo
        logo_path = "https://phwyhgzcnnjffovepbrt.supabase.co/storage/v1/object/public/file/Logo%20NSIA%20Assurances.png"
        logo_section = f'<img src="{logo_path}" alt="NSIA Logo" style="max-width: 150px; max-height: 80px;">'
        
        # Section promo conditionnelle
        promo_section = ""
        if promo_code:
            promo_section = f'''
            <div class="promo-section" style="background-color: #e8f5e9; padding: 10px; margin: 10px 0; border-left: 3px solid #4caf50;">
                <div style="color: #2e7d32; font-weight: 600;">✓ CODE PROMO APPLIQUÉ: {promo_code}</div>
                <div style="font-size: 10px; margin-top: 5px; color: #666;">Réduction appliquée sur votre prime</div>
            </div>
            '''
        
        # Construction dynamique des lignes selon la catégorie
        sr_ic_row = ""
        gestion_pool_row = ""
        
        if categorie == 4:
            # Pour CAT 4: Indemnité Chauffeur + Gestion Pool
            if ind_chauf:
                sr_ic_row = f'''
                    <tr>
                        <td class="label">Indemnité Chauffeur</td>
                        <td class="amount">{ind_chauf} FCFA</td>
                    </tr>
                '''
            if gestion_pool:
                gestion_pool_row = f'''
                    <tr>
                        <td class="label">Gestion Pool (5%)</td>
                        <td class="amount">{gestion_pool} FCFA</td>
                    </tr>
                '''
        else:
            # Pour CAT 1-3: Sécurité Routière ou Incendie/Collision
            if sr_ic:
                label = "Sécurité Routière (SR)" if categorie == 1 else "Incendie et Collision (IC)"
                sr_ic_row = f'''
                    <tr>
                        <td class="label">{label}</td>
                        <td class="amount">{sr_ic} FCFA</td>
                    </tr>
                '''
        
        # Chargement du template
        template_full_path = os.path.join(TEMPLATES_DIR, template_path)
        if not os.path.exists(template_full_path):
            raise FileNotFoundError(f"Template non trouvé: {template_full_path}")
        
        with open(template_full_path, "r", encoding="utf-8") as file:
            html_template = file.read()
        
        # Formatage du template
        html_content = html_template.format(
            # Sections générées
            logo_section=logo_section,
            promo_section=promo_section,
            sr_ic_row=sr_ic_row,
            gestion_pool_row=gestion_pool_row,
            barcode_base64=barcode_base64,
            reference_number=reference_number,
            
            # Informations générales
            receipt_number=receipt_number,
            generation_date=generation_date,
            couverture=couverture or "Non spécifiée",
            
            # Informations client
            nom_complet=nom_complet,
            telephone=telephone,
            ville=ville,
            
            # Informations véhicule
            vehicule_categorie=vehicule_categorie,
            vehicule_brand=vehicule_brand,
            immatriculation=immatriculation,
            
            # Composantes de la prime
            rc=rc,
            police=police,
            taxes=taxes,
            timbre=timbre,
            carte_rose=carte_rose,
            total_amount=total_amount
        )
        
        # Génération du PDF
        HTML(string=html_content).write_pdf(target=output_filename)
        logging.info(f"Reçu NSIA AUTO généré avec succès: {output_filename}")
        return True
        
    except FileNotFoundError as e:
        logging.error(f"Fichier non trouvé: {e}")
        return False
    except Exception as e:
        logging.error(f"Erreur génération reçu NSIA AUTO: {e}")
        raise e


# Fonction helper pour générer depuis les données de tarification
def generate_receipt_from_pricing(
    output_filename: str,
    pricing_data: dict,
    periode: str,  # "3M", "6M" ou "12M"
    nom_complet: str,
    telephone: str,
    ville: str,
    vehicule_brand: str,
    immatriculation: str,
    promo_code: str = None,
    receipt_number = None,
    is_paid: bool = True
) -> bool:
    """
    Génère un reçu à partir des données de tarification (sortie de ttc_auto ou ttc_auto_cat4)
    
    Args:
        output_filename (str): Nom du fichier PDF
        pricing_data (dict): Données retournées par ttc_auto() ou ttc_auto_cat4()
        periode (str): "3M", "6M" ou "12M"
        nom_complet (str): Nom du client
        telephone (str): Téléphone du client
        ville (str): Ville du client
        vehicule_brand (str): Marque du véhicule
        immatriculation (str): Immatriculation
        promo_code (str): Code promo éventuel
        is_paid (bool): True pour reçu payé, False pour proposition
    
    Returns:
        bool: True si succès
    
    Example:
        # Après avoir appelé ttc_auto_cat4()
        pricing = ttc_auto_cat4(power=7, energy="ESSENCE", modele="TAXI", place=4)
        
        generate_receipt_from_pricing(
            output_filename="recu_taxi.pdf",
            pricing_data=pricing,
            periode="12M",
            nom_complet="Jean KONGO",
            telephone="+242 066 11 22 33",
            ville="Brazzaville",
            vehicule_brand="TAXI - TOYOTA Corolla",
            immatriculation="CG-789-EF"
        )
    """
    
    # Extraction des informations
    info = pricing_data.get("INFORMATIONS", {})
    categorie = info.get("CATEGORIE", 1)
    
    # Mapping de la période vers la clé d'offre
    periode_mapping = {
        "3M": ("OFFRE_3_MOIS", "3 mois"),
        "6M": ("OFFRE_6_MOIS", "6 mois"),
        "12M": ("OFFRE_12_MOIS", "12 mois"),
        "3_MOIS": ("OFFRE_3_MOIS", "3 mois"),
        "6_MOIS": ("OFFRE_6_MOIS", "6 mois"),
        "12_MOIS": ("OFFRE_12_MOIS", "12 mois")
    }
    
    # Sélection de l'offre
    if periode not in periode_mapping:
        raise ValueError(f"Période invalide: {periode}. Utilisez '3M', '6M', '12M' ou '3_MOIS', '6_MOIS', '12_MOIS'")
    
    offre_key, couverture = periode_mapping[periode]
    
    if offre_key not in pricing_data:
        raise ValueError(f"Offre '{offre_key}' non trouvée dans les données de tarification")
    
    offre = pricing_data[offre_key]
    
    # Construction de la description de catégorie
    usage = info.get("USAGE", "")
    modele = info.get("MODELE", "")
    vehicule_categorie = f"CAT {categorie} - {usage}"
    
    # Template selon si c'est payé ou proposition
    template = "paid_auto_receipt.txt" if is_paid else "auto_proposal.txt"
    
    # Appel de la fonction principale
    if categorie == 4:
        # CAT 4: avec IND_CHAUF et GESTION_POOL
        return generate_auto_receipt_pdf(
            output_filename=output_filename,
            nom_complet=nom_complet,
            telephone=telephone,
            ville=ville,
            vehicule_categorie=vehicule_categorie,
            vehicule_brand=vehicule_brand,
            immatriculation=immatriculation,
            rc=str(offre["RC"]),
            ind_chauf=str(offre["IND_CHAUF"]),
            gestion_pool=str(offre["GESTION_POOL"]),
            police=str(offre["POLICE"]),
            taxes=str(offre["TAXES"]),
            timbre=str(offre["TIMBRE"]),
            carte_rose=str(offre["CARTE_ROSE"]),
            total_amount=str(offre["PRIME_TOTALE"]),
            categorie=categorie,
            couverture=couverture,
            promo_code=promo_code,
            template_path=template,
            receipt_number=receipt_number,
            is_paid=is_paid
        )
    else:
        # CAT 1-3: avec SR_IC
        return generate_auto_receipt_pdf(
            output_filename=output_filename,
            nom_complet=nom_complet,
            telephone=telephone,
            ville=ville,
            vehicule_categorie=vehicule_categorie,
            vehicule_brand=vehicule_brand,
            immatriculation=immatriculation,
            rc=str(offre["RC"]),
            sr_ic=str(offre["SR_IC"]),
            police=str(offre["POLICE"]),
            taxes=str(offre["TAXES"]),
            timbre=str(offre["TIMBRE"]),
            carte_rose=str(offre["CARTE_ROSE"]),
            total_amount=str(offre["PRIME_TOTALE"]),
            categorie=categorie,
            couverture=couverture,
            promo_code=promo_code,
            template_path=template,
            receipt_number=receipt_number,
            is_paid=is_paid
        )

def generate_product_receipt_pdf(
    output_filename: str,
    # Informations client
    nom_complet: str,
    telephone: str,
    ville: str,
    # Informations produit
    product_type: str,
    prime_a_payer_ttc: str,
    # Paramètres optionnels
    promo_code: str = None,
    receipt_number: str = None,
    generation_date: str = None,
    couverture: str = None,
    template_path: str = "paid_product_receipt.txt",
    product_name : str = "test"
) -> bool:
    """
    Génère un reçu ou proposition MRH en PDF (version simple, pas de logique PAYÉ)
    """
    try:
        from datetime import datetime
        import os, logging
        from weasyprint import HTML
        import uuid

        # Génération des valeurs par défaut si non fournies
        if not receipt_number:
            receipt_number = f"NSIA-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"
        if not generation_date:
            generation_date = datetime.now().strftime("%d/%m/%Y - %H:%M")


        # Génération du code-barres et référence
        barcode_base64 = generate_qr_base64(receipt_number)
        reference_number = f"{receipt_number.replace('-', '')}{telephone.replace(' ', '').replace('+', '')[-6:]}"

        # Gestion du logo
        logo_path = "https://phwyhgzcnnjffovepbrt.supabase.co/storage/v1/object/public/file/Logo%20NSIA%20Assurances.png"
        logo_section = '<div class="logo-space">LOGO NSIA</div>'
        logo_section = f'<img src="{logo_path}" alt="NSIA Logo" style="max-width: 150px; max-height: 80px;">'


        # Section promo conditionnelle
        promo_section = ""
        if promo_code:
            promo_section = f'''
            <div class="promo-section">
                <div class="promo-code">CODE PROMO APPLIQUÉ: {promo_code}</div>
                <div style="font-size: 10px; margin-top: 5px;">Réduction appliquée</div>
            </div>
            '''
            print('promo added')

        template_full_path = os.path.join(TEMPLATES_DIR, template_path)
        # Chargement du template HTML
        template_path = template_full_path
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template non trouvé: {template_path}")
        with open(template_path, "r", encoding="utf-8") as file:
            html_template = file.read()

        # Formatage du template avec tous les paramètres
        html_content = html_template.format(
            logo_section=logo_section,
            promo_section=promo_section,
            barcode_base64=barcode_base64,
            reference_number=reference_number,
            receipt_number=receipt_number,
            generation_date=generation_date,
            couverture=couverture,
            nom_complet=nom_complet,
            telephone=telephone,
            ville=ville,
            product_type=product_type,
            prime_a_payer_ttc=prime_a_payer_ttc,
            product_name=product_name
        )

        # Génération du PDF
        HTML(string=html_content).write_pdf(target=output_filename)
        logging.info(f"Reçu {product_name} généré avec succès: {output_filename}")
        return True

    except FileNotFoundError as e:
        logging.error(f"Fichier non trouvé: {e}")
        return False
    except Exception as e:
        raise e
    

