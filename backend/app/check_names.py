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
    """Nettoie le texte pour la comparaison (minuscule, sans espaces)."""
    return text.strip().lower().replace("-", " ").replace("_", " ")

def main():
    print(f"🔍 Analyse des différences entre CSV et dictées...\n")

    csv_names = set()
    try:
        # On reprend votre logique robuste de lecture
        encodings = ['utf-8-sig', 'cp1252', 'latin-1']
        found = False
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
                            csv_names.add(f"{normalize(nom)} {normalize(prenom)}")
                    found = True
                    print(f"✅ CSV chargé avec {encoding} ({len(csv_names)} étudiants).")
                    break
            except:
                continue
        
        if not found:
            print("❌ Impossible de lire le CSV.")
            return

    except Exception as e:
        print(f"❌ Erreur CSV : {e}")
        return

    file_names = []
    file_map = {}
    
    for f in DICTATES_DIR.glob("*.txt"):
        if "GRAZIANO" in f.name: continue
        parts = f.stem.split('_')
        if len(parts) >= 2:
            nom_fichier = normalize(parts[0])
            prenom_fichier = normalize(parts[1])
            full_name = f"{nom_fichier} {prenom_fichier}"
            file_names.append(full_name)
            file_map[full_name] = f.name

    print(f"✅ {len(file_names)} fichiers trouvés dans le dossier dictées.\n")

    orphans = [name for name in file_names if name not in csv_names]
    
    print(f"🚨 {len(orphans)} Fichiers Orphelins (Non trouvés dans le CSV) :\n")
    print(f"{'DICTÉE':<40} | {'CSV':<40} | {'CONFIANCE'}")
    print("-" * 95)

    for orphan in orphans:
        matches = difflib.get_close_matches(orphan, csv_names, n=1, cutoff=0.6)
        
        suggestion = matches[0] if matches else "???"
        score = difflib.SequenceMatcher(None, orphan, suggestion).ratio() if matches else 0
        
        original_filename = file_map[orphan]
        
        print(f"{original_filename:<40} | {suggestion.title():<40} | {score:.2f}")

if __name__ == "__main__":
    main()