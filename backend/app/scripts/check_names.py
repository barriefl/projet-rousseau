import csv
import os
import difflib
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
CSV_PATH = DATA_DIR / "SECRET_correspondance.csv"
DICTATES_DIR = DATA_DIR / "dictates"

def normalize(text):
    """Nettoie le texte pour la comparaison (minuscule, sans espaces)."""
    if not text: 
        return ""
    text = text.strip().lower().replace("-", " ").replace("_", " ")
    return " ".join(text.split())

def main():
    print(f"🔍 Analyse croisée : CSV vs Fichiers Dictées...\n")

    # Structure : { "nom prenom normalisé": { "original": "Nom Prénom", "initial": False, "final": False } }
    student_tracker = {}
    encodings = ['utf-8-sig', 'cp1252', 'latin-1']
    csv_loaded = False

    # --- 1. CHARGEMENT DU CSV ---
    for encoding in encodings:
        try:
            with open(CSV_PATH, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=';')
                if not reader.fieldnames: continue

                temp_tracker = {}
                for row in reader:
                    clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                    nom = clean_row.get('nom')
                    prenom = clean_row.get('prenom') or clean_row.get('prénom')
                    
                    if nom and prenom:
                        key = f"{normalize(nom)} {normalize(prenom)}"
                        # On stocke le nom d'origine pour l'affichage et deux booléens pour les dictées
                        temp_tracker[key] = {
                            "original": f"{nom} {prenom}", 
                            "initial": False, 
                            "final": False
                        }

                if temp_tracker:
                    student_tracker = temp_tracker
                    print(f"✅ CSV chargé avec {encoding} ({len(student_tracker)} étudiants).")
                    csv_loaded = True
                    break
        except:
            continue
    
    if not csv_loaded:
        print("❌ Impossible de lire le CSV.")
        return

    # --- 2. ANALYSE DES FICHIERS ---
    files_orphans = []
    
    # On parcourt récursivement tous les fichiers txt
    for f in DICTATES_DIR.rglob("*.txt"):
        if "GRAZIANO" in f.name: 
            continue

        parts = f.stem.split('_')
        if len(parts) >= 2:
            nom_fichier = normalize(parts[0])
            prenom_fichier = normalize(parts[1])
            full_name_norm = f"{nom_fichier} {prenom_fichier}"
            
            # Détection du type de dictée basé sur le dossier parent
            is_initial = "initial" in f.parent.name.lower()
            is_final = "final" in f.parent.name.lower()

            if full_name_norm in student_tracker:
                # MATCH : On coche la case correspondante
                if is_initial:
                    student_tracker[full_name_norm]["initial"] = True
                elif is_final:
                    student_tracker[full_name_norm]["final"] = True
                else:
                    # Cas rare : fichier trouvé mais dossier parent ne dit ni "initial" ni "final"
                    # On considère qu'il a au moins rendu quelque chose
                    pass 
            else:
                # NO MATCH : C'est un fichier orphelin
                files_orphans.append({
                    'norm': full_name_norm,
                    'path': f"{f.parent.name}/{f.name}"
                })

    # --- 3. RAPPORT : FICHIERS ORPHELINS (Ceux qui ne sont pas dans le CSV) ---
    print(f"\n{'='*40}")
    print(f"📁 RAPPORT 1 : Fichiers Dictées inconnus")
    print(f"{'='*40}")

    if not files_orphans:
        print("🎉 Aucun fichier orphelin. Tout correspond au CSV !")
    else:
        print(f"🚨 {len(files_orphans)} Fichiers ne correspondant à personne dans le CSV :\n")
        print(f"{'DICTÉE':<55} | {'SUGGESTION CSV':<30} | {'CONFIANCE'}")
        print("-" * 95)

        csv_keys_list = list(student_tracker.keys())
        for orphan in files_orphans:
            matches = difflib.get_close_matches(orphan['norm'], csv_keys_list, n=1, cutoff=0.6)
            suggestion_key = matches[0] if matches else None
            suggestion_display = student_tracker[suggestion_key]["original"] if suggestion_key else "???"
            score = difflib.SequenceMatcher(None, orphan['norm'], suggestion_key).ratio() if suggestion_key else 0
            
            print(f"{orphan['path']:<55} | {suggestion_display:<30} | {score:.2f}")

    # --- 4. RAPPORT : ÉTUDIANTS MANQUANTS (Ceux qui sont dans le CSV mais sans dictée) ---
    print(f"\n{'='*40}")
    print(f"👥 RAPPORT 2 : Étudiants du CSV sans dictées")
    print(f"{'='*40}")

    missing_all = []
    missing_initial = []
    missing_final = []

    for key, data in student_tracker.items():
        if not data["initial"] and not data["final"]:
            missing_all.append(data["original"])
        elif not data["initial"]:
            missing_initial.append(data["original"])
        elif not data["final"]:
            missing_final.append(data["original"])

    if not missing_all and not missing_initial and not missing_final:
        print("🎉 Parfait ! Tous les étudiants ont leurs deux dictées.")
    else:
        if missing_all:
            print(f"\n🔴 MANQUENT TOUT ({len(missing_all)}) :")
            for name in sorted(missing_all):
                print(f"   - {name}")
        
        if missing_initial:
            print(f"\n🟠 MANQUENT INITIALE SEULEMENT ({len(missing_initial)}) :")
            for name in sorted(missing_initial):
                print(f"   - {name}")

        if missing_final:
            print(f"\n🟡 MANQUENT FINALE SEULEMENT ({len(missing_final)}) :")
            for name in sorted(missing_final):
                print(f"   - {name}")

if __name__ == "__main__":
    main()