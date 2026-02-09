import csv
import sys
import os
import difflib
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Set, Tuple, List, Dict

# --- CONFIGURATION ---
DATA_DIR = Path("/data")
REPORT_DIR = DATA_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True) # Crée le dossier s'il n'existe pas

FILES = {
    "SECRET": DATA_DIR / "SECRET_correspondance.csv",
    "VOLTAIRE_INIT": DATA_DIR / "results/voltaire_initial.csv",
    "VOLTAIRE_FINAL": DATA_DIR / "results/voltaire_final.csv",
    "ECRIPLUS_INIT": DATA_DIR / "results/ecriplus_initial.csv",
    "ECRIPLUS_FINAL": DATA_DIR / "results/ecriplus_final.csv"
}

# --- OUTILS ---
def normalize_text(text):
    if not text: return ""
    # Suppression accents (Clément -> Clement)
    text = unicodedata.normalize('NFD', text)
    text = "".join(c for c in text if unicodedata.category(c) != 'Mn')
    # Standardisation
    text = text.strip().lower().replace("-", " ").replace("_", " ")
    return " ".join(text.split())

def get_suggestion(target_nom, target_prenom, secret_database):
    target_full = f"{target_nom} {target_prenom}"
    secret_strings = [f"{s['nom']} {s['prenom']}" for s in secret_database]
    
    matches = difflib.get_close_matches(target_full, secret_strings, n=1, cutoff=0.6)
    if matches:
        return f"💡 Peut-être : '{matches[0]}' ?"

    target_tokens = set(target_full.split())
    for s in secret_database:
        secret_full = f"{s['nom']} {s['prenom']}"
        secret_tokens = set(secret_full.split())
        common = target_tokens.intersection(secret_tokens)
        if len(common) >= 2 or (len(common) >= 1 and len(target_tokens) <= 2):
             if len(common) / len(secret_tokens) > 0.5:
                 return f"💡 Mots communs trouvés dans : '{secret_full}'"

    return "🚫 Totalement inconnu (Absent du fichier Secret ?)"

def read_csv_smart(path: Path) -> List[Dict[str, str]]:
    if not path.exists(): return []
    encodings = ['utf-8-sig', 'cp1252', 'latin-1']
    for encoding in encodings:
        try:
            with open(path, 'r', encoding=encoding) as f:
                sample = f.read(2048)
                f.seek(0)
                try: dialect = csv.Sniffer().sniff(sample, delimiters=[',', ';', '\t'])
                except: dialect = csv.Dialect; dialect.delimiter = ';' if ';' in sample else ','
                reader = csv.DictReader(f, delimiter=dialect.delimiter)
                return list(reader)
        except: continue
    return []

def get_name_columns(headers: List[str]) -> Tuple[str, str]:
    normalized_headers = {h.lower(): h for h in headers}
    if "nom du participant" in normalized_headers:
        return normalized_headers["nom du participant"], normalized_headers.get("prénom du participant", "Prénom du Participant")
    if "nom" in normalized_headers:
        return normalized_headers["nom"], next((h for h in headers if "prénom" in h.lower() or "prenom" in h.lower()), "Prénom")
    nom_col = next((h for h in headers if "nom" in h.lower() and "organisation" not in h.lower() and "campagne" not in h.lower()), None)
    prenom_col = next((h for h in headers if "prénom" in h.lower() or "prenom" in h.lower()), None)
    return nom_col, prenom_col

# --- MAIN ---
def main():
    timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%M")
    output_file = REPORT_DIR / f"Audit_Resultats_{timestamp}.txt"
    lines_buffer = []

    def log(msg):
        print(msg)
        lines_buffer.append(msg)

    log(f"🕵️‍♂️ AUDIT INTELLIGENT AVEC SUGGESTIONS ({timestamp})")
    log(f"📂 Sortie : {output_file}")
    log("="*60)

    # 1. Chargement Secret
    secret_keys = set()
    secret_database = [] 
    rows = read_csv_smart(FILES["SECRET"])
    
    if not rows:
        log("❌ Erreur critique : SECRET_correspondance.csv introuvable ou illisible.")
        return

    for row in rows:
        clean = {k.strip().lower(): v for k, v in row.items()}
        n_raw, p_raw = clean.get("nom"), clean.get("prenom") or clean.get("prénom")
        if n_raw and p_raw:
            n_norm = normalize_text(n_raw)
            p_norm = normalize_text(p_raw)
            secret_keys.add((n_norm, p_norm))
            secret_keys.add((p_norm, n_norm))
            secret_database.append({'nom': n_norm, 'prenom': p_norm})

    log(f"✅ SECRET : {len(rows)} étudiants chargés.")
    log("="*60)

    # 2. Vérification
    targets = [
        ("⚡ Voltaire Initial", FILES["VOLTAIRE_INIT"]),
        ("⚡ Voltaire Final  ", FILES["VOLTAIRE_FINAL"]),
        ("✍️  Ecri+ Initial   ", FILES["ECRIPLUS_INIT"]),
        ("✍️  Ecri+ Final     ", FILES["ECRIPLUS_FINAL"]),
    ]

    for title, filepath in targets:
        log(f"\n📂 {title}")
        rows = read_csv_smart(filepath)
        if not rows: 
            log("   ⚠️  Fichier non trouvé ou vide.")
            continue

        headers = list(rows[0].keys())
        col_nom, col_prenom = get_name_columns(headers)
        
        if not col_nom or not col_prenom:
            log(f"   ❌ Colonnes Nom/Prénom introuvables.")
            continue

        found = 0
        missing_details = []
        
        for i, row in enumerate(rows):
            nom_val = row.get(col_nom, "").strip()
            prenom_val = row.get(col_prenom, "").strip()
            if not nom_val or not prenom_val: continue 

            n_norm = normalize_text(nom_val)
            p_norm = normalize_text(prenom_val)
            key = (n_norm, p_norm)
            
            if key in secret_keys:
                found += 1
                log(f"   ✅ Ligne {i+1}: '{nom_val}' '{prenom_val}' -> MATCH")
            else:
                suggestion = get_suggestion(n_norm, p_norm, secret_database)
                msg = f"   ❌ Ligne {i+1}: '{nom_val}' '{prenom_val}'\n      👉 {suggestion}"
                log(msg)
                missing_details.append(msg)

        log("-" * 20)
        log(f"   📊 {found} trouvés / {len(missing_details)} suspects")

    # 3. Ecriture fichier
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines_buffer))
        print(f"\n✅ Rapport sauvegardé avec succès dans : {output_file}")
    except Exception as e:
        print(f"\n❌ Erreur écriture rapport : {e}")

if __name__ == "__main__":
    main()