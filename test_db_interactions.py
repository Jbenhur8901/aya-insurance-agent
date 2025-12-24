"""
Test des interactions avec la base de données
Ce script teste le workflow complet de création client -> souscription -> détails produit
"""
import asyncio
import sys
import json
from uuid import uuid4, UUID

async def test_workflow_auto():
    """Test du workflow AUTO complet"""
    print("=" * 80)
    print("🧪 TEST WORKFLOW AUTO - Interactions avec la base de données")
    print("=" * 80)

    from app.services.supabase_client import supabase_service
    from app.models.schemas import ClientCreate, SouscriptionCreate, AutoData

    # Données de test
    test_phone = f"+242066{uuid4().hex[:6]}"
    test_fullname = "Jean MOKOKO"

    print(f"\n1️⃣ Test création/récupération client")
    print(f"   Téléphone: {test_phone}")
    print(f"   Nom: {test_fullname}")

    try:
        # Chercher client existant
        client = await supabase_service.get_client_by_phone(test_phone)

        if client:
            print(f"   ✅ Client existant trouvé: {client.id}")
            client_id = client.id
        else:
            # Créer nouveau client
            client_data = ClientCreate(
                whatsappnumber=test_phone,
                fullname=test_fullname,
                status="active"
            )
            new_client = await supabase_service.create_client(client_data)

            if new_client:
                client_id = new_client.id
                print(f"   ✅ Nouveau client créé: {client_id}")
            else:
                print(f"   ❌ ERREUR: Impossible de créer le client")
                return False

    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

    print(f"\n2️⃣ Test création souscription")
    print(f"   Client ID: {client_id}")
    print(f"   Produit: auto")
    print(f"   Prime TTC: 85000 FCFA")
    print(f"   Période: 12M")

    try:
        souscription_data = SouscriptionCreate(
            client_id=client_id,
            producttype="auto",
            prime_ttc=85000.0,
            coverage_duration="12M",
            status="en_cours"
        )

        souscription = await supabase_service.create_souscription(souscription_data)

        if souscription:
            souscription_id = souscription.id
            print(f"   ✅ Souscription créée: {souscription_id}")
        else:
            print(f"   ❌ ERREUR: Impossible de créer la souscription")
            return False

    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

    print(f"\n3️⃣ Test enregistrement détails AUTO")
    print(f"   Souscription ID: {souscription_id}")

    # Créer une quotation de test
    quotation_data = {
        "OFFRE_12_MOIS": {
            "PRIME_TOTALE": 85000,
            "PRIME_NETTE": 75000,
            "ACCESSOIRES": 5000,
            "TAXES": 5000
        }
    }

    try:
        auto_data = AutoData(
            fullname=test_fullname,
            immatriculation="ABC-123-CG",
            power="7",
            seat_number=5,
            fuel_type="ESSENCE",
            brand="TOYOTA",
            phone=test_phone,
            prime_ttc=85000,
            coverage="12M",
            quotation=quotation_data,
            chassis_number="VIN123456789",
            model="COROLLA",
            address="Brazzaville",
            profession="Ingénieur"
        )

        success = await supabase_service.create_souscription_auto(
            data=auto_data,
            souscription_id=souscription_id
        )

        if success:
            print(f"   ✅ Détails AUTO enregistrés dans souscription_auto")
        else:
            print(f"   ❌ ERREUR: Impossible d'enregistrer les détails AUTO")
            return False

    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 80)
    print("✅ TEST AUTO RÉUSSI!")
    print("=" * 80)
    print(f"\n📊 Résumé:")
    print(f"   • Client créé: {client_id}")
    print(f"   • Souscription créée: {souscription_id}")
    print(f"   • Détails AUTO enregistrés: ✅")
    print(f"\n💾 Vérifiez dans Supabase:")
    print(f"   • Table clients: whatsappnumber = {test_phone}")
    print(f"   • Table souscriptions: id = {souscription_id}")
    print(f"   • Table souscription_auto: souscription_id = {souscription_id}")

    return True


async def test_workflow_voyage():
    """Test du workflow VOYAGE"""
    print("\n" + "=" * 80)
    print("🧪 TEST WORKFLOW VOYAGE - Interactions avec la base de données")
    print("=" * 80)

    from app.services.supabase_client import supabase_service
    from app.models.schemas import ClientCreate, SouscriptionCreate, VoyageData

    test_phone = f"+242066{uuid4().hex[:6]}"
    test_fullname = "Marie NGOMA"

    print(f"\n1️⃣ Création client VOYAGE")
    print(f"   Téléphone: {test_phone}")

    try:
        client_data = ClientCreate(
            whatsappnumber=test_phone,
            fullname=test_fullname,
            status="active"
        )
        client = await supabase_service.create_client(client_data)

        if client:
            client_id = client.id
            print(f"   ✅ Client créé: {client_id}")
        else:
            print(f"   ❌ ERREUR: Impossible de créer le client")
            return False

    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

    print(f"\n2️⃣ Création souscription VOYAGE")

    try:
        souscription_data = SouscriptionCreate(
            client_id=client_id,
            producttype="voyage",
            prime_ttc=45000.0,
            coverage_duration="30J",
            status="en_cours"
        )
        souscription = await supabase_service.create_souscription(souscription_data)

        if souscription:
            souscription_id = souscription.id
            print(f"   ✅ Souscription créée: {souscription_id}")
        else:
            print(f"   ❌ ERREUR: Impossible de créer la souscription")
            return False

    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

    print(f"\n3️⃣ Enregistrement détails VOYAGE")

    try:
        voyage_data = VoyageData(
            full_name=test_fullname,
            passport_number="P123456789",
            prime_ttc="45000",
            coverage="30J",
            nationality="Congolaise",
            date_of_birth="1990-05-15",
            sex="F"
        )

        success = await supabase_service.create_souscription_voyage(
            data=voyage_data,
            souscription_id=souscription_id
        )

        if success:
            print(f"   ✅ Détails VOYAGE enregistrés dans souscription_voyage")
        else:
            print(f"   ❌ ERREUR: Impossible d'enregistrer les détails VOYAGE")
            return False

    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n✅ TEST VOYAGE RÉUSSI!")
    print(f"\n📊 Résumé:")
    print(f"   • Client créé: {client_id}")
    print(f"   • Souscription créée: {souscription_id}")
    print(f"   • Détails VOYAGE enregistrés: ✅")

    return True


async def main():
    """Exécute tous les tests"""
    print("\n🚀 Démarrage des tests d'interaction avec la base de données\n")

    # Test AUTO
    auto_success = await test_workflow_auto()

    if not auto_success:
        print("\n❌ Le test AUTO a échoué")
        sys.exit(1)

    # Test VOYAGE
    voyage_success = await test_workflow_voyage()

    if not voyage_success:
        print("\n❌ Le test VOYAGE a échoué")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("🎉 TOUS LES TESTS ONT RÉUSSI!")
    print("=" * 80)
    print("\n✅ Les interactions avec la base de données fonctionnent correctement.")
    print("✅ Les workflows AUTO et VOYAGE sont opérationnels.")
    print("\n👉 Prochaine étape: Vérifier les données dans Supabase Dashboard")


if __name__ == "__main__":
    asyncio.run(main())
