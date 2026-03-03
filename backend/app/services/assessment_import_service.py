import csv
from typing import Any, Dict, List, Tuple

from sqlmodel import Session, select

from app.models import AssessmentResult, Student
from app.schemas.assessment_schema import (
    AssessmentExecuteRequest,
    AssessmentMatchPreview,
    AssessmentPreviewResponse,
    AssessmentType,
    Platform,
)
from app.utils.crypto import decrypt_text
from app.utils.import_utils import (
    clean_float,
    find_col_by_keyword,
    is_fuzzy_match,
    normalize_text,
)

# --- CONSTANTES D'IMPORTATION ---
VOLTAIRE_COLS = {
    AssessmentType.INITIAL: {
        "score": "score évaluation initiale",
        "details": {"temps_initial": "temps évaluation initiale"},
    },
    AssessmentType.FINAL: {
        "score": "score évaluation evaluation finale",
        "details": {
            "temps_total": "temps total passé",
            "duree_entrainement": "durée d'entraînement",
            "niveau_atteint": "niveau atteint",
            "progres": "progrès",
            "tests_blancs": "variante tests blancs mensuels",
        },
    },
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
        "score_domaine_texte": ["domaine du texte"],
    },
}


class AssessmentImportService:
    def __init__(self, session: Session):
        self.session = session

    def _read_csv(self, file_content: bytes) -> List[Dict[str, str]]:
        try:
            csv_text = file_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            csv_text = file_content.decode("cp1252", errors="replace")

        lines = csv_text.splitlines()
        if not lines:
            return []

        reader = csv.reader(lines, delimiter=";")
        raw_headers = next(reader, None)
        if not raw_headers:
            return []

        headers = []
        seen = {}
        for h in raw_headers:
            if h in seen:
                seen[h] += 1
                headers.append(f"{h} (copie {seen[h]})")
            else:
                seen[h] = 0
                headers.append(h)

        result = []
        for row in reader:
            row_dict = {
                headers[i]: (row[i] if i < len(row) else "")
                for i in range(len(headers))
            }
            result.append(row_dict)

        return result

    def _extract_voltaire_data(
        self, row: Dict[str, str], headers: List[str], assessment_type: AssessmentType
    ) -> Tuple[float, Dict[str, Any]]:
        """Logique d'extraction spécifique à Voltaire basée sur VOLTAIRE_COLS."""
        config = VOLTAIRE_COLS[assessment_type]

        col_score = find_col_by_keyword(headers, config["score"])
        raw_score = clean_float(row.get(col_score)) if col_score else 0.0

        score = raw_score / 100.0 if raw_score > 1 else raw_score

        details = {}
        for key, keyword in config["details"].items():
            if key == "tests_blancs":
                cols = [h for h in headers if "blanc" in h.lower()]
                if cols:
                    tests = []
                    for c in cols:
                        val = clean_float(row.get(c))
                        if val is not None:
                            norm_val = val / 100.0 if val > 1 else val
                            tests.append(norm_val)
                    if tests:
                        details[key] = tests
            else:
                col = find_col_by_keyword(headers, keyword)
                if col:
                    val = row.get(col)
                    numeric_fields = ["niveau_atteint", "progres"]
                    if key in numeric_fields:
                        clean_val = clean_float(val)
                        if clean_val is not None:
                            details[key] = clean_val
                    elif val and str(val).strip():
                        details[key] = str(val).strip()

        return score, details

    def _extract_ecriplus_data(
        self, row: Dict[str, str], headers: List[str]
    ) -> Tuple[float, Dict[str, Any]]:
        """Logique d'extraction spécifique à Ecri+ basée sur ECRIPLUS_COLS."""
        col_global = None
        for kw in ECRIPLUS_COLS["global"]:
            col = find_col_by_keyword(headers, kw)
            if col:
                col_global = col
                break

        raw_score = clean_float(row.get(col_global)) if col_global else 0.0
        score = raw_score / 100.0 if raw_score > 1 else raw_score

        details = {}
        for key, keywords in ECRIPLUS_COLS["details"].items():
            for kw in keywords:
                col = next(
                    (h for h in headers if kw.lower() in h.lower() and "%" in h), None
                )
                if col:
                    val = clean_float(row.get(col))
                    if val is not None:
                        details[key] = val / 100.0 if val > 1 else val
                    break

        return score, details

    def analyze_file(
        self,
        promotion_id: int,
        platform: Platform,
        assessment_type: AssessmentType,
        file_content: bytes,
    ) -> AssessmentPreviewResponse:
        rows = self._read_csv(file_content)
        if not rows:
            raise ValueError("Le fichier CSV est vide.")

        headers = list(rows[0].keys())
        col_nom = find_col_by_keyword(
            headers,
            ["nom du participant", "nom", "nom d'usage"],
            exclude=["organisation", "établissement", "etablissement", "fichier"],
        )
        col_prenom = find_col_by_keyword(
            headers,
            ["prénom du participant", "prenom du participant", "prénom", "prenom"],
        )

        if not col_nom or not col_prenom:
            raise ValueError(
                "Impossible de trouver les colonnes 'Nom' et 'Prénom' dans le fichier. Vérifiez le format."
            )

        existing_students = self.session.exec(
            select(Student).where(Student.promotion_id == promotion_id)
        ).all()
        db_students = [
            {
                "student": s,
                "norm_first": normalize_text(decrypt_text(s.first_name_encrypted)),
                "norm_last": normalize_text(decrypt_text(s.last_name_encrypted)),
            }
            for s in existing_students
        ]

        matched = []
        unmatched = []

        for row in rows:
            csv_nom = row.get(col_nom, "").strip()
            csv_prenom = row.get(col_prenom, "").strip()
            if not csv_nom or not csv_prenom:
                continue

            norm_csv_first = normalize_text(csv_prenom)
            norm_csv_last = normalize_text(csv_nom)

            if platform == Platform.VOLTAIRE:
                score, details = self._extract_voltaire_data(
                    row, headers, assessment_type
                )
            else:
                score, details = self._extract_ecriplus_data(row, headers)

            match_found = False
            for db_s in db_students:
                if (
                    norm_csv_first == db_s["norm_first"]
                    and norm_csv_last == db_s["norm_last"]
                ):
                    match_found = True
                    match_type = "exact"
                elif is_fuzzy_match(
                    norm_csv_first, db_s["norm_first"]
                ) and is_fuzzy_match(norm_csv_last, db_s["norm_last"]):
                    match_found = True
                    match_type = "fuzzy"

                if match_found:
                    matched.append(
                        AssessmentMatchPreview(
                            csv_nom=csv_nom,
                            csv_prenom=csv_prenom,
                            db_student_id=db_s["student"].id,
                            db_first_name=decrypt_text(
                                db_s["student"].first_name_encrypted
                            ),
                            db_last_name=decrypt_text(
                                db_s["student"].last_name_encrypted
                            ),
                            match_type=match_type,
                            score=score,
                            details=details,
                        )
                    )
                    break

            if not match_found:
                unmatched.append(
                    AssessmentMatchPreview(
                        csv_nom=csv_nom,
                        csv_prenom=csv_prenom,
                        match_type="not_found",
                        score=score,
                        details=details,
                    )
                )

        return AssessmentPreviewResponse(
            platform=platform,
            assessment_type=assessment_type,
            matched_results=matched,
            unmatched_results=unmatched,
        )

    def execute_import(self, request: AssessmentExecuteRequest) -> Dict[str, Any]:
        created_count = 0
        updated_count = 0

        try:
            for item in request.results:
                statement = select(AssessmentResult).where(
                    AssessmentResult.student_id == item.student_id,
                    AssessmentResult.platform == request.platform,
                    AssessmentResult.assessment_type == request.assessment_type,
                )
                existing_result = self.session.exec(statement).first()

                if existing_result:
                    existing_result.score = item.score
                    existing_result.details = item.details
                    self.session.add(existing_result)
                    updated_count += 1
                else:
                    new_result = AssessmentResult(
                        student_id=item.student_id,
                        platform=request.platform,
                        assessment_type=request.assessment_type,
                        score=item.score,
                        details=item.details,
                    )
                    self.session.add(new_result)
                    created_count += 1

            self.session.commit()
            return {
                "status": "success",
                "created": created_count,
                "updated": updated_count,
            }

        except Exception as e:
            self.session.rollback()
            raise e
