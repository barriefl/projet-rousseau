import difflib
import re
from typing import Any, Dict, List, Tuple
import requests
from sqlalchemy.orm import Session
from sqlmodel import select
from app.models import Dictation, GradingScale, Mistake, Rule, Submission

class CorrectionService:
    DEFAULT_LT_URL = "http://languagetool:8010/v2/check"

    def __init__(self, session: Session, lt_url: str = None):
        self.session = session
        self.lt_api_url = lt_url or self.DEFAULT_LT_URL
        self.scales = self.session.exec(select(GradingScale)).all()

    def _get_scale_by_name(self, name: str) -> GradingScale:
        """Helper pour récupérer une règle par son nom."""
        return next((s for s in self.scales if s.name == name), None)

    def _get_scale_for_lt_match(self, match: Dict[str, Any]) -> GradingScale:
        """Auto-découverte : mappe, ignore, ou crée une règle LT."""
        rule_id = match["rule"]["id"]
        
        rule = self.session.exec(select(Rule).where(Rule.lt_rule_id == rule_id)).first()

        if not rule:
            description = match.get("message", f"Règle LT: {rule_id}")
            rule = Rule(
                lt_rule_id=rule_id,
                description=description[:255],
                is_active=True,
                grading_scale_id=None
            )
            self.session.add(rule)
            self.session.commit()
            self.session.refresh(rule)

        if not rule.is_active:
            return None
        
        if rule.grading_scale_id:
            return self.session.get(GradingScale, rule.grading_scale_id)
        
        return self._get_scale_by_name("Autre erreur")
    
    def _get_scale_for_custom_rule(self, rule_id: str, description: str) -> GradingScale:
        """Enregistre une règle 'maison' (Fidélité) dans la base pour qu'elle apparaisse dans l'interface."""
        rule = self.session.exec(select(Rule).where(Rule.lt_rule_id == rule_id)).first()

        if not rule:
            rule = Rule(
                lt_rule_id=rule_id,
                description=description[:255],
                is_active=True,
                grading_scale_id=None
            )
            self.session.add(rule)
            self.session.commit()
            self.session.refresh(rule)

        if not rule.is_active:
            return None
        
        if rule.grading_scale_id:
            return self.session.get(GradingScale, rule.grading_scale_id)
        
        return self._get_scale_by_name("Autre erreur")
    
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

                    scale = self._get_scale_for_custom_rule("FIDELITY_SUBSTITUTION", "Mot remplacé ou mal orthographié (Fidélité)")
                    if not scale: continue
                    
                    mistakes.append(Mistake(
                        student_word=token["text"],
                        correct_word=ref_word,
                        position_index=token["start"],
                        length=token["end"] - token["start"],
                        grading_scale_id=scale.id,
                        type_rousseau=scale.type_rousseau,
                        malus_applied=scale.penalty,
                        rule_id_lt="FIDELITY_SUBSTITUTION",
                        message=f"Mot incorrect. Attendu : '{ref_word}'",
                        context=token["text"]
                    ))

            # --- CAS 2 : INSERTION (AJOUT). ---
            elif tag == 'insert':
                scale = self._get_scale_for_custom_rule("FIDELITY_ADDITION", "Mot ajouté en trop (Fidélité)")
                if not scale: continue
                
                for k in range(j1, j2):
                    token = stu_tokens[k]
                    mistakes.append(Mistake(
                        student_word=token["text"],
                        correct_word="",
                        position_index=token["start"],
                        length=token["end"] - token["start"],
                        grading_scale_id=scale.id,
                        type_rousseau=scale.type_rousseau,
                        malus_applied=scale.penalty,
                        rule_id_lt="FIDELITY_ADDITION",
                        message="Mot ajouté (ne figure pas dans le texte)",
                        context=token["text"]
                    ))

            # --- CAS 3 : SUPPRESSION (OUBLI). ---
            elif tag == 'delete':
                scale = self._get_scale_for_custom_rule("FIDELITY_OMISSION", "Mot manquant / oublié (Fidélité)")
                if not scale: continue
                
                pos_anchor = stu_tokens[j1]["start"] if j1 < len(stu_tokens) else len(student_text)
                
                missing_words = " ".join(ref_words[i1:i2])
                
                mistakes.append(Mistake(
                    student_word="[OUBLI]",
                    correct_word=missing_words,
                    position_index=pos_anchor,
                    length=0,
                    grading_scale_id=scale.id,
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
                timeout=20
            )
            if response.status_code == 200:
                matches = response.json().get("matches", [])
                for match in matches:
                    if match["rule"]["issueType"] == "style": continue
                    
                    scale = self._get_scale_for_lt_match(match)
                    if not scale: continue

                    replacements = [r["value"] for r in match.get("replacements", [])]
                    best_correction = replacements[0] if replacements else ""

                    if ref_text and replacements:
                        for rep in replacements:
                            if rep.lower() in ref_text.lower():
                                best_correction = rep
                                break

                    m = Mistake(
                        submission_id=submission.id,
                        student_word=text[match["offset"] : match["offset"] + match["length"]],
                        correct_word=best_correction,
                        position_index=match["offset"],
                        length=match["length"],
                        grading_scale_id=scale.id,
                        type_rousseau=scale.type_rousseau,
                        malus_applied = self._get_penalty_for_scale(scale, submission.dictation),
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

        id_to_name = {s.id: s.name for s in self.scales}

        for m in all_mistakes:
            total_penalty += m.malus_applied

            category_name = id_to_name.get(m.grading_scale_id, "Autre erreur")

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
    
    def generate_html_text(self, text: str, mistakes: List[Mistake]) -> str:
        """
        Génère le texte HTML avec les balises <span> pour les fautes.
        On lit les erreurs à l'envers pour ne pas décaler les index lors de l'insertion !
        """
        import html
        
        sorted_mistakes = sorted(mistakes, key=lambda m: m.position_index, reverse=True)
        html_text = text

        for m in sorted_mistakes:
            start = m.position_index
            end = start + m.length
            
            word = html_text[start:end]
            
            desc = html.escape(m.message) if m.message else ""
            corr = html.escape(m.correct_word) if m.correct_word else ""
            rule_id = html.escape(m.rule_id_lt) if m.rule_id_lt else "INCONNU"
            
            span = f'<span class="faute" data-type="{m.type_rousseau}" data-malus="{m.malus_applied}" data-corr="{corr}" data-desc="{desc}" data-rule-id="{rule_id}">{word}</span>'
            
            html_text = html_text[:start] + span + html_text[end:]

        return html_text.replace('\n', '<br>')
    
    def _get_penalty_for_scale(self, scale: GradingScale, dictation: Dictation) -> float:
        """Récupère la pénalité depuis la config de la dictée, ou la globale par défaut."""
        if dictation and dictation.rules_config:
            return dictation.rules_config.get(scale.name, scale.penalty)
        return scale.penalty

    def recalculate_dictation_scores(self, dictation: Dictation):
        """Ré-évalue les fautes d'une dictée selon les règles et barèmes actuels."""
        all_rules = self.session.exec(select(Rule)).all()
        rules_map = {r.lt_rule_id: r for r in all_rules}

        all_scales = self.session.exec(select(GradingScale)).all()
        scales_map = {s.id: s for s in all_scales}

        dictation_config = dictation.rules_config or {}

        for sub in dictation.submissions:
            total_penalty = 0.0
            scores_breakdown = {}

            for m in sub.mistakes:
                db_rule = rules_map.get(m.rule_id_lt)

                if not db_rule or not db_rule.is_active:
                    m.malus_applied = 0.0
                    m.grading_scale_id = None
                    continue

                scale = scales_map.get(db_rule.grading_scale_id)
                if not scale:
                    continue

                m.grading_scale_id = scale.id
                m.type_rousseau = scale.type_rousseau
                
                new_penalty = dictation_config.get(scale.name, scale.penalty)
                m.malus_applied = new_penalty
                
                total_penalty += new_penalty

                if scale.name not in scores_breakdown:
                    scores_breakdown[scale.name] = 0.0
                scores_breakdown[scale.name] += new_penalty

            sub.final_score = round(total_penalty, 2)
            sub.scores = {k: round(v, 2) for k, v in scores_breakdown.items()}
            
            self.session.add(sub)
        
        self.session.commit()