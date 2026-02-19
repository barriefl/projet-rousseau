import csv
from dataclasses import dataclass, field
import difflib
import socket
import sys
import os
import uuid
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from tqdm import tqdm
from sqlmodel import Session, select, text
from sqlmodel import SQLModel
from app.database import engine
from app.services.correction_service import CorrectionService

os.environ['NO_PROXY'] = '127.0.0.1,localhost'

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.database import engine, init_db
from app.models import (
    AssessmentResult, AssessmentType, GradingScale, Group, MistakeType, Platform, Rule, Student, Dictation, Submission, Mistake, 
    CSP, Degree, ReadingSupport, Library
)
from app.utils.crypto import encrypt_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION. ---

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
DICTATES_DIR = DATA_DIR / "dictates"
RESULTS_DIR = DATA_DIR / "results"

FILES = {
    "SECRET": DATA_DIR / "SECRET_correspondance.csv",
    "SURVEY": DATA_DIR / "Enquête des antécédants 2024+2026.csv",
    "TEACHER": DICTATES_DIR / "GRAZIANO_Emmanuelle_graziaem.txt",
    "VOLTAIRE_INIT": RESULTS_DIR / "voltaire_initial.csv",
    "VOLTAIRE_FINAL": RESULTS_DIR / "voltaire_final.csv",
    "ECRIPLUS_INIT": RESULTS_DIR / "ecriplus_initial.csv",
    "ECRIPLUS_FINAL": RESULTS_DIR / "ecriplus_final.csv"
}

VOLTAIRE_COLS = {
    AssessmentType.INITIAL: {
        "score": "score évaluation initiale",
        "details": {
            "temps_initial": "temps évaluation initiale"
        }
    },
    AssessmentType.FINAL: {
        "score": "score évaluation evaluation finale",
        "details": {
            "temps_total": "temps total passé",
            "duree_entrainement": "durée d'entraînement",
            "niveau_atteint": "niveau atteint",
            "progres": "progrès",
            "tests_blancs": "variante tests blancs mensuels"
        }
    }
}

ECRIPLUS_COLS = {
    "global": ["% maitrise de l'ensemble", "% maîtrise de l'ensemble"],
    "details": {
        "score_articuler": ["articuler les termes"],
        "score_construire": ["construire ses phrases"],
        "score_orthographe_grammaticale": ["orthographe grammaticale"],
        "score_conjugaison": ["marques de la conjugaison"],
        "score_point_de_vue": ["points de vue adoptés"],
        "score_effets_de_style": ["effets de style"],
        "score_expression": ["ses mots et ses expressions"],
        "score_comprehension": ["comprendre les mots"],
        "score_vocabulaire": ["développer un vocabulaire étendu"],
        "score_orthographe_lexicale": ["orthographe des mots"],
        "score_enchainement": ["enchaîner les phrases"],
        "score_organisation": ["organiser ses textes"],
        "score_reprise": ["utiliser des reprises"],
        "score_domaine_phrase": ["domaine de la phrase"],
        "score_domaine_discours": ["domaine du discours"],
        "score_domaine_mot": ["domaine du mot"],
        "score_domaine_texte": ["domaine du texte"]
    }
}

SURVEY_MAPPING = {
    "nom": "15. nom",
    "prenom": "16. prenom",
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

# --- STATISTIQUES. ---

@dataclass
class ImportStats:
    students_created: int = 0
    students_skipped: int = 0
    voltaire_imported: int = 0
    ecriplus_imported: int = 0
    dictations_imported: int = 0
    errors: List[str] = field(default_factory=list)

    def print_summary(self, dry_run: bool):
        print("\n" + "="*40)
        print(f"📊 RAPPORT D'IMPORTATION {'(DRY RUN)' if dry_run else ''}")
        print("="*40)
        print(f"👥 Étudiants   : {self.students_created} créés / {self.students_skipped} ignorés")
        print(f"⚡ Voltaire    : {self.voltaire_imported} résultats")
        print(f"✍️  Ecri+       : {self.ecriplus_imported} résultats")
        print(f"📝 Dictées     : {self.dictations_imported} copies")
        print("-" * 40)
        if self.errors:
            print(f"❌ {len(self.errors)} ERREURS RENCONTRÉES :")
            for e in self.errors[:10]:
                print(f"  - {e}")
            if len(self.errors) > 10: print("  ... (voir logs pour le reste)")
        else:
            print("✅ AUCUNE ERREUR DÉTECTÉE.")
        print("="*40 + "\n")

# --- FONCTIONS UTILITAIRES. ---

def normalize_text(text: str) -> str:
    """Nettoyage standard des chaînes (minuscule, sans accents/espaces superflus)."""
    if not text: 
        return ""
    text = text.strip().lower().replace("-", " ").replace("_", " ")
    return " ".join(text.split())

def clean_float(value: str) -> float:
    """
    Convertit en float normalisé (0.xx).
    Gère les %, les virgules et les valeurs négatives.
    Ex: "37%" -> 0.37 | "-4" -> -0.04 | "0,41" -> 0.41
    """
    if value is None:
        return None
    
    if isinstance(value, (int, float)):
        f = float(value)
        if abs(f) > 1.0:
            return f / 100.0
        return f
    
    val_str = str(value).strip()

    if not val_str or val_str.upper() in ["-", "ABS", "N/A", "NON NOTÉ", "None"]:
        return None
    
    has_percent = "%" in val_str
    
    clean_str = val_str.replace(",", ".").replace("%", "").strip()

    try:
        f = float(clean_str)
        if has_percent:
            return f/100.0

        if abs(f) > 1.0: 
            return f / 100.0
        
        return f
    except ValueError:
        return None
    
def get_enum_safe(enum_cls, value: str):
    """Tente de matcher un string avec un Enum (insensible à la casse)."""
    if not value: 
        return None
    val_clean = value.strip().lower()
    for member in enum_cls:
        if member.value.lower() == val_clean:
            return member
    return None

def find_col_by_keyword(headers: List[str], keyword: str) -> Optional[str]:
    """Trouve le nom exact d'une colonne contenant un mot-clé."""
    keyword = keyword.lower()
    for h in headers:
        if keyword in h.lower():
            return h
    return None

# --- SERVICES MÉTIERS. ---

class StudentService:
    def __init__(self, session: Session, stats: ImportStats, dry_run: bool = False):
        self.session = session
        self.stats = stats
        self.dry_run = dry_run
        self.uuid_map = self._load_uuid_map()
        self.student_cache: Dict[uuid.UUID, int] = {}
        self._refresh_cache()

    def _refresh_cache(self):
        """Met à jour le cache local des étudiants."""
        if self.dry_run:
            return
        students = self.session.exec(select(Student.id, Student.anonymous_id)).all()
        self.student_cache = {s.anonymous_id: s.id for s in students}
        logger.debug(f"🧠 Cache étudiant mis à jour : {len(self.student_cache)} entrées.")

    def _load_uuid_map(self) -> Dict[Tuple[str, str], Dict[str, str]]:
        """Charge le fichier SECRET_correspondance.csv."""
        mapping = {}
        path = FILES["SECRET"]
        if not path.exists():
            self.stats.errors.append(f"Fichier secret manquant: {FILES['SECRET']}")
            return mapping

        for encoding in ['utf-8-sig', 'cp1252', 'latin-1']:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    sample = f.read(1024)
                    f.seek(0)

                    try:
                        dialect = csv.Sniffer().sniff(sample, delimiters=[',', ';', '\t'])
                    except:
                        dialect = csv.Dialect
                        dialect.delimiter = ';' if ';' in sample else ','

                    reader = csv.DictReader(f, dialect=dialect)
                    headers = [h.lower() for h in reader.fieldnames or []]

                    if not any("nom" in h for h in headers):
                        continue
                    
                    for row in reader:
                        clean = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                        nom = clean.get("nom")
                        prenom = clean.get("prenom") or clean.get("prénom")
                        uuid_val = clean.get("uuid") or clean.get("uuid4")
                        group_val = clean.get("groupe") or clean.get("group")
                        promo_val = clean.get("promo")
                        
                        if nom and prenom and uuid_val:
                            data = {
                                "uuid": uuid_val, 
                                "group": group_val,
                                "promo": promo_val,
                                "nom": nom,
                                "prenom": prenom
                            }
                            
                            key = (normalize_text(nom), normalize_text(prenom))
                            mapping[key] = data

                            key = (normalize_text(prenom), normalize_text(nom))
                            mapping[key] = data
                    
                    if mapping:
                        logger.info(f"✅ Mapping chargé ({len(mapping)} entrées) avec {encoding} et délimiteur '{dialect.delimiter}'.")
                        return mapping
            except: 
                continue
        logger.error("❌ Impossible de lire le fichier de correspondance (aucun encodage/délimiteur ne fonctionne).")
        return mapping
    
    def get_student_id(self, nom: str, prenom: str) -> Optional[int]:
        """Récupère l'ID étudiant avec Fuzzy Matching (tolérance aux fautes)."""
        if not nom or not prenom: 
            return None
        
        n_nom, n_prenom = normalize_text(nom), normalize_text(prenom)
        
        # Match Exact.
        student_info = self.uuid_map.get((n_nom, n_prenom))
        
        # Match Inversé (Nom <-> Prénom).
        if not student_info:
            student_info = self.uuid_map.get((n_prenom, n_nom))

        # Match Flou (Fuzzy).
        if not student_info:
            candidates = {f"{k[0]} {k[1]}": k for k in self.uuid_map.keys()}
            target = f"{n_nom} {n_prenom}"
            matches = difflib.get_close_matches(target, candidates.keys(), n=1, cutoff=0.85)
            
            if matches:
                best_key = candidates[matches[0]]
                student_info = self.uuid_map[best_key]
                logger.debug(f"🪄 Correction: {nom} {prenom} -> {best_key}")

        if not student_info: 
            return None
        
        if self.dry_run:
            return 999999
        
        try:
            target_uuid = uuid.UUID(student_info["uuid"])
            return self.student_cache.get(target_uuid)
        except: 
            return None

    def import_survey(self):
        """Importe les étudiants depuis l'enquête."""
        path = FILES["SURVEY"]
        if not path.exists(): 
            return

        simulated_uuids = set()

        encodings = ['utf-8-sig', 'cp1252', 'latin-1']
        for encoding in encodings:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f, delimiter=';')

                    if not reader.fieldnames: 
                        continue

                    rows = list(reader)
                    for row in tqdm(rows, desc="Import Étudiants"):
                        nom = row.get(SURVEY_MAPPING["nom"])
                        prenom = row.get(SURVEY_MAPPING["prenom"])
                        
                        n_nom, n_prenom = normalize_text(nom), normalize_text(prenom)

                        student_info = self.uuid_map.get((n_nom, n_prenom))

                        if not student_info:
                            logger.info(f"⛔ Ignoré (Pas dans Secret) : {nom} {prenom}")
                            continue

                        uuid_str = str(uuid.uuid4())
                        group_str = None
                        promo_str = None
                        secret_nom = nom
                        secret_prenom = prenom

                        if student_info:
                            uuid_str = student_info["uuid"]
                            group_str = student_info["group"]
                            promo_str = student_info.get("promo")
                            secret_nom = student_info.get("nom", nom)
                            secret_prenom = student_info.get("prenom", prenom)

                        uid = uuid.UUID(uuid_str)
                        
                        if uid in self.student_cache or uid in simulated_uuids:
                            logger.warning(f"⚠️ DOUBLON DÉTECTÉ ET IGNORÉ : {nom} {prenom}")
                            self.stats.students_skipped += 1
                            continue

                        if not self.dry_run:
                            s = Student(
                                anonymous_id=uid,

                                first_name_encrypted=encrypt_text(secret_prenom),
                                last_name_encrypted=encrypt_text(secret_nom),
                                promo=promo_str,
                                group=get_enum_safe(Group, group_str),

                                has_library=get_enum_safe(Library, row.get(SURVEY_MAPPING["biblio"])),
                                reading_support=get_enum_safe(ReadingSupport, row.get(SURVEY_MAPPING["support"])),
                                reading_works=row.get(SURVEY_MAPPING["oeuvres"]),
                                motive=row.get(SURVEY_MAPPING["motif"]),
                                appetence_level=row.get(SURVEY_MAPPING["appetence"]),
                                declared_level=row.get(SURVEY_MAPPING["niveau_declare"]),

                                parent_1_degree=get_enum_safe(Degree, row.get(SURVEY_MAPPING["p1_dip"])),
                                parent_1_csp=get_enum_safe(CSP, row.get(SURVEY_MAPPING["p1_csp"])),
                                parent_2_degree=get_enum_safe(Degree, row.get(SURVEY_MAPPING["p2_dip"])),
                                parent_2_csp=get_enum_safe(CSP, row.get(SURVEY_MAPPING["p2_csp"])),
                            )
                            self.session.add(s)

                        simulated_uuids.add(uid)
                        self.stats.students_created += 1
                    break
            except UnicodeDecodeError:
                continue
        
        if not self.dry_run:
            self.session.commit()
            self._refresh_cache()

class AssessmentImporter:
    def __init__(self, session: Session, student_service: StudentService, stats: ImportStats, dry_run: bool):
        self.session = session
        self.student_service = student_service
        self.stats = stats
        self.dry_run = dry_run

    def _upsert_result(self, sid: int, platform: Platform, a_type: AssessmentType, score: float, details: dict):
        """Insère ou met à jour un résultat."""
        if self.dry_run: 
            return True

        existing = self.session.exec(select(AssessmentResult).where(
            AssessmentResult.student_id == sid,
            AssessmentResult.platform == platform,
            AssessmentResult.assessment_type == a_type
        )).first()

        if not existing:
            res = AssessmentResult(
                student_id=sid,
                platform=platform,
                assessment_type=a_type,
                score=score,
                details=details
            )
            self.session.add(res)
            return True
        return False
    
    def _read_csv_content(self, path: Path) -> List[Dict[str, str]]:
        """Lit un CSV avec détection automatique d'encodage et séparateur."""
        if not path.exists(): 
            logger.warning(f"⚠️ Fichier introuvable : {path}")
            return []

        encodings = ['utf-8-sig', 'utf-8', 'cp1252', 'latin-1']
        delimiters = [';', ',', '\t']
        
        for encoding in encodings:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    sample = f.read(4096)
                    f.seek(0)
                    
                    dialect = None
                    try:
                        dialect = csv.Sniffer().sniff(sample, delimiters=delimiters)
                    except:
                        for d in delimiters:
                            if d in sample:
                                dialect = csv.Dialect
                                dialect.delimiter = d
                                break
                    
                    if not dialect: 
                        continue

                    reader = csv.reader(f, delimiter=dialect.delimiter)

                    try:
                        headers = next(reader)
                    except StopIteration:
                        logger.warning(f"⚠️ Fichier vide : {path.name}")
                        return []
                    
                    new_headers = []
                    counts = {}

                    for h in headers:
                        h_clean = h.strip()
                        if h_clean in counts:
                            counts[h_clean] += 1
                            new_headers.append(f"{h_clean}_{counts[h_clean]}")
                        else:
                            counts[h_clean] = 1
                            new_headers.append(h_clean)

                    return [dict(zip(new_headers, row)) for row in reader]
            except (UnicodeDecodeError, csv.Error):
                continue
        
        logger.error(f"❌ Impossible de lire {path.name} (Encodage/Format inconnu).")
        return []
    
    def _get_col_name(self, headers: List[str], keywords: List[str]) -> Optional[str]:
        """Cherche une colonne correspondant aux mots-clés, en évitant les pièges."""
        normalized_headers = {h.lower(): h for h in headers}
        
        for kw in keywords:
            target = f"{kw} du participant"
            if target in normalized_headers:
                return normalized_headers[target]

        for kw in keywords:
            for h_clean, h_real in normalized_headers.items():
                if kw in h_clean:
                    if "nom" in kw and ("organisation" in h_clean or "campagne" in h_clean or "utilisateur" in h_clean):
                        continue
                    return h_real
        return None

    def import_voltaire(self):
        """Logique spécifique Voltaire."""
        configs = [
            (AssessmentType.INITIAL, FILES["VOLTAIRE_INIT"]),
            (AssessmentType.FINAL, FILES["VOLTAIRE_FINAL"])
        ]

        for a_type, path in configs:
            if not path.exists(): 
                continue
            count = 0
            
            try: 
                rows = self._read_csv_content(path)
                if not rows:
                    logger.warning(f"⚠️ Fichier vide ou illisible : {path.name}")
                    continue

                headers = list(rows[0].keys())
                config = VOLTAIRE_COLS[a_type] 
                
                col_score = find_col_by_keyword(headers, config["score"])
                col_details = {}
                for key, keyword in config["details"].items():
                    if key == "tests_blancs":
                        cols = [h for h in headers if keyword in h.lower()]
                        if cols: 
                            col_details[key] = cols
                    else:
                        col = find_col_by_keyword(headers, keyword)
                        if col: 
                            col_details[key] = col

                col_nom = self._get_col_name(headers, ["nom"])
                col_prenom = self._get_col_name(headers, ["prénom", "prenom"])

                for row in rows: 
                    nom = row.get(col_nom)
                    prenom = row.get(col_prenom)
                    
                    sid = self.student_service.get_student_id(nom, prenom)
                    if not sid: 
                        continue

                    score = clean_float(row.get(col_score)) if col_score else 0.0
                    
                    details = {}
                    for key, col_ref in col_details.items():
                        if key == "tests_blancs" and isinstance(col_ref, list):
                            tests = []
                            for c in col_ref:
                                val = clean_float(row.get(c))
                                if val is not None:
                                    tests.append(val)
                            if tests: 
                                details[key] = tests
                        else:
                            val = row.get(col_ref)
                            numeric_fields = ["score", "niveau_atteint", "progres"]
                            if key in numeric_fields:
                                clean_val = clean_float(val)
                                if clean_val is not None:
                                    details[key] = clean_val
                            elif val and val.strip(): 
                                details[key] = val.strip()

                    if self._upsert_result(sid, Platform.VOLTAIRE, a_type, score, details):
                        count += 1
            
                if not self.dry_run:
                    self.session.commit()
                self.stats.voltaire_imported += count
            except Exception as e:
                self.stats.errors.append(f"Erreur Voltaire {path.name}: {e}")

    def import_ecriplus(self):
        """Logique spécifique Ecri+."""
        configs = [
            (AssessmentType.INITIAL, FILES["ECRIPLUS_INIT"]),
            (AssessmentType.FINAL, FILES["ECRIPLUS_FINAL"])
        ]

        for a_type, path in configs:
            if not path.exists(): 
                continue
            count = 0

            try:
                rows = self._read_csv_content(path)
                if not rows:
                    logger.warning(f"⚠️ Fichier vide ou illisible : {path.name}")
                    continue

                headers = list(rows[0].keys())
                
                col_global = None
                for kw in ECRIPLUS_COLS["global"]:
                    col = find_col_by_keyword(headers, kw)
                    if col: 
                        col_global = col
                        break
                
                col_details = {}
                for key, keywords in ECRIPLUS_COLS["details"].items():
                    for kw in keywords:
                        col = next((h for h in headers if kw in h.lower() and "%" in h), None)
                        if col:
                            col_details[key] = col
                            break

                col_nom = self._get_col_name(headers, ["nom"])
                col_prenom = self._get_col_name(headers, ["prénom", "prenom"])

                if not col_nom or not col_prenom:
                    logger.warning(f"⚠️ Colonnes Nom/Prénom introuvables dans {path.name}")
                    continue
                
                for row in rows:
                    nom = row.get(col_nom)
                    prenom = row.get(col_prenom)
                    
                    sid = self.student_service.get_student_id(nom, prenom)
                    if not sid: 
                        continue

                    score = clean_float(row.get(col_global)) if col_global else 0.0
                    
                    details = {}
                    for key, col_name in col_details.items():
                        details[key] = clean_float(row.get(col_name))

                    if self._upsert_result(sid, Platform.ECRIPLUS, a_type, score, details):
                        count += 1
            
                if not self.dry_run:
                    self.session.commit()
                self.stats.ecriplus_imported += count
            except Exception as e:
                self.stats.errors.append(f"Erreur Ecri+ {path.name}: {e}")

def seed_grading_scales(session: Session, stats: ImportStats, dry_run: bool):
    """Initialise les barèmes de correction Rousseau et les règles LT associées."""
    if dry_run:
        return

    scales_data = [
        {
            "name": "Fautes de frappe ou erreur sur les lettres muettes", 
            "description": "Substitutions, omissions, ajouts de lettres ou de mots.",
            "type_rousseau": MistakeType.D,
            "penalty": 0.5,
            "patterns": ["misspelling", "typo", "MORFOLOGIK_RULE_FR_FR"]
        },
        {
            "name": "Erreurs d'accents et de cédilles", 
            "description": "Absence ou mauvaises utilisation des accents (ex : é/è/ê), absence ou mauvaise utilisation de la cédille (ex : ç).",
            "type_rousseau": MistakeType.R,
            "penalty": 1.0,
            "patterns": ["accent", "cedille"]
        },
        {
            "name": "Erreurs de doublement", 
            "description": "Doubles consonnes ou voyelles manquantes ou superflues.",
            "type_rousseau": MistakeType.D,
            "penalty": 0.5,
            "patterns": ["double"]
        },
        {
            "name": "Confusions homophoniques", 
            "description": "Confondre des mots qui se prononcent de la même manière mais s'écrivent différemment (ex : a/à, et/est, ses/ces/s'est/c'est, mais/mes).",
            "type_rousseau": MistakeType.S,
            "penalty": 1.0,
            "patterns": ["homophone", "confused_words"]
        },
        {
            "name": "Erreurs de terminaison", 
            "description": "Mauvaise conjugaison des verbes, mauvaise formation  des adjectifs et des participes passés.",
            "type_rousseau": MistakeType.R,
            "penalty": 1.0,
            "patterns": ["grammar", "conjugation", "agreement"]
        },
        {
            "name": "Autre erreur",
            "description": "Erreur non classifiée.",
            "type_rousseau": MistakeType.AUTRE,
            "penalty": 0.0,
            "patterns": []
        }
    ]

    count_scales = 0
    count_rules = 0

    for data in scales_data:
        existing_scale = session.exec(select(GradingScale).where(GradingScale.name == data["name"])).first()

        if not existing_scale:
            scale = GradingScale(
                name=data["name"],
                description=data["description"],
                type_rousseau=data["type_rousseau"],
                penalty=data["penalty"]
            )
            session.add(scale)
            session.commit()
            session.refresh(scale)
            count_scales += 1
        else:
            scale = existing_scale
            scale.description = data["description"]
            scale.type_rousseau = data["type_rousseau"]
            scale.penalty = data["penalty"]
            session.add(scale)
            session.commit()

        for pattern in data["patterns"]:
            existing_rule = session.exec(select(Rule).where(Rule.lt_rule_id == pattern)).first()
            if not existing_rule:
                new_rule = Rule(
                    lt_rule_id=pattern,
                    description=f"Règle de base pour {scale.name}",
                    is_active=True,
                    grading_scale_id=scale.id
                )
                session.add(new_rule)
                count_rules += 1
            else:
                existing_rule.grading_scale_id = scale.id
                session.add(existing_rule)

    if not dry_run:
        session.commit()
        logger.info(f"📏 Barèmes : {count_scales} typologies et {count_rules} règles LT créées/mises à jour.")
    
def seed_dictations(session: Session, student_service: StudentService, stats: ImportStats, dry_run: bool):
    """Import des dictées (par vague)."""
    if not DICTATES_DIR.exists(): return
    if not FILES["TEACHER"].exists(): return

    lt_host_docker = "languagetool"
    lt_host_windows = "host.docker.internal"
    try:
        socket.gethostbyname(lt_host_docker)
        lt_url = f"http://{lt_host_docker}:8081/v2/check"
        print(f"🐳 Mode Docker Network : {lt_url}")
    except socket.gaierror:
        try:
            socket.gethostbyname(lt_host_windows)
            lt_url = f"http://{lt_host_windows}:8010/v2/check"
            print(f"🪟 Mode Pont Windows : {lt_url}")
        except socket.gaierror:
            lt_url = "http://127.0.0.1:8010/v2/check"
            print(f"💻 Mode Localhost : {lt_url}")

    correction_service = CorrectionService(session, lt_url=lt_url)

    try:
        ref_txt = FILES["TEACHER"].read_text(encoding="utf-8").strip()
    except:
        ref_txt = FILES["TEACHER"].read_text(encoding="latin-1").strip()

    waves = [
        ("data-initial", "Initiale", AssessmentType.INITIAL), 
        ("data-final", "Finale", AssessmentType.FINAL)
    ]

    for folder, suffix, assessment_type in waves:
        wave_dir = DICTATES_DIR / folder
        if not wave_dir.exists(): 
            continue

        dictation_id = 999

        if not dry_run:
            title = f"Dictées Étude Rousseau ({suffix})"
            dictation = session.exec(select(Dictation).where(Dictation.title == title)).first()
            if not dictation:
                default_rules = {s.name: s.penalty for s in session.exec(select(GradingScale)).all()}

                dictation = Dictation(
                    title=title, 
                    content_reference=ref_txt, 
                    rules_config=default_rules
                )
                session.add(dictation)
                session.commit()
                session.refresh(dictation)
            dictation_id = dictation.id
        
        existing = set()
        if not dry_run:
            existing = {(s.student_id, s.dictation_id) for s in session.exec(
                select(Submission).where(Submission.dictation_id == dictation_id)
            ).all()}

        count = 0
        for f in wave_dir.glob("*.txt"):
            if "GRAZIANO" in f.name: 
                continue
            
            parts = f.stem.split('_')
            if len(parts) < 2: 
                continue
            
            sid = student_service.get_student_id(parts[0], parts[1])

            if sid and (sid, dictation_id) not in existing:
                if not dry_run:
                    try:
                        content = f.read_text(encoding='utf-8', errors='ignore').strip()

                        sub = Submission(
                            student_id=sid, 
                            dictation_id=dictation_id, 
                            content_student=content, 
                            assessment_type=assessment_type,
                            scores={}
                        )
                        session.add(sub)
                        session.flush()
                        correction_service.correct_submission(sub)
                        count += 1
                    except Exception as e: 
                        stats.errors.append(f"Erreur dictée {f.name}: {e}")
                else:
                    count += 1

        if not dry_run:
            session.commit()
        stats.dictations_imported += count

# --- MAIN. ---

def reset_db(session: Session):
    logger.warning("☢️ Réinitialisation complète de la base de données en cours...")
    try:
        session.exec(text("DROP SCHEMA public CASCADE;"))
        session.exec(text("CREATE SCHEMA public;"))
        session.exec(text("GRANT ALL ON SCHEMA public TO rousseau;"))
        session.commit()
        SQLModel.metadata.create_all(engine)
        logger.info("♻️ Base de données réinitialisée.")
    except Exception as e:
        logger.error(f"❌ Échec de la réinitialisation de la base de données : {e}")
        session.rollback()
        raise e

def main():
    parser = argparse.ArgumentParser(description="Script d'importation des données initiales.")
    parser.add_argument("--reset-db", action="store_true", help="Réinitialiser la base de données avant l'importation.")
    parser.add_argument("--dry-run", action="store_true", help="Simuler l'import sans écrire en DB.")
    args = parser.parse_args()

    stats = ImportStats()

    if args.dry_run:
        logger.info("🔍 Mode DRY RUN activé : aucune modification ne sera apportée à la base de données.")
    else:
        logger.info("🚀 Initialisation de la base de données...")
        init_db()

    try:
        with Session(engine) as session:
            if args.reset_db and not args.dry_run:
                reset_db(session)
            
            student_service = StudentService(session, stats, args.dry_run)
            if not student_service.uuid_map:
                logger.error("❌ Arrêt : Mapping UUID vide.")
                return

            student_service.import_survey()

            importer = AssessmentImporter(session, student_service, stats, args.dry_run)
            importer.import_voltaire()
            importer.import_ecriplus()

            seed_grading_scales(session, stats, args.dry_run)
            seed_dictations(session, student_service, stats, args.dry_run)

            if not args.dry_run:
                session.commit()

            stats.print_summary(args.dry_run)
    except Exception as e:
        logger.error(f"❌ Erreur critique lors de l'importation : {e}")
        stats.errors.append(str(e))
        stats.print_summary(args.dry_run)
        sys.exit(1)

if __name__ == "__main__":
    main()