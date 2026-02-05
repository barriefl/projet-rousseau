import csv
from email.mime import text
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
    print(f"🔍 Analyse des différences entre CSV et dictées...\n")

    csv_names = set()
    encodings = ['utf-8-sig', 'cp1252', 'latin-1']

    for encoding in encodings:
        try:
            with open(CSV_PATH, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=';')

                if not reader.fieldnames: 
                    continue

                temp_names = set()
                for row in reader:
                    clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                    nom = clean_row.get('nom')
                    prenom = clean_row.get('prenom') or clean_row.get('prénom')
                    if nom and prenom:
                        key = f"{normalize(nom)} {normalize(prenom)}"
                        temp_names.add(key)

                if temp_names:
                    csv_names = temp_names
                    print(f"✅ CSV chargé avec {encoding} ({len(csv_names)} étudiants).")
                    break
        except:
            continue
        
        if not csv_names:
            print("❌ Impossible de lire le CSV.")
            return

    files_to_check = []
    
    for f in DICTATES_DIR.rglob("*.txt"):
        if "GRAZIANO" in f.name: 
            continue

        parts = f.stem.split('_')
        if len(parts) >= 2:
            nom_fichier = normalize(parts[0])
            prenom_fichier = normalize(parts[1])
            full_name = f"{nom_fichier} {prenom_fichier}"

            files_to_check.append({
                'norm': full_name,
                'path': f"{f.parent.name}/{f.name}"
            })

    print(f"✅ {len(files_to_check)} fichiers trouvés dans le dossier dictées.\n")

    orphans = [item for item in files_to_check if item['norm'] not in csv_names]

    if not orphans:
        print("🎉 Tous les fichiers dictées correspondent à des étudiants du CSV !")
        return
    
    print(f"🚨 {len(orphans)} Fichiers Orphelins (Non trouvés dans le CSV) :\n")
    print(f"{'DICTÉE':<55} | {'CSV':<30} | {'CONFIANCE'}")
    print("-" * 95)

    csv_names_list = list(csv_names)

    for orphan in orphans:
        matches = difflib.get_close_matches(orphan['norm'], csv_names_list, n=1, cutoff=0.6)
        
        suggestion = matches[0] if matches else "???"
        score = difflib.SequenceMatcher(None, orphan['norm'], suggestion).ratio() if matches else 0
        
        print(f"{orphan['path']:<55} | {suggestion.title():<30} | {score:.2f}")

if __name__ == "__main__":
    main()