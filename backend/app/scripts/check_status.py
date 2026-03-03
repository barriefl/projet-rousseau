import csv
import unicodedata
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# --- CONFIGURATION. ---
DATA_DIR = Path("/data")
REPORT_DIR = DATA_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)

FILES = {
    "SECRET": DATA_DIR / "SECRET_correspondance.csv",
    "DICTATES_DIR": DATA_DIR / "dictates",
    "VOLTAIRE_INIT": DATA_DIR / "results/voltaire_initial.csv",
    "VOLTAIRE_FINAL": DATA_DIR / "results/voltaire_final.csv",
    "ECRIPLUS_INIT": DATA_DIR / "results/ecriplus_initial.csv",
    "ECRIPLUS_FINAL": DATA_DIR / "results/ecriplus_final.csv"
}

# --- FONCTIONS UTILITAIRES. ---

def normalize(text):
    if not text: return ""
    text = unicodedata.normalize('NFD', text)
    text = "".join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.strip().lower().replace("-", " ").replace("_", " ")
    return " ".join(text.split())

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

def get_name_cols(headers: List[str]) -> Tuple[str, str]:
    headers_map = {h.lower(): h for h in headers}
    if "nom du participant" in headers_map:
        return headers_map["nom du participant"], headers_map.get("prénom du participant", "Prénom du Participant")
    if "nom" in headers_map:
        return headers_map["nom"], next((h for h in headers if "prénom" in h.lower() or "prenom" in h.lower()), "Prénom")
    return None, None

def get_requirements(group: str) -> List[str]:
    """Retourne la liste des tâches obligatoires pour un groupe donné."""
    reqs = ["dictee_init", "dictee_final"]
    
    g = group.upper().strip() if group else ""
    
    if g in ["G1", "G2", "G3", "G4"]:
        reqs.extend(["voltaire_init", "voltaire_final"])
    elif g == "G5":
        reqs.extend(["ecriplus_init", "ecriplus_final"])
    elif g == "G0":
        pass
    else:
        pass 
        
    return reqs

# --- MAIN. ---

def main():
    timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%M")
    report_file = REPORT_DIR / f"Bilan_Avancement_{timestamp}.txt"
    
    lines_buffer = []
    
    def log(msg):
        print(msg)
        lines_buffer.append(msg)

    log(f"🚀 GÉNÉRATION DU RAPPORT D'AVANCEMENT ({timestamp})")
    log(f"📂 Sortie : {report_file}\n")

    students = {}
    rows = read_csv_smart(FILES["SECRET"])
    
    if not rows:
        log("❌ Erreur : Impossible de lire SECRET_correspondance.csv")
        return

    for row in rows:
        clean = {k.strip().lower(): v for k, v in row.items()}
        n_raw = clean.get("nom")
        p_raw = clean.get("prenom") or clean.get("prénom")
        
        g_raw = clean.get("groupe") or clean.get("group") or clean.get("td") or "?"
        
        if n_raw and p_raw:
            key = (normalize(n_raw), normalize(p_raw))
            students[key] = {
                "display": f"{n_raw} {p_raw}",
                "group": g_raw.upper(),
                "tasks_done": {
                    "dictee_init": False, "dictee_final": False,
                    "voltaire_init": False, "voltaire_final": False,
                    "ecriplus_init": False, "ecriplus_final": False
                }
            }

    log(f"✅ {len(students)} étudiants chargés.\n")

    for f in FILES["DICTATES_DIR"].rglob("*.txt"):
        if "GRAZIANO" in f.name: continue
        parts = f.stem.split('_')
        if len(parts) >= 2:
            key = (normalize(parts[0]), normalize(parts[1]))
            if key not in students:
                key = (normalize(parts[1]), normalize(parts[0]))
            
            if key in students:
                is_final = "final" in f.parent.name.lower() or "final" in f.name.lower()
                task_key = "dictee_final" if is_final else "dictee_init"
                students[key]["tasks_done"][task_key] = True

    targets = [
        ("voltaire_init", FILES["VOLTAIRE_INIT"]),
        ("voltaire_final", FILES["VOLTAIRE_FINAL"]),
        ("ecriplus_init", FILES["ECRIPLUS_INIT"]),
        ("ecriplus_final", FILES["ECRIPLUS_FINAL"]),
    ]

    for task_name, path in targets:
        rows = read_csv_smart(path)
        if not rows: continue
        col_nom, col_prenom = get_name_cols(list(rows[0].keys()))
        if not col_nom: continue

        for row in rows:
            n, p = row.get(col_nom, ""), row.get(col_prenom, "")
            if not n or not p: continue
            
            key = (normalize(n), normalize(p))
            if key not in students:
                key = (normalize(p), normalize(n))
                
            if key in students:
                students[key]["tasks_done"][task_name] = True

    missing_global_count = 0
    
    header = "{:<4} | {:<30} | {:<7} | {:<7} | {:<7} | {:<7} | {:<7} | {:<7}".format(
        "GRP", "ÉTUDIANT", "D.Init", "D.Fin", "V.Init", "V.Fin", "E.Init", "E.Fin"
    )
    separator = "-" * 105
    
    log(header)
    log(separator)

    sorted_students = sorted(students.items(), key=lambda x: (x[1]['group'], x[1]['display']))

    for key, data in sorted_students:
        group = data["group"]
        done = data["tasks_done"]
        required = get_requirements(group)
        
        is_student_complete = True
        row_cells = []
        
        columns_order = [
            "dictee_init", "dictee_final",
            "voltaire_init", "voltaire_final",
            "ecriplus_init", "ecriplus_final"
        ]

        for task in columns_order:
            if task in required:
                if done[task]:
                    row_cells.append("✅")
                else:
                    row_cells.append("❌")
                    is_student_complete = False
            else:
                if done[task]:
                    row_cells.append("🆗")
                else:
                    row_cells.append("➖")

        if not is_student_complete:
            missing_global_count += 1

        row_str = "{:<4} | {:<30} | {:<7} | {:<7} | {:<7} | {:<7} | {:<7} | {:<7}".format(
            group[:4],
            data["display"][:30],
            *row_cells
        )
        log(row_str)

    log(separator)
    
    if missing_global_count == 0:
        log("🎉 TOUT EST COMPLET ! Tous les étudiants ont fait leurs devoirs respectifs.")
    else:
        log(f"⚠️  {missing_global_count} étudiants incomplets (sur {len(students)}).")
        log("   Légende : ✅=Fait, ❌=Manquant, ➖=Non requis, 🆗=Fait (Bonus)")

    try:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines_buffer))
        print(f"\n✅ Rapport sauvegardé : {report_file}")
    except Exception as e:
        print(f"\n❌ Erreur sauvegarde : {e}")

if __name__ == "__main__":
    main()