import csv
import os
import difflib
import unicodedata
from pathlib import Path
from typing import Tuple, List, Dict

DATA_DIR = Path("/data")
OUTPUT_FILE = Path("/app/audit_resultats.txt")

FILES = {
    "SECRET": DATA_DIR / "SECRET_correspondance.csv",
    "VOLTAIRE_INIT": DATA_DIR / "results/voltaire_initial.csv",
    "VOLTAIRE_FINAL": DATA_DIR / "results/voltaire_final.csv",
    "ECRIPLUS_INIT": DATA_DIR / "results/ecriplus_initial.csv",
    "ECRIPLUS_FINAL": DATA_DIR / "results/ecriplus_final.csv"
}

def log(message):
    print(message)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def normalize_text(text):
    if not text: return ""
    text = unicodedata.normalize('NFD', text)
    text = "".join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.strip().lower().replace("-", " ").replace("_", " ")
    return " ".join(text.split())

def get_suggestion(target_nom, target_prenom, secret_database):
    """
    Cherche la cause de l'erreur :
    1. Inclusion (Nom composé manquant/ajouté)
    2. Ressemblance (Faute de frappe)
    """
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
    if not path.exists():
        log(f"⚠️ Fichier introuvable : {path}")
        return []
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

if OUTPUT_FILE.exists(): os.remove(OUTPUT_FILE)

log(f"🕵️‍♂️ AUDIT INTELLIGENT AVEC SUGGESTIONS (Liste complète)")
log("="*60)

secret_keys = set()
secret_database = [] 

rows = read_csv_smart(FILES["SECRET"])
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

targets = [
    ("⚡ Voltaire Initial", FILES["VOLTAIRE_INIT"]),
    ("⚡ Voltaire Final  ", FILES["VOLTAIRE_FINAL"]),
    ("✍️  Ecri+ Initial   ", FILES["ECRIPLUS_INIT"]),
    ("✍️  Ecri+ Final     ", FILES["ECRIPLUS_FINAL"]),
]

for title, filepath in targets:
    log(f"\n📂 {title}")
    rows = read_csv_smart(filepath)
    if not rows: continue

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

log("\n" + "="*60)
log(f"📝 Rapport : {OUTPUT_FILE}")