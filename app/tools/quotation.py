import pandas as pd
from pydantic import BaseModel, Field
import os
import logging
from dotenv import load_dotenv
import pandas as pd
from openai import OpenAI
import google.generativeai as genai
from google.generativeai import types
import requests
import json 


load_dotenv()

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

VISION_INSTRUCTION = """Tu es l'agent Vision en charge d'analyser les images que les utilisateurs te donnent pour extraire
            les informations pertinentes des cartes grises comme nombre de chaises, puissance et modèle de véhicule.Si l'image
            n'est pas une carte grise, prière de demander à l'utilisateur de t'en fournir. """

# Chemins relatifs depuis la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Racine du projet
DATA_DIR = os.path.join(BASE_DIR, "data")

db = pd.read_excel(os.path.join(DATA_DIR, "tarification_nsia_auto.xlsx"), sheet_name=None)

# ============================================================================
# Modèles VISON
# ============================================================================


class Formater(BaseModel):
    """Always use this tool to structure your response to the user."""
    content : str = Field(description="The answer to the user's input")
    next_agent : str = Field(description="which agent to call next, '__end__' if supervisor reply")

    def __getitem__(self, key: str):
        """Make the Formater class subscriptable."""
        if key in self.__dict__:
            return self.__dict__[key]
        raise KeyError(f"Key '{key}' not found in Formater")
    
class Grey_card(BaseModel):

    fullname : str = Field(description="Full name of cardholder, if not present return N/A")
    immatriculation : str = Field(description="The car's registration number, if not present return N/A")
    power : str = Field(description="Engine power of the vehicle sometimes written as 'Puissance Administrative', if not present return N/A") # mandatory
    seat_number : str = Field(description="Total number of seats in the car, if not present return N/A") # mandatory
    fuel_type : str = Field(description="Type of Fuel of the vehicule, if not present return N/A") # necessary
    brand : str = Field(description="Brand of the car, if not present return N/A") # mandatory
    chassis_number : str = Field(description = "Car's chassis number or Vehicle Identification Number,if not present return N/A ")
    phone : str = Field(description="phone number on the paper, if not present return N/A")
    model : str = Field(description="Car's model, if not present return N/A")
    address : str = Field(description="address of the cardholder, if not present return N/A")
    profession : str = Field(description = "Profession of the cardholder, if not present return N/A")
    content : str = Field(description="'Informations extraites avec succès' if the image is a grey card , if not grey card return 'S'il vous plait envoyer l'image d'une carte grise'")

class PassportInfo(BaseModel):
    full_name: str = Field(description="Full name of the passport holder (surname and given names), if not present return N/A")
    passport_number: str = Field(description="Passport number, if not present return N/A")
    nationality: str = Field(description="Nationality of the holder, if not present return N/A")
    date_of_birth: str = Field(description="Date of birth in DD MMM/YYY format, if not present return N/A")
    place_of_birth: str = Field(description="Place of birth, if not present return N/A")
    sex: str = Field(description="Gender (M or F), if not present return N/A")
    profession: str = Field(description="Profession of the passport holder, if not present return N/A")
    issue_date: str = Field(description="Date of passport issuance, if not present return N/A")
    expiry_date: str = Field(description="Date of passport expiry, if not present return N/A")
    place_of_issue: str = Field(description="Location where the passport was issued, if not present return N/A")
    country_code: str = Field(description="Three-letter country code, if not present return N/A")
    type: str = Field(description="Passport type (usually 'P'), if not present return N/A")
    content: str = Field(description="'Informations extraites avec succès' if the image is a passport, otherwise 'S'il vous plaît envoyer l'image d'un passeport'")

class NIUInfo(BaseModel):
    """Modèle pour l'extraction des informations du NIU (Numéro d'Identification Unique) congolais"""
    full_name: str = Field(description="Nom complet du titulaire, if not present return N/A")
    niu_number: str = Field(description="Numéro d'Identification Unique (NIU), if not present return N/A")
    date_of_birth: str = Field(description="Date de naissance, if not present return N/A")
    place_of_birth: str = Field(description="Lieu de naissance, if not present return N/A")
    sex: str = Field(description="Sexe (M ou F), if not present return N/A")
    nationality: str = Field(description="Nationalité, if not present return N/A")
    address: str = Field(description="Adresse du titulaire, if not present return N/A")
    profession: str = Field(description="Profession du titulaire, if not present return N/A")
    issue_date: str = Field(description="Date de délivrance, if not present return N/A")
    expiry_date: str = Field(description="Date d'expiration, if not present return N/A")
    issuing_authority: str = Field(description="Autorité de délivrance, if not present return N/A")
    content: str = Field(description="'Informations extraites avec succès' if the image is a NIU, otherwise 'S'il vous plaît envoyer l'image d'un NIU'")

class CNIInfo(BaseModel):
    """Modèle pour l'extraction des informations de la Carte Nationale d'Identité (CNI)"""
    full_name: str = Field(description="Nom complet du titulaire, if not present return N/A")
    cni_number: str = Field(description="Numéro de la carte nationale d'identité, if not present return N/A")
    date_of_birth: str = Field(description="Date de naissance, if not present return N/A")
    place_of_birth: str = Field(description="Lieu de naissance, if not present return N/A")
    sex: str = Field(description="Sexe (M ou F), if not present return N/A")
    nationality: str = Field(description="Nationalité, if not present return N/A")
    address: str = Field(description="Adresse du titulaire, if not present return N/A")
    father_name: str = Field(description="Nom du père, if not present return N/A")
    mother_name: str = Field(description="Nom de la mère, if not present return N/A")
    height: str = Field(description="Taille du titulaire, if not present return N/A")
    profession: str = Field(description="Profession du titulaire, if not present return N/A")
    issue_date: str = Field(description="Date de délivrance, if not present return N/A")
    expiry_date: str = Field(description="Date d'expiration, if not present return N/A")
    issuing_authority: str = Field(description="Autorité de délivrance, if not present return N/A")
    content: str = Field(description="'Informations extraites avec succès' if the image is a CNI, otherwise 'S'il vous plaît envoyer l'image d'une CNI'")

def image_processor(image_path: str, 
                    vision_model : str = "gemini-2.0-flash-exp", 
                    vision_instruction = None, 
                    response_schema : BaseModel = Grey_card) -> dict:
    """
    Analyse une image pour extraire les informations de la carte grise.
    """
    
    try:

        if vision_model.startswith("gpt") :

        # --- Traitement avec OpenAI (gpt-4o ou gpt-4o-mini) --- 
            client = OpenAI()
            response = client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "developer", "content": vision_instruction},
                    {"role": "user", "content": [{"type": "image_url", "image_url": {"url": image_path}}]}
                    ],
                    response_format=response_schema
                    )
            return json.loads(response.choices[0].message.content)
            
        elif vision_model.startswith("gem"):

            # --- Traitement avec Gemini ---

            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            image_bytes = requests.get(image_path).content
            image = types.Part.from_bytes(
                data=image_bytes, mime_type="image/jpeg"
                )                
            response = client.models.generate_content(
                model=vision_model,
                contents=[vision_instruction, image],
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': response_schema
                    }
                    )
            return json.loads(response.text)
            
        else : 
            raise ValueError(f"Modèle non reconnu pour l'analyse d'image : {vision_model}")
                       
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'analyse de l'image : {str(e)}")


# ============================================================================
# Modèles Quotations
# ============================================================================

def transform(db : dict, sheetname: str = None) -> pd.DataFrame:
    """
    Transforms a DataFrame by consolidating 'PUISSANCE' and 'PLACE' ranges
    into single IntervalIndex columns, then removes the original boundary columns.

    Args:
        db (dict): A dictionary mapping sheet names (str) to pandas DataFrames.
        sheetname (str): The name of the DataFrame within `db` to transform.
    Returns:
        pandas.DataFrame: A new DataFrame with 'PUISSANCE' and 'PLACE' as
                          IntervalIndex columns, and boundary columns dropped.
    """
    
    

    df = db[sheetname].copy()

    df["PUISSANCE"] = pd.IntervalIndex.from_arrays(df["PUISSANCE_BORNE_A"], df["PUISSANCE_BORNE_B"], closed="both")
    df["PLACE"] = pd.IntervalIndex.from_arrays(df["PLACE_BORNE_A"], df["PLACE_BORNE_B"], closed="both")

    # Drop original boundary columns
    return df.drop(["PLACE_BORNE_A", "PLACE_BORNE_B", "PUISSANCE_BORNE_A", "PUISSANCE_BORNE_B"], axis=1)

def transform_2(df : pd.DataFrame) -> pd.DataFrame:
    """
    Transforms a DataFrame by consolidating 'Duree' ranges
    into single IntervalIndex column, then removes the original boundary columns.

    Args:
        df (pd.DataFrame): the DataFrame to transform.

    Returns:
        pandas.DataFrame: A new DataFrame with 'Duree' as
                          IntervalIndex columns, and boundary columns dropped.
    """
    transform_df = df.copy() 

    transform_df["Duree"] = pd.IntervalIndex.from_arrays(transform_df["Duree_Borne_A"], transform_df["Duree_Borne_B"], closed="right")

    # Drop original boundary columns
    return transform_df.drop(["Duree_Borne_A", "Duree_Borne_B"], axis=1)

def voyage_api(client: str, zone : str, product: str, duration : int) -> int:

    df = pd.read_csv(os.path.join(DATA_DIR, "voyage.csv"))
    t_df = transform_2(df)
    # Base conditions
    condition = (
        (t_df["Client"] == client) &
        (t_df["Zone"] == zone) &
        (t_df["Product"] == product) &
        (t_df["Duree"].apply(lambda x: duration in x))
    )
    
    try :
        result = t_df.loc[condition]
        return int(result["Tarif_TTC"].iloc[0])
    
    except Exception as e:
        return 0

def ttcAuto_all(power: int, 
             energy: str,
             place: int,
             modele: str = "VOITURE",
             tarif_type : str = "NORMAL",
             usage: str = "PROMENADE/AFFAIRES") -> dict:
    """
    Filters a DataFrame for a specific row and returns detailed pricing breakdown for 3, 6, and 12 months offers.
    
    Args:
        power (int): Power value within 'PUISSANCE_BORNE_A' to 'PUISSANCE_BORNE_B' interval.
        energy (str): Energy type (ESSENCE or DIESEL).
        modele (str): Vehicle model (TAXI, PICNIC, MINI-BUS, COASTER).
        place (int): Place value within 'PLACE_BORNE_A' to 'PLACE_BORNE_B' interval.
        usage (str): Vehicle usage type (default: "TRANSPORT_PUBLIC_VOYAGEURS").
    
    Returns:
        dict: Dictionary containing detailed pricing breakdown for each period (3M, 6M, 12M).
    """

    df = transform(db,"mass_market_allcat")
    
    # Base conditions
    condition = (
        (df["USAGE"] == usage) &
        (df["MODELE"] == modele) &
        (df["ENERGY"] == energy) &
        (df["TARIF_TYPE"] == tarif_type) &
        (df["PUISSANCE"].apply(lambda x: power in x)) &
        (df["PLACE"].apply(lambda x: place in x))
    )

    result = df.loc[condition]
    
    if result.empty:
        raise ValueError(f"No matching tariff found for: usage={usage}, modele={modele}, "
                        f"energy={energy}, power={power}, place={place}")
    
    # Extract row as series for easier access
    row = result.iloc[0]
    
    # Build detailed pricing breakdown
    pricing = {
        "OFFRE_3_MOIS": {
            "RC": int(round(row["RC_3M"])),
            "SR_IC": int(round(row["SR_IC_3M"])),
            "POLICE": int(round(row["POLICE"])),
            "TAXES": int(round(row["TAXES_3M"])),
            "CARTE_ROSE": int(round(row["CARTE_ROSE"])),
            "TIMBRE": int(round(row["TIMBRE"])),
            "PRIME_TOTALE": int(round(row["PRIME_3M"]))
        },
        "OFFRE_6_MOIS": {
            "RC": int(round(row["RC_6M"])),
            "SR_IC": int(round(row["SR_IC_6M"])),
            "POLICE": int(round(row["POLICE"])),
            "TAXES": int(round(row["TAXES_6M"])),
            "CARTE_ROSE": int(round(row["CARTE_ROSE"])),
            "TIMBRE": int(round(row["TIMBRE"])),
            "PRIME_TOTALE": int(round(row["PRIME_6M"]))
        },
        "OFFRE_12_MOIS": {
            "RC": int(round(row["RC_12M"])),
            "SR_IC": int(round(row["SR_IC_12M"])),
            "POLICE": int(round(row["POLICE"])),
            "TAXES": int(round(row["TAXES_12M"])),
            "CARTE_ROSE": int(round(row["CARTE_ROSE"])),
            "TIMBRE": int(round(row["TIMBRE"])),
            "PRIME_TOTALE": int(round(row["PRIME_12M"]))
        },
        "INFORMATIONS": {
            "USAGE": row["USAGE"],
            "MODELE": row["MODELE"],
            "CATEGORIE": int(row["CATEGORIE"]),
            "TARIF_TYPE": row["TARIF_TYPE"],
            "ENERGY": row["ENERGY"],
            "PLACE": f"{place}",
            "PUISSANCE": f"{power}"
        }
    }
    
    return pricing

def ttc_auto_cat4(power: int, 
                  energy: str,
                  modele: str, 
                  place: int,
                  usage: str = "TRANSPORT PUBLIC VOYAGEURS") -> dict:
    """
    Filters a DataFrame for CAT 4 vehicles and returns detailed pricing breakdown for 3, 6, and 12 months offers.
    
    Args:
        power (int): Power value within 'PUISSANCE_BORNE_A' to 'PUISSANCE_BORNE_B' interval.
        energy (str): Energy type (ESSENCE or DIESEL).
        modele (str): Vehicle model (TAXI, PICNIC, MINI-BUS, COASTER).
        place (int): Place value within 'PLACE_BORNE_A' to 'PLACE_BORNE_B' interval.
        usage (str): Vehicle usage type (default: "TRANSPORT_PUBLIC_VOYAGEURS").
    
    Returns:
        dict: Dictionary containing detailed pricing breakdown for each period (3M, 6M, 12M) including GESTION_POOL and IND_CHAUF.
    """
    df =  transform(db,"mass_market_cat4")
    
    # Base conditions
    condition = (
        (df["USAGE"] == usage) &
        (df["MODELE"] == modele) &
        (df["ENERGY"] == energy) &
        (df["PUISSANCE"].apply(lambda x: power in x)) &
        (df["PLACE"].apply(lambda x: place in x))
    )

    result = df.loc[condition]
    
    if result.empty:
        raise ValueError(f"No matching tarif found for CAT 4: usage={usage}, modele={modele}, "
                        f"energy={energy}, power={power}, place={place}")
    
    # Extract row as series for easier access
    row = result.iloc[0]
    
    # Build detailed pricing breakdown for CAT 4
    pricing = {
        "OFFRE_3_MOIS": {
            "RC": int(round(row["RC_3M"])),
            "IND_CHAUF": int(round(row["IND_CHAUF"])),
            "GESTION_POOL": int(round(row["GESTION_POOL_3M"])),
            "POLICE": int(round(row["POLICE"])),
            "TAXES": int(round(row["TAXES_3M"])),
            "TIMBRE": int(round(row["TIMBRE"])),
            "CARTE_ROSE": int(round(row["CARTE_ROSE"])),
            "PRIME_TOTALE": int(round(row["PRIME_3M"]))
        },
        "OFFRE_6_MOIS": {
            "RC": int(round(row["RC_6M"])),
            "IND_CHAUF": int(round(row["IND_CHAUF"])),
            "GESTION_POOL": int(round(row["GESTION_POOL_6M"])),
            "POLICE": int(round(row["POLICE"])),
            "TAXES": int(round(row["TAXES_6M"])),
            "TIMBRE": int(round(row["TIMBRE"])),
            "CARTE_ROSE": int(round(row["CARTE_ROSE"])),
            "PRIME_TOTALE": int(round(row["PRIME_6M"]))
        },
        "OFFRE_12_MOIS": {
            "RC": int(round(row["RC_12M"])),
            "IND_CHAUF": int(round(row["IND_CHAUF"])),
            "GESTION_POOL": int(round(row["GESTION_POOL_12M"])),
            "POLICE": int(round(row["POLICE"])),
            "TAXES": int(round(row["TAXES_12M"])),
            "TIMBRE": int(round(row["TIMBRE"])),
            "CARTE_ROSE": int(round(row["CARTE_ROSE"])),
            "PRIME_TOTALE": int(round(row["PRIME_12M"]))
        },
        "INFORMATIONS": {
            "USAGE": row["USAGE"],
            "MODELE": row["MODELE"],
            "CATEGORIE": int(row["CATEGORIE"]),
            "PLACE": f"{place}",
            "PUISSANCE": f"{power}"
        }
    }

    return pricing


# ============================================================================
# Fonction de quotation MRH
# ============================================================================

def get_mrh_forfaits() -> dict:
    """
    Récupère tous les forfaits MRH disponibles.

    Returns:
        dict: Dictionnaire contenant tous les forfaits MRH avec leurs prix et garanties.
    """
    try:
        with open(os.path.join(DATA_DIR, "mrh_forfaits.json"), "r", encoding="utf-8") as f:
            mrh_data = json.load(f)
        return mrh_data
    except Exception as e:
        logging.error(f"Erreur lors de la lecture des forfaits MRH: {e}")
        return {}


def get_mrh_quotation(forfait: str = None) -> dict:
    """
    Retourne la quotation pour un forfait MRH spécifique ou tous les forfaits.

    Args:
        forfait (str, optional): Nom du forfait ("standard", "equilibre", "confort", "premium").
                                Si None, retourne tous les forfaits.

    Returns:
        dict: Dictionnaire contenant les informations du/des forfait(s) MRH.
    """
    mrh_data = get_mrh_forfaits()

    if not mrh_data:
        raise ValueError("Impossible de charger les données des forfaits MRH")

    forfaits = mrh_data.get("forfaits", {})
    garanties = mrh_data.get("garanties_incluses", {})

    # Normaliser le nom du forfait
    if forfait:
        forfait = forfait.lower().strip()
        if forfait not in forfaits:
            raise ValueError(f"Forfait '{forfait}' non trouvé. Forfaits disponibles: {', '.join(forfaits.keys())}")

        # Retourner un forfait spécifique
        forfait_info = forfaits[forfait]
        return {
            "forfait": forfait,
            "nom": forfait_info["nom"],
            "prime_annuelle": forfait_info["prime_annuelle"],
            "couverture": forfait_info["couverture"],
            "description": forfait_info["description"],
            "garanties": garanties.get(forfait, [])
        }

    # Retourner tous les forfaits
    result = {}
    for key, forfait_info in forfaits.items():
        result[key] = {
            "nom": forfait_info["nom"],
            "prime_annuelle": forfait_info["prime_annuelle"],
            "couverture": forfait_info["couverture"],
            "description": forfait_info["description"],
            "garanties": garanties.get(key, [])
        }

    return result


def format_mrh_quotation_response(forfait: str = None) -> str:
    """
    Formate la réponse de quotation MRH pour l'affichage à l'utilisateur.

    Args:
        forfait (str, optional): Nom du forfait spécifique ou None pour tous.

    Returns:
        str: Message formaté pour l'utilisateur.
    """
    try:
        quotation = get_mrh_quotation(forfait)

        if forfait:
            # Un seul forfait
            message = f"📋 *Forfait MRH {quotation['nom']}*\n\n"
            message += f"💰 *Prime annuelle:* {quotation['prime_annuelle']:,} FCFA\n"
            message += f"🏠 *Couverture:* {quotation['couverture']:,} FCFA\n"
            message += f"📝 *Description:* {quotation['description']}\n\n"
            message += "*Garanties incluses:*\n"
            for garantie in quotation['garanties']:
                message += f"✅ {garantie}\n"
        else:
            # Tous les forfaits
            message = "🏠 *NOS FORFAITS MULTIRISQUE HABITATION (MRH)*\n\n"

            for key in ["standard", "equilibre", "confort", "premium"]:
                if key in quotation:
                    forfait_info = quotation[key]
                    message += f"📦 *{forfait_info['nom']}* - {forfait_info['prime_annuelle']:,} FCFA/an\n"
                    message += f"   {forfait_info['description']}\n\n"

            message += "\n💡 Pour plus de détails sur un forfait spécifique, demandez-moi !"

        return message

    except Exception as e:
        logging.error(f"Erreur lors du formatage de la quotation MRH: {e}")
        return f"❌ Erreur lors de la récupération des forfaits MRH: {str(e)}"


# ============================================================================
# Fonction de quotation IAC (Individuelle Accident)
# ============================================================================

def get_iac_data() -> dict:
    """
    Récupère les données de tarification IAC.

    Returns:
        dict: Dictionnaire contenant les données de tarification IAC.
    """
    try:
        with open(os.path.join(DATA_DIR, "iac_tarification.json"), "r", encoding="utf-8") as f:
            iac_data = json.load(f)
        return iac_data
    except Exception as e:
        logging.error(f"Erreur lors de la lecture des données IAC: {e}")
        return {}


def get_iac_quotation(statut: str = None) -> dict:
    """
    Retourne la quotation pour l'assurance Individuelle Accident.

    Args:
        statut (str, optional): Statut professionnel ("commercant", "travailleur_independant", "entrepreneur").
                               Si None, retourne les informations générales.

    Returns:
        dict: Dictionnaire contenant les informations de tarification IAC.
    """
    iac_data = get_iac_data()

    if not iac_data:
        raise ValueError("Impossible de charger les données IAC")

    tarification = iac_data.get("tarification", {})
    statuts = iac_data.get("statuts_professionnels", [])
    garanties = iac_data.get("garanties_incluses", [])
    capitaux = iac_data.get("capitaux_garantis", {})

    result = {
        "prime_ttc": tarification.get("prime_ttc", 12500),
        "devise": tarification.get("devise", "FCFA"),
        "periode": tarification.get("periode", "annuelle"),
        "statuts_disponibles": statuts,
        "garanties": garanties,
        "capitaux_garantis": capitaux
    }

    if statut:
        # Normaliser le statut
        statut = statut.lower().strip()
        statut_info = next((s for s in statuts if s["code"] == statut), None)

        if statut_info:
            result["statut_selectionne"] = statut_info
        else:
            raise ValueError(f"Statut '{statut}' non trouvé. Statuts disponibles: {', '.join([s['code'] for s in statuts])}")

    return result


def format_iac_quotation_response(statut: str = None, include_details: bool = True) -> str:
    """
    Formate la réponse de quotation IAC pour l'affichage à l'utilisateur.

    Args:
        statut (str, optional): Statut professionnel spécifique ou None pour informations générales.
        include_details (bool): Inclure les détails des garanties et capitaux.

    Returns:
        str: Message formaté pour l'utilisateur.
    """
    try:
        quotation = get_iac_quotation(statut)

        message = "🛡️ *NSIA INDIVIDUEL ACCIDENT*\n\n"
        message += f"💰 *Tarif unique:* {quotation['prime_ttc']:,} {quotation['devise']}/{quotation['periode']}\n\n"

        # Statuts disponibles
        if not statut:
            message += "*Quel est votre statut ?*\n"
            for s in quotation['statuts_disponibles']:
                message += f"○ {s['label']}\n"
            message += "\n"

        # Si un statut est sélectionné
        if statut and "statut_selectionne" in quotation:
            statut_info = quotation["statut_selectionne"]
            message += f"*Statut sélectionné:* {statut_info['label']}\n"
            message += f"_{statut_info['description']}_\n\n"

        # Garanties incluses
        if include_details:
            message += "*✅ Garanties incluses:*\n"
            for garantie in quotation['garanties']:
                message += f"• {garantie}\n"
            message += "\n"

            # Capitaux garantis
            message += "*💰 Capitaux garantis:*\n"
            capitaux = quotation['capitaux_garantis']

            if "deces_accident" in capitaux:
                message += f"• Décès par accident: {capitaux['deces_accident']['montant']:,} FCFA\n"

            if "invalidite_permanente_totale" in capitaux:
                message += f"• Invalidité permanente totale: {capitaux['invalidite_permanente_totale']['montant']:,} FCFA\n"

            if "frais_medicaux" in capitaux:
                message += f"• Frais médicaux: {capitaux['frais_medicaux']['montant']:,} FCFA\n"

            if "indemnites_hospitalisations" in capitaux:
                indemnites = capitaux['indemnites_hospitalisations']
                message += f"• Indemnités journalières: {indemnites['montant']:,} FCFA/jour "
                message += f"(max {indemnites.get('duree_max_jours', 365)} jours)\n"

        message += "\n📝 _Note: Le tarif est identique quel que soit le statut professionnel choisi._"

        return message

    except Exception as e:
        logging.error(f"Erreur lors du formatage de la quotation IAC: {e}")
        return f"❌ Erreur lors de la récupération des informations IAC: {str(e)}"


def validate_iac_statut(statut: str) -> bool:
    """
    Valide si le statut professionnel est valide pour l'IAC.

    Args:
        statut (str): Statut à valider.

    Returns:
        bool: True si le statut est valide, False sinon.
    """
    try:
        iac_data = get_iac_data()
        statuts = iac_data.get("statuts_professionnels", [])
        statut_normalise = statut.lower().strip()

        return any(s["code"] == statut_normalise or s["label"].lower() == statut_normalise
                  for s in statuts)
    except Exception as e:
        logging.error(f"Erreur lors de la validation du statut IAC: {e}")
        return False