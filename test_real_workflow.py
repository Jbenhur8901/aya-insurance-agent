"""
Test du workflow complet avec une vraie carte grise
"""
import asyncio
import json
from uuid import uuid4

# URL de la carte grise fournie par l'utilisateur
CARTE_GRISE_URL = "https://phwyhgzcnnjffovepbrt.supabase.co/storage/v1/object/public/file/WhatsApp%20Image%202025-12-24%20at%2016.51.09.jpeg"

async def test_complete_workflow():
    """Test du workflow AUTO complet avec une vraie carte grise"""
    print("=" * 80)
    print("🧪 TEST WORKFLOW COMPLET - Carte Grise Réelle")
    print("=" * 80)
    print(f"\n📸 URL Carte Grise: {CARTE_GRISE_URL}\n")

    from app.tools.quotation import image_processor, Grey_card, VISION_INSTRUCTION, ttcAuto_all
    from app.config import settings
    from app.services.supabase_client import supabase_service
    from app.models.schemas import ClientCreate, SouscriptionCreate, AutoData

    # ÉTAPE 1: Analyser la carte grise
    print("=" * 80)
    print("ÉTAPE 1: ANALYSE DE LA CARTE GRISE")
    print("=" * 80)

    try:
        print("⏳ Analyse en cours avec Gemini Vision...")

        carte_data = image_processor(
            image_path=CARTE_GRISE_URL,
            vision_model=settings.VISION_MODEL,
            vision_instruction=VISION_INSTRUCTION,
            response_schema=Grey_card
        )

        print("\n✅ Carte grise analysée avec succès!")
        print(f"\n📋 Informations extraites:")
        print(f"   • Nom: {carte_data.get('fullname', 'N/A')}")
        print(f"   • Immatriculation: {carte_data.get('immatriculation', 'N/A')}")
        print(f"   • Puissance: {carte_data.get('power', 'N/A')} CV")
        print(f"   • Places: {carte_data.get('seat_number', 'N/A')}")
        print(f"   • Carburant: {carte_data.get('fuel_type', 'N/A')}")
        print(f"   • Marque: {carte_data.get('brand', 'N/A')}")
        print(f"   • Modèle: {carte_data.get('model', 'N/A')}")
        print(f"   • Châssis: {carte_data.get('chassis_number', 'N/A')}")
        print(f"   • Téléphone: {carte_data.get('phone', 'N/A')}")

    except Exception as e:
        print(f"\n❌ ERREUR lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ÉTAPE 2: Calculer les tarifs
    print("\n" + "=" * 80)
    print("ÉTAPE 2: CALCUL DES TARIFS AUTO")
    print("=" * 80)

    try:
        print("⏳ Calcul des tarifs en cours...")

        # Extraire les paramètres nécessaires
        # Nettoyer le champ power (enlever "CV" et autres caractères)
        power_str = str(carte_data.get('power', '7')).upper().replace('CV', '').strip()
        power = int(power_str)

        seat_number = int(carte_data.get('seat_number', 5))
        fuel_type = carte_data.get('fuel_type', 'ESSENCE').upper()

        # Détecter le modèle de véhicule
        model_name = carte_data.get('model', '').upper()
        if 'PICNIC' in model_name or 'PIC NIC' in model_name:
            modele = "PICNIC"
            usage = "TRANSPORT PUBLIC VOYAGEURS"
        elif 'TAXI' in model_name:
            modele = "TAXI"
            usage = "TRANSPORT PUBLIC VOYAGEURS"
        else:
            modele = "VOITURE"
            usage = "PROMENADE/AFFAIRES"

        print(f"   • Puissance: {power} CV")
        print(f"   • Places: {seat_number}")
        print(f"   • Carburant: {fuel_type}")
        print(f"   • Modèle détecté: {modele}")
        print(f"   • Usage: {usage}")

        # Calculer selon le type de véhicule
        if modele in ["PICNIC", "TAXI", "MINI-BUS", "COASTER"]:
            from app.tools.quotation import ttc_auto_cat4
            quotation = ttc_auto_cat4(
                power=power,
                energy=fuel_type,
                modele=modele,
                place=seat_number
            )
        else:
            quotation = ttcAuto_all(
                power=power,
                energy=fuel_type,
                place=seat_number,
                modele=modele,
                usage=usage
            )

        print("\n✅ Tarifs calculés avec succès!")
        print(f"\n💰 Offres disponibles:")

        if "OFFRE_3_MOIS" in quotation:
            offre_3m = quotation["OFFRE_3_MOIS"]
            print(f"   • 3 MOIS: {offre_3m.get('PRIME_TOTALE', 0):,} FCFA")

        if "OFFRE_6_MOIS" in quotation:
            offre_6m = quotation["OFFRE_6_MOIS"]
            print(f"   • 6 MOIS: {offre_6m.get('PRIME_TOTALE', 0):,} FCFA")

        if "OFFRE_12_MOIS" in quotation:
            offre_12m = quotation["OFFRE_12_MOIS"]
            print(f"   • 12 MOIS: {offre_12m.get('PRIME_TOTALE', 0):,} FCFA")

        # Utiliser l'offre 12 mois pour la suite
        prime_ttc = int(offre_12m.get('PRIME_TOTALE', 0))
        coverage = "12M"

    except Exception as e:
        print(f"\n❌ ERREUR lors du calcul: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ÉTAPE 3: Créer/Récupérer le client
    print("\n" + "=" * 80)
    print("ÉTAPE 3: CRÉATION/RÉCUPÉRATION DU CLIENT")
    print("=" * 80)

    try:
        # Utiliser un numéro de test si pas de téléphone dans la carte
        phone_number = carte_data.get('phone') or f"+242066{uuid4().hex[:6]}"
        fullname = carte_data.get('fullname', 'Client Test')

        print(f"⏳ Recherche du client: {phone_number}")

        client = await supabase_service.get_client_by_phone(phone_number)

        if client:
            print(f"✅ Client existant trouvé: {client.id}")
            client_id = client.id
        else:
            print(f"⏳ Création d'un nouveau client...")
            client_data = ClientCreate(
                whatsappnumber=phone_number,
                fullname=fullname,
                status="active",
                address=carte_data.get('address'),
                profession=carte_data.get('profession')
            )

            new_client = await supabase_service.create_client(client_data)

            if new_client:
                client_id = new_client.id
                print(f"✅ Nouveau client créé: {client_id}")
            else:
                print("❌ Impossible de créer le client")
                return False

    except Exception as e:
        print(f"\n❌ ERREUR lors de la gestion du client: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ÉTAPE 4: Créer la souscription
    print("\n" + "=" * 80)
    print("ÉTAPE 4: CRÉATION DE LA SOUSCRIPTION")
    print("=" * 80)

    try:
        print(f"⏳ Création de la souscription...")
        print(f"   • Client ID: {client_id}")
        print(f"   • Produit: AUTO")
        print(f"   • Prime TTC: {prime_ttc:,} FCFA")
        print(f"   • Période: {coverage}")

        souscription_data = SouscriptionCreate(
            client_id=client_id,
            producttype="auto",
            prime_ttc=float(prime_ttc),
            coverage_duration=coverage,
            status="en_cours"
        )

        souscription = await supabase_service.create_souscription(souscription_data)

        if souscription:
            souscription_id = souscription.id
            print(f"\n✅ Souscription créée: {souscription_id}")
        else:
            print("❌ Impossible de créer la souscription")
            return False

    except Exception as e:
        print(f"\n❌ ERREUR lors de la création de la souscription: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ÉTAPE 5: Enregistrer les détails AUTO
    print("\n" + "=" * 80)
    print("ÉTAPE 5: ENREGISTREMENT DES DÉTAILS AUTO")
    print("=" * 80)

    try:
        print(f"⏳ Enregistrement des détails dans souscription_auto...")

        auto_data = AutoData(
            fullname=fullname,
            immatriculation=carte_data.get('immatriculation', 'N/A'),
            power=str(carte_data.get('power', 7)),
            seat_number=int(carte_data.get('seat_number', 5)),
            fuel_type=carte_data.get('fuel_type', 'ESSENCE').upper(),
            brand=carte_data.get('brand', 'N/A'),
            phone=phone_number,
            prime_ttc=prime_ttc,
            coverage=coverage,
            quotation=quotation,
            chassis_number=carte_data.get('chassis_number'),
            model=carte_data.get('model'),
            address=carte_data.get('address'),
            profession=carte_data.get('profession'),
            documentUrl=CARTE_GRISE_URL
        )

        success = await supabase_service.create_souscription_auto(
            data=auto_data,
            souscription_id=souscription_id
        )

        if success:
            print(f"\n✅ Détails AUTO enregistrés dans souscription_auto!")
        else:
            print("❌ Impossible d'enregistrer les détails AUTO")
            return False

    except Exception as e:
        print(f"\n❌ ERREUR lors de l'enregistrement des détails: {e}")
        import traceback
        traceback.print_exc()
        return False

    # RÉSUMÉ
    print("\n" + "=" * 80)
    print("🎉 WORKFLOW COMPLET RÉUSSI!")
    print("=" * 80)
    print(f"\n📊 Résumé:")
    print(f"   • Client ID: {client_id}")
    print(f"   • Nom: {fullname}")
    print(f"   • Téléphone: {phone_number}")
    print(f"   • Souscription ID: {souscription_id}")
    print(f"   • Immatriculation: {carte_data.get('immatriculation', 'N/A')}")
    print(f"   • Prime TTC: {prime_ttc:,} FCFA")
    print(f"   • Période: {coverage}")

    print(f"\n💾 Données enregistrées dans Supabase:")
    print(f"   ✅ Table clients")
    print(f"   ✅ Table souscriptions")
    print(f"   ✅ Table souscription_auto")

    print(f"\n👉 Prochaine étape:")
    print(f"   → Vérifier dans Supabase Dashboard")
    print(f"   → Initier le paiement MTN MoMo")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_complete_workflow())

    if not success:
        print("\n❌ Le test a échoué")
        exit(1)

    print("\n✅ Test terminé avec succès!")
