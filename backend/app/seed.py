import csv
import difflib
import sys
import os
import uuid
import logging
import re
import argparse
from pathlib import Path
from typing import Dict, Optional, Tuple
from tqdm import tqdm
from sqlmodel import Session, select, text

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.database import engine, init_db
from app.models import (
    AssessmentResult, AssessmentType, Platform, Student, Dictation, Submission, Mistake, 
    CSP, Degree, ReadingSupport, Library
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))

SECRET_CSV_PATH = DATA_DIR / "SECRET_correspondance.csv"

SURVEY_CSV_PATH = DATA_DIR / "Enquête des antécédants 2024+2026.csv"

DICTATES_DIR = DATA_DIR / "dictates"
TEACHER_FILENAME = "GRAZIANO_Emmanuelle_graziaem.txt"

WAVES = [
    { "folder": "data-initial", "suffix": "Initiale" },
    { "folder": "data-final", "suffix": "Finale" }
]

DICTATION_BASE_TITLE = "Dictées Étude Rousseau"

CSV_COLS = {
    "nom": "15. nom",
    "prenom": "16. prenom",
    "td": "17. td",
    "biblio": "14. bibliotheque",
    "support": "4. support",
    "oeuvres": "2. oeuvres",
    "motif": "3. motif",
    "appetence": "1. Comment_evaluez-vous_votre_gout_personne",
    "niveau_declare": "5. niveau",
    "p1_dip": "10. diplome_parent_1",
    "p1_csp": "12. CSP_parent1",
    "p2_dip": "11. diplome_parent_2",
    "p2_csp": "13. CSP_parent2"
}

FILENAME_PATTERN = re.compile(r'^(?P<nom>[^_]+)_(?P<prenom>[^_]+)(?:_.*)?\.txt$')

RESULTS_DIR = DATA_DIR / "results"

VOLTAIRE_FILES = {
    AssessmentType.INITIAL: "voltaire_initial.csv",
    AssessmentType.FINAL: "voltaire_final.csv"
}
ECRIPLUS_FILES = {
    AssessmentType.INITIAL: "ecriplus_initial.csv",
    AssessmentType.FINAL: "ecriplus_final.csv"
}

ECRIPLUS_MAP = {
    "score_articuler": ["articuler les termes"],
    "score_construire": ["construire ses phrases"],
    "score_orthographe": ["orthographe grammaticale"],
    "score_vocabulaire": ["effets de style", "vocabulaire"]
}

def clean_float(value: str) -> float:
    """Convertit '0,88', '43 %', '40 %' en float 0.0-1.0."""
    if not value: 
        return 0.0
    v = str(value).replace(",", ".").replace("%", "").strip()
    try:
        f = float(v)
        if f > 1.0: 
            return f / 100.0
        return f
    except ValueError:
        return 0.0
    
def normalize_name(text):
    if not text: return ""
    text = text.strip().lower().replace("-", " ").replace("_", " ")
    return " ".join(text.split())

def find_student_id(session, nom: str, prenom: str, uuid_map: Dict) -> Optional[int]:
    """
    Cherche un étudiant de manière intelligente (Exacte -> Inversée -> Floue).
    """
    if not nom or not prenom: return None

    n_nom = normalize_name(nom)
    n_prenom = normalize_name(prenom)
    
    # Tentative Exacte.
    key = (n_nom, n_prenom)
    uuid_str = uuid_map.get(key)

    # Tentative Inversée (Si le CSV a inversé Nom/Prénom).
    if not uuid_str:
        uuid_str = uuid_map.get((n_prenom, n_nom))
        if uuid_str:
            logger.info(f"   🔄 Inversion détectée pour : {nom} {prenom}")

    # Tentative Floue (Fuzzy Matching).
    if not uuid_str:
        candidates = {f"{k[0]} {k[1]}": k for k in uuid_map.keys()}
        
        target = f"{n_nom} {n_prenom}"
        matches = difflib.get_close_matches(target, candidates.keys(), n=1, cutoff=0.80)
        
        if matches:
            best_match_str = matches[0]
            best_key = candidates[best_match_str]
            uuid_str = uuid_map[best_key]
            
            logger.warning(f"   🪄 Autocorrection : '{nom} {prenom}' -> '{best_key[0]} {best_key[1]}' (Score élevé).")

    if not uuid_str:
        logger.debug(f"   ❌ Introuvable : {nom} {prenom}.")
        return None
        
    try:
        res = session.exec(select(Student.id).where(Student.anonymous_id == uuid.UUID(uuid_str))).first()
        return res
    except:
        return None

def print_diagnostic():
    logger.info(f"🔍 Diagnostic de l'environnement de données :")
    logger.info(f"   -> DATA_DIR = {DATA_DIR} ({'✅ Présent' if DATA_DIR.exists() else '❌ Absent'})")
    logger.info(f"   -> DICTATES_DIR = {DICTATES_DIR} ({'✅ Présent' if DICTATES_DIR.exists() else '❌ Absent'})")

    if DICTATES_DIR.exists():
        files = list(DICTATES_DIR.iterdir())
        logger.info(f"   -> Contenu de DICTATES_DIR : {[f.name for f in files]}")
    else:
        logger.error("   ❌ Le dossier 'dictates' est introuvable dans /data !")

def read_file_safely(file_path: Path) -> str:
    """Lit un fichier en essayant différentes encodages."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"❌ Erreur lors de la lecture du fichier {file_path} : {e}")
        return ""

def get_enum_value(enum_class, value: str):
    """
    Tente de convertir une chaîne CSV en Enum.
    Si la valeur ne correspond pas exactement, renvoie None.
    """
    if not value or not value.strip():
        return None
    
    clean_value = value.strip()
    
    # Tentative 1 : Correspondance exacte.
    try:
        return enum_class(clean_value)
    except ValueError:
        pass
        
    # Tentative 2 : Gestion des cas particuliers (espaces, casse...).
    for member in enum_class:
        if member.value.lower() == clean_value.lower():
            return member
            
    logger.warning(f"⚠️ Attention : Valeur '{clean_value}' inconnue pour {enum_class.__name__}")
    return None

def load_uuid_map() -> Dict[Tuple[str, str], str]:
    """
    Charge le fichier de correspondance pour garantir la pseudonymisation constante.
    Retourne un dictionnaire : {(nom_lower, prenom_lower): 'UUID_STRING'}
    """
    mapping = {}
    
    if not SECRET_CSV_PATH.exists():
        logger.error(f"⚠️  ATTENTION : Fichier de correspondance introuvable : {SECRET_CSV_PATH}")
        return mapping

    logger.info(f"🔑 Chargement de la table de correspondance : {SECRET_CSV_PATH.name}")

    encodings = ['utf-8-sig', 'cp1252', 'latin-1', 'utf-8']
    
    for encoding in encodings:
        try:
            with open(SECRET_CSV_PATH, mode="r", encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=";") 

                if not reader.fieldnames:
                    logger.error(f"❌ Le fichier de correspondance est vide ou mal formaté avec l'encodage {encoding}.")
                    return mapping
                
                headers = [h.lower() for h in reader.fieldnames]
                required = ["nom", "prenom", "uuid"]

                if not any('nom' in h for h in headers):
                    logger.warning(f"⚠️ Colonnes suspectes avec {encoding} : {reader.fieldnames}.")
                    continue
                
                count = 0
                for row in reader:
                    clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                    nom = clean_row.get("nom")
                    prenom = clean_row.get("prenom") or clean_row.get("prénom")
                    uuid_val = clean_row.get("uuid") or clean_row.get("uuid4")

                    if nom and prenom and uuid_val:
                        key = (nom.lower(), prenom.lower())
                        mapping[key] = uuid_val
                        count += 1

                if count > 0:
                    logger.info(f"✅ SUCCÈS : {count} identités chargées avec l'encodage '{encoding}'.")
                    return mapping
                else:
                    logger.warning(f"⚠️ Fichier lu avec {encoding} mais aucune donnée valide trouvée.")

        except UnicodeDecodeError:
            logger.warning(f"⚠️ Échec de la lecture avec l'encodage {encoding}, tentative suivante...")
            continue
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors de la lecture du fichier de correspondance avec {encoding} : {e}")
            return {}
        
    logger.error("❌ Échec de la lecture du fichier de correspondance avec tous les encodages.")
    return mapping

def seed_students(session: Session, uuid_map: Dict):
    """Lit l'enquête et importe les étudiants en utilisant l'UUID map."""
    if not SURVEY_CSV_PATH.exists():
        logger.error(f"❌ Erreur : Le fichier d'enquête est introuvable ici : {SURVEY_CSV_PATH}")
        return
    
    existing_uuids = set(session.exec(select(Student.anonymous_id)).all())
    
    logger.info(f"📂 Lecture du fichier : {SURVEY_CSV_PATH}")
    
    try:
        with open(SURVEY_CSV_PATH, mode="r", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f, delimiter=";"))
            count = 0

            for row in tqdm(rows, desc="Importing Students"):
                nom = row.get(CSV_COLS["nom"], "").strip()
                prenom = row.get(CSV_COLS["prenom"], "").strip()

                if not nom or not prenom:
                    continue

                key = (normalize_name(nom), normalize_name(prenom))
                uuid_str = uuid_map.get(key)

                if uuid_str:
                    try:
                        student_uuid = uuid.UUID(uuid_str)
                    except ValueError:
                        logger.warning(f"⚠️ UUID invalide dans la correspondance pour : {nom} {prenom}.")
                        continue
                else:
                    student_uuid = uuid.uuid4()
                    logger.debug(f"⚠️  Nouveau UUID généré pour : {nom} {prenom}")

                if student_uuid in existing_uuids:
                    logger.debug(f"ℹ️ Étudiant déjà existant (ignoré) : {nom} {prenom}")
                    continue

                student = Student(
                    anonymous_id=student_uuid,
                    td_group=row.get(CSV_COLS["td"], "Inconnu"),
                    
                    has_library=get_enum_value(Library, row.get(CSV_COLS["biblio"])),
                    reading_support=get_enum_value(ReadingSupport, row.get(CSV_COLS["support"])),
                    
                    reading_works=row.get(CSV_COLS["oeuvres"]),
                    motive=row.get(CSV_COLS["motif"]),
                    appetence_level=row.get(CSV_COLS["appetence"]),
                    declared_level=row.get(CSV_COLS["niveau_declare"]),
                    
                    parent_1_degree=get_enum_value(Degree, row.get(CSV_COLS["p1_dip"])),
                    parent_1_csp=get_enum_value(CSP, row.get(CSV_COLS["p1_csp"])),
                    parent_2_degree=get_enum_value(Degree, row.get(CSV_COLS["p2_dip"])),
                    parent_2_csp=get_enum_value(CSP, row.get(CSV_COLS["p2_csp"])),
                )
                
                session.add(student)
                existing_uuids.add(student_uuid)
                count += 1

            logger.info(f"💾 Enregistrement des étudiants en base de données... ({count} étudiants ajoutés).")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'importation des étudiants : {e}")
        raise e
    
def seed_results_unified(session: Session, uuid_map: Dict):
    logger.info("📊 Importation Résultats Unifiés...")
    
    # --- VOLTAIRE ---
    for type_enum, fname in VOLTAIRE_FILES.items():
        fpath = RESULTS_DIR / fname
        if not fpath.exists(): continue
        
        count = 0
        try:
            with open(fpath, 'r', encoding='utf-8-sig') as f:
                # Détection délimiteur (virgule ou point-virgule)
                dialect = csv.Sniffer().sniff(f.read(1024))
                f.seek(0)
                reader = csv.DictReader(f, dialect=dialect)
                
                for row in reader:
                    # Nettoyage header
                    row = {k.strip().lower(): v for k, v in row.items() if k}
                    
                    nom = row.get('nom')
                    prenom = row.get('prénom') or row.get('prenom')
                    if not nom or not prenom: continue
                    
                    sid = find_student_id(session, nom, prenom, uuid_map)
                    if not sid: continue

                    # Recherche Score et Durée (Logique floue selon colonnes)
                    score_val = 0.0
                    details = {}
                    
                    for k, v in row.items():
                        # Score
                        if "score" in k:
                            # Priorité au type courant
                            if (type_enum == AssessmentType.FINAL and "final" in k) or \
                               (type_enum == AssessmentType.INITIAL and "initial" in k) or \
                               ("score" in k and score_val == 0.0):
                                score_val = clean_float(v)
                        
                        # Durée / Temps
                        if "temps" in k or "durée" in k:
                            details["duration"] = v
                        
                        # Niveau
                        if "niveau" in k:
                            details["level"] = v

                    # Upsert (Insert si n'existe pas)
                    exists = session.exec(select(AssessmentResult).where(
                        AssessmentResult.student_id == sid,
                        AssessmentResult.platform == Platform.VOLTAIRE,
                        AssessmentResult.type == type_enum
                    )).first()
                    
                    if not exists:
                        res = AssessmentResult(
                            student_id=sid,
                            platform=Platform.VOLTAIRE,
                            type=type_enum,
                            score=score_val,
                            details=details
                        )
                        session.add(res)
                        count += 1
            logger.info(f"   ⚡ Voltaire {type_enum.value}: {count} importés.")
        except Exception as e:
            logger.error(f"   ❌ Erreur Voltaire {fname}: {e}")

    # --- ECRI+ ---
    for type_enum, fname in ECRIPLUS_FILES.items():
        fpath = RESULTS_DIR / fname
        if not fpath.exists(): continue
        
        count = 0
        try:
            with open(fpath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                
                # Mapping dynamique des colonnes
                col_map = {}
                headers = [h.lower() for h in reader.fieldnames or []]
                
                # Trouve la colonne Global
                for h in reader.fieldnames:
                    if "ensemble" in h.lower() and "%" in h:
                        col_map["global"] = h
                        break
                
                # Trouve les sous-compétences
                for key, keywords in ECRIPLUS_MAP.items():
                    for h in reader.fieldnames:
                        h_low = h.lower()
                        if any(kw in h_low for kw in keywords) and "%" in h:
                            col_map[key] = h
                            break

                for row in reader:
                    nom = row.get("Nom du Participant") or row.get("Nom")
                    prenom = row.get("Prénom du Participant") or row.get("Prénom")
                    if not nom or not prenom: continue
                    
                    sid = find_student_id(session, nom, prenom, uuid_map)
                    if not sid: continue

                    exists = session.exec(select(AssessmentResult).where(
                        AssessmentResult.student_id == sid,
                        AssessmentResult.platform == Platform.ECRIPLUS,
                        AssessmentResult.type == type_enum
                    )).first()
                    
                    if not exists:
                        # Score Global
                        score_col = col_map.get("global")
                        global_score = clean_float(row.get(score_col)) if score_col else 0.0
                        
                        # Détails (Sous-scores)
                        details = {}
                        for k, col in col_map.items():
                            if k != "global":
                                details[k] = clean_float(row.get(col))

                        res = AssessmentResult(
                            student_id=sid,
                            platform=Platform.ECRIPLUS,
                            type=type_enum,
                            score=global_score,
                            details=details
                        )
                        session.add(res)
                        count += 1
            logger.info(f"   ✍️ Ecri+ {type_enum.value}: {count} importés.")
        except Exception as e:
            logger.error(f"   ❌ Erreur Ecri+ {fname}: {e}")
    
def seed_dictation_files(session: Session, uuid_map: Dict):
    """
    Lit les fichiers .txt dans /data/dictates.
    1. Crée la Dictée de référence (Mme Graziano).
    2. Crée les Submissions pour les étudiants trouvés.
    """
    if not DICTATES_DIR.exists():
        logger.warning(f"Dossier dictées introuvable : {DICTATES_DIR}")
        return

    logger.info(f"Traitement des dictées dans : {DICTATES_DIR}")

    teacher_path = DICTATES_DIR / TEACHER_FILENAME
    if not teacher_path.exists():
        logger.error(f"❌ Erreur critique : Le fichier enseignant {TEACHER_FILENAME} est absent !")
        return
    
    content_ref = read_file_safely(teacher_path)

    all_students = session.exec(select(Student)).all()
    student_lookup = {s.anonymous_id: s.id for s in all_students}

    total_added = 0

    for wave in WAVES:
        folder_name = wave["folder"]
        suffix = wave["suffix"]
        wave_dir = DICTATES_DIR / folder_name

        logger.info(f"\n📂 Traitement de la vague '{suffix}' dans le dossier : {wave_dir}")
        if not wave_dir.exists():
            logger.warning(f"⚠️ Dossier de vague introuvable : {wave_dir} (attendu pour la vague '{suffix}').")
            continue

        full_title = f"{DICTATION_BASE_TITLE} ({suffix})"
        dictation = session.exec(select(Dictation).where(Dictation.title == full_title)).first()

        if not dictation:
            dictation = Dictation(
                title=full_title,
                content_reference=content_ref,
                rules_config={"DEFAULT": 1.0}
            )
            session.add(dictation)
            session.flush()
            session.refresh(dictation)
            logger.info(f"✅ Dictée de référence créée {full_title} (ID: {dictation.id}).")
        else:
            logger.info(f"ℹ️ La dictée {full_title} existe déjà (ID: {dictation.id}).")

        existing_submissions = { 
            (sub.student_id, sub.dictation_id) 
            for sub in session.exec(select(Submission).where(Submission.dictation_id == dictation.id)).all()
        }

        txt_files = list(wave_dir.glob("*.txt"))
        wave_added = 0
        wave_missing = 0

        logger.info(f"📂 Importation des copies étudiantes pour '{suffix}'... ({len(txt_files)} fichiers à traiter).")

        for file_path in tqdm(txt_files, desc=f"Importing Submissions for {suffix} Wave."):
            if file_path.name == TEACHER_FILENAME:
                continue

            match = FILENAME_PATTERN.match(file_path.name)
            if not match:
                logger.warning(f"⚠️ Format de fichier invalide (ignoré) : {file_path.name}")
                continue

            nom_file = match.group("nom")
            prenom_file = match.group("prenom")

            key = (nom_file.lower(), prenom_file.lower())
            uuid_str = uuid_map.get(key)

            if not uuid_str:
                logger.debug(f"⚠️ Étudiant introuvable dans le mapping : {file_path.name}")
                wave_missing += 1
                continue

            try:
                target_uuid = uuid.UUID(uuid_str)
            except ValueError:
                logger.warning(f"⚠️ UUID invalide dans le mapping : {uuid_str}")
                wave_missing += 1
                continue

            student_id = student_lookup.get(target_uuid)
            if not student_id:
                logger.warning(f"⚠️ Étudiant {file_path.name} a un UUID mais n'est pas en base.")
                wave_missing += 1
                continue

            if (student_id, dictation.id) in existing_submissions:
                logger.debug(f"ℹ️ Copie déjà existante (ignorée) : {file_path.name}")
                continue

            content = read_file_safely(file_path)
            sub = Submission(
                student_id=student_id,
                dictation_id=dictation.id,
                content_student=content,
                scores={}
            )
            session.add(sub)
            wave_added += 1

        total_added += wave_added
        logger.info(f"✅ Vague '{suffix}' : {wave_added} nouvelles copies ajoutées, {wave_missing} fichiers ignorés (étudiants non reconnus).")

    logger.info(f"🎉 Importation des dictées terminée : {total_added} nouvelles copies ajoutées au total.")

def reset_database(session: Session):
    """Supprime toutes les données des tables principales."""
    logger.warning("☢️ Réinitialisation complète de la base de données en cours...")
    try:
        session.exec(text("TRUNCATE TABLE mistakes, submissions, students, dictations RESTART IDENTITY CASCADE;"))
        session.commit()
        logger.info("♻️ Base de données réinitialisée.")
    except Exception as e:
        logger.error(f"❌ Échec de la réinitialisation de la base de données : {e}")
        session.rollback()
        raise e

def main():
    parser = argparse.ArgumentParser(description="Script d'importation des données initiales.")
    parser.add_argument("--reset-db", action="store_true", help="Réinitialiser la base de données avant l'importation.")
    args = parser.parse_args()

    print_diagnostic()

    logger.info("🚀 Initialisation de la base de données...")
    init_db()

    try:
        with Session(engine) as session:
            if args.reset_db:
                reset_database(session)

            uuid_map = load_uuid_map()
            if uuid_map:
                logger.info(f"🔑 {len(uuid_map)} correspondances chargées pour la pseudonymisation.")
                seed_students(session, uuid_map)
                seed_results_unified(session, uuid_map)
                seed_dictation_files(session, uuid_map)
                session.commit()
                print("🎉 Importation terminée avec succès !")
            else:
                logger.error("❌ Aucune correspondance chargée, l'importation a été annulée pour éviter les incohérences.")
    except Exception as e:
        logger.error(f"❌ Échec de l'importation : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()