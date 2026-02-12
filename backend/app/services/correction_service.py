import difflib
import re
from typing import Any, Dict, List, Tuple
import requests
from sqlalchemy.orm import Session
from sqlmodel import select
from app.models import GradingScale, Mistake, Submission

class CorrectionService:
    DEFAULT_LT_URL = "http://languagetool:8010/v2/check"

    def __init__(self, session: Session, lt_url: str = None):
        self.session = session
        self.lt_api_url = lt_url or self.DEFAULT_LT_URL
        self.scales = self.session.exec(select(GradingScale)).all()

    def _get_scale_by_code(self, code: str) -> GradingScale:
        """Helper pour récupérer une règle par son code (ex: '1')."""
        return next((s for s in self.scales if s.code == code), None)

    def _get_scale_for_lt_match(self, match: Dict[str, Any]) -> GradingScale:
        """Mappe une erreur LanguageTool vers une règle Rousseau."""
        rule_id = match["rule"]["id"].lower()
        issue_type = match["rule"]["issueType"].lower()

        for scale in self.scales:
            if not scale.lt_rule_patterns:
                continue

            patterns = [p.strip().lower() for p in scale.lt_rule_patterns.split(",")]

            for pattern in patterns:
                if pattern in rule_id or pattern in issue_type:
                    return scale
                
        if issue_type == "misspelling":
            return self._get_scale_by_code("1")
        
        return self._get_scale_by_code("AUTRE")
    
    def _check_fidelity(self, ref_text: str, student_text: str, existing_mistakes_ranges: List[Tuple[int, int]]) -> List[Mistake]:
        """
        Compare le texte étudiant au texte de référence mot à mot.
        Détecte : Omissions, Ajouts, Substitutions lexicales (que LanguageTool n'a pas vu).
        """
        mistakes = []
        
        def tokenize_with_positions(text):
            tokens = []
            for m in re.finditer(r'\S+', text):
                tokens.append({
                    "text": m.group(0),
                    "start": m.start(),
                    "end": m.end()
                })
            return tokens

        ref_tokens = tokenize_with_positions(ref_text)
        stu_tokens = tokenize_with_positions(student_text)
        
        ref_words = [t["text"] for t in ref_tokens]
        stu_words = [t["text"] for t in stu_tokens]

        matcher = difflib.SequenceMatcher(None, ref_words, stu_words)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            
            # --- CAS 1 : REMPLACEMENT (SUBSTITUTION). ---
            if tag == 'replace':
                for k in range(j2 - j1):
                    stu_idx = j1 + k
                    ref_idx = i1 + k if (i1 + k) < i2 else i1
                    
                    token = stu_tokens[stu_idx]
                    ref_word = ref_words[ref_idx] if ref_idx < len(ref_words) else "?"

                    is_already_caught = False
                    for (start, end) in existing_mistakes_ranges:
                        if not (token["end"] <= start or token["start"] >= end):
                            is_already_caught = True
                            break
                    
                    if is_already_caught:
                        continue

                    scale = self._get_scale_by_code("1")
                    
                    mistakes.append(Mistake(
                        student_word=token["text"],
                        correct_word=ref_word,
                        position_index=token["start"],
                        length=token["end"] - token["start"],
                        category_code=scale.code,
                        type_rousseau=scale.type_rousseau,
                        malus_applied=scale.penalty,
                        rule_id_lt="FIDELITY_SUBSTITUTION",
                        message=f"Mot incorrect. Attendu : '{ref_word}'",
                        context=token["text"]
                    ))

            # --- CAS 2 : INSERTION (AJOUT). ---
            elif tag == 'insert':
                scale = self._get_scale_by_code("1")
                
                for k in range(j1, j2):
                    token = stu_tokens[k]
                    mistakes.append(Mistake(
                        student_word=token["text"],
                        correct_word="",
                        position_index=token["start"],
                        length=token["end"] - token["start"],
                        category_code=scale.code,
                        type_rousseau=scale.type_rousseau,
                        malus_applied=scale.penalty,
                        rule_id_lt="FIDELITY_ADDITION",
                        message="Mot ajouté (ne figure pas dans le texte)",
                        context=token["text"]
                    ))

            # --- CAS 3 : SUPPRESSION (OUBLI). ---
            elif tag == 'delete':
                scale = self._get_scale_by_code("1")
                
                pos_anchor = stu_tokens[j1]["start"] if j1 < len(stu_tokens) else len(student_text)
                
                missing_words = " ".join(ref_words[i1:i2])
                
                mistakes.append(Mistake(
                    student_word="[OUBLI]",
                    correct_word=missing_words,
                    position_index=pos_anchor,
                    length=0,
                    category_code=scale.code,
                    type_rousseau=scale.type_rousseau,
                    malus_applied=scale.penalty,
                    rule_id_lt="FIDELITY_OMISSION",
                    message=f"Mot(s) manquant(s) : '{missing_words}'",
                    context="[...]"
                ))

        return mistakes
    
    def correct_submission(self, submission: Submission) -> Submission:
        """
        Corrige une soumission : appelle LanguageTool, crée les objets Mistake et calcule la note.
        """
        text = submission.content_student

        if not submission.dictation:
            from app.models import Dictation
            submission.dictation = self.session.get(Dictation, submission.dictation_id)

        ref_text = submission.dictation.content_reference if submission.dictation else ""

        if not text or not text.strip():
            submission.final_score = 0.0
            return submission
        
        lt_mistakes = []
        lt_ranges = []
        
        try:
            response = requests.post(
                self.lt_api_url,
                data={
                    "text": text,
                    "language": "fr",
                    "enabledOnly": "false"
                },
                timeout=5
            )
            if response.status_code == 200:
                matches = response.json().get("matches", [])
                for match in matches:
                    if match["rule"]["issueType"] == "style": continue
                    
                    scale = self._get_scale_for_lt_match(match)
                    if not scale: continue

                    m = Mistake(
                        submission_id=submission.id,
                        student_word=match["context"]["text"][match["offset"] : match["offset"] + match["length"]],
                        correct_word=match["replacements"][0]["value"] if match["replacements"] else "",
                        position_index=match["offset"],
                        length=match["length"],
                        category_code=scale.code,
                        type_rousseau=scale.type_rousseau,
                        malus_applied=scale.penalty,
                        rule_id_lt=match["rule"]["id"],
                        message=match["message"],
                        context=match["context"]["text"]
                    )
                    lt_mistakes.append(m)
                    lt_ranges.append((match["offset"], match["offset"] + match["length"]))
        except Exception as e:
            print(f"⚠️ Warning LT: {e}")

        fidelity_mistakes = []
        if ref_text:
            fidelity_mistakes = self._check_fidelity(ref_text, text, lt_ranges)

        all_mistakes = lt_mistakes + fidelity_mistakes

        total_penalty = 0.0
        scores_breakdown = {}

        code_to_name = {s.code: s.name for s in self.scales}

        for m in all_mistakes:
            total_penalty += m.malus_applied

            code = m.category_code
            category_name = code_to_name.get(code, code)

            if category_name not in scores_breakdown:
                scores_breakdown[category_name] = 0.0
            
            scores_breakdown[category_name] += m.malus_applied

        scores_breakdown = {k: round(v, 2) for k, v in scores_breakdown.items()}

        submission.final_score = round(total_penalty, 2)
        
        submission.scores = scores_breakdown
        
        for m in all_mistakes:
            if submission.id: m.submission_id = submission.id
            self.session.add(m)

        return submission