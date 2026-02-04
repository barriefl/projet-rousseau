import csv
import os
import difflib
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
CSV_PATH = DATA_DIR / "SECRET_correspondance.csv"
DICTATES_DIR = DATA_DIR / "dictates"

def normalize(text):
    """Nettoie le texte pour la comparaison."""
    return text.strip().lower().replace("-", " ").replace("_", " ")

def main():
    print(f"🔧 Correction automatique des fichiers dictées...\n")

    csv_db = []
    
    encodings = ['utf-8-sig', 'cp1252', 'latin-1']
    for encoding in encodings:
        try:
            with open(CSV_PATH, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=';')
                if not reader.fieldnames: continue
                
                for row in reader:
                    clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                    nom = clean_row.get('nom')
                    prenom = clean_row.get('prenom') or clean_row.get('prénom')
                    
                    if nom and prenom:
                        csv_db.append({
                            'nom': nom,
                            'prenom': prenom,
                            'compare_key': f"{normalize(nom)} {normalize(prenom)}"
                        })
                if csv_db: break
        except: continue
    
    if not csv_db:
        print("❌ Impossible de lire le CSV Correspondance.")
        return

    print(f"✅ {len(csv_db)} étudiants chargés depuis le CSV.")
    
    renamed_count = 0
    csv_keys = [x['compare_key'] for x in csv_db]
    
    for file_path in DICTATES_DIR.glob("*.txt"):
        if "GRAZIANO" in file_path.name: continue
        
        parts = file_path.stem.split('_')
        if len(parts) < 2: continue
        
        current_nom = parts[0]
        current_prenom = parts[1]
        suffix = "_" + "_".join(parts[2:]) if len(parts) > 2 else ""
        
        file_compare_key = f"{normalize(current_nom)} {normalize(current_prenom)}"
        
        if file_compare_key in csv_keys:
            continue
            
        matches = difflib.get_close_matches(file_compare_key, csv_keys, n=1, cutoff=0.75)
        
        if matches:
            match_key = matches[0]
            target_data = next(x for x in csv_db if x['compare_key'] == match_key)
            
            target_nom = target_data['nom']
            target_prenom = target_data['prenom']
            
            new_filename = f"{target_nom}_{target_prenom}{suffix}.txt"
            new_path = DICTATES_DIR / new_filename
            
            print(f"🔄 Renommage : {file_path.name:<35} -> {new_filename}")
            
            try:
                os.rename(file_path, new_path)
                renamed_count += 1
            except Exception as e:
                print(f"   ❌ Erreur : {e}")
        else:
            print(f"⚠️  Pas de correspondance trouvée pour : {file_path.name} (Ajoutez-le au CSV !)")

    print(f"\n🎉 Terminé ! {renamed_count} fichiers corrigés.")

if __name__ == "__main__":
    main()