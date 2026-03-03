import difflib
import re
from typing import Any, Dict, List, Tuple

import requests
from sqlalchemy.orm import Session
from sqlmodel import select

from app.models import Category, Dictation, Mistake, MistakeType, Rule, Submission


class CorrectionService:
    DEFAULT_LT_URL = "http://languagetool:8010/v2/check"

    def __init__(self, session: Session, lt_url: str = None):
        self.session = session
        self.lt_api_url = lt_url or self.DEFAULT_LT_URL

    def _get_or_create_rule_and_category(self, match: Dict[str, Any]) -> Category:
        """Auto-découverte : crée la catégorie LT si elle n'existe pas, puis la règle, et les lie."""

        cat_id = match["rule"]["category"]["id"]
        cat_name = match["rule"]["category"]["name"]

        category = self.session.exec(
            select(Category).where(Category.lt_category_id == cat_id)
        ).first()
        if not category:
            category = Category(
                lt_category_id=cat_id,
                name=cat_name,
                type_rousseau=MistakeType.AUTRE,
                penalty=1.0,
            )
            self.session.add(category)
            self.session.commit()
            self.session.refresh(category)

        rule_id = match["rule"]["id"]
        rule = self.session.exec(select(Rule).where(Rule.lt_rule_id == rule_id)).first()

        if not rule:
            description = match.get("message", f"Règle LT: {rule_id}")
            rule = Rule(
                lt_rule_id=rule_id,
                description=description[:255],
                is_active=True,
                category_id=category.id,
            )
            self.session.add(rule)
            self.session.commit()
            self.session.refresh(rule)

        if not rule.is_active:
            return None

        return category

    def _get_or_create_custom_rule_and_category(
        self, rule_id: str, description: str
    ) -> Category:
        """Enregistre les règles de Fidélité dans une catégorie 'Fidélité au texte'."""
        cat_id = "FIDELITY"
        category = self.session.exec(
            select(Category).where(Category.lt_category_id == cat_id)
        ).first()

        if not category:
            category = Category(
                lt_category_id=cat_id,
                name="Fidélité au texte",
                type_rousseau=MistakeType.AUTRE,
                penalty=1.0,
            )
            self.session.add(category)
            self.session.commit()
            self.session.refresh(category)

        rule = self.session.exec(select(Rule).where(Rule.lt_rule_id == rule_id)).first()
        if not rule:
            rule = Rule(
                lt_rule_id=rule_id,
                description=description[:255],
                is_active=True,
                category_id=category.id,
            )
            self.session.add(rule)
            self.session.commit()
            self.session.refresh(rule)

        if not rule.is_active:
            return None

        return category

    def _check_fidelity(
        self,
        ref_text: str,
        student_text: str,
        existing_mistakes_ranges: List[Tuple[int, int]],
    ) -> List[Mistake]:
        """Compare le texte étudiant au texte de référence mot à mot."""
        mistakes = []

        def tokenize_with_positions(text):
            tokens = []
            for m in re.finditer(r"\S+", text):
                tokens.append({"text": m.group(0), "start": m.start(), "end": m.end()})
            return tokens

        ref_tokens = tokenize_with_positions(ref_text)
        stu_tokens = tokenize_with_positions(student_text)

        ref_words = [t["text"] for t in ref_tokens]
        stu_words = [t["text"] for t in stu_tokens]

        matcher = difflib.SequenceMatcher(None, ref_words, stu_words)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue

            # --- CAS 1 : REMPLACEMENT (SUBSTITUTION). ---
            if tag == "replace":
                for k in range(j2 - j1):
                    stu_idx = j1 + k
                    ref_idx = i1 + k if (i1 + k) < i2 else i1

                    token = stu_tokens[stu_idx]
                    ref_word = ref_words[ref_idx] if ref_idx < len(ref_words) else "?"

                    is_already_caught = False
                    for start, end in existing_mistakes_ranges:
                        if not (token["end"] <= start or token["start"] >= end):
                            is_already_caught = True
                            break

                    if is_already_caught:
                        continue

                    category = self._get_or_create_custom_rule_and_category(
                        "FIDELITY_SUBSTITUTION",
                        "Mot remplacé ou mal orthographié (Fidélité)",
                    )
                    if not category:
                        continue

                    mistakes.append(
                        Mistake(
                            student_word=token["text"],
                            correct_word=ref_word,
                            position_index=token["start"],
                            length=token["end"] - token["start"],
                            category_id=category.id,
                            type_rousseau=category.type_rousseau,
                            malus_applied=category.penalty,
                            rule_id_lt="FIDELITY_SUBSTITUTION",
                            message=f"Mot incorrect. Attendu : '{ref_word}'",
                            context=token["text"],
                        )
                    )

            # --- CAS 2 : INSERTION (AJOUT). ---
            elif tag == "insert":
                category = self._get_or_create_custom_rule_and_category(
                    "FIDELITY_ADDITION", "Mot ajouté en trop (Fidélité)"
                )
                if not category:
                    continue

                for k in range(j1, j2):
                    token = stu_tokens[k]
                    mistakes.append(
                        Mistake(
                            student_word=token["text"],
                            correct_word="",
                            position_index=token["start"],
                            length=token["end"] - token["start"],
                            category_id=category.id,
                            type_rousseau=category.type_rousseau,
                            malus_applied=category.penalty,
                            rule_id_lt="FIDELITY_ADDITION",
                            message="Mot ajouté (ne figure pas dans le texte)",
                            context=token["text"],
                        )
                    )

            # --- CAS 3 : SUPPRESSION (OUBLI). ---
            elif tag == "delete":
                category = self._get_or_create_custom_rule_and_category(
                    "FIDELITY_OMISSION", "Mot manquant / oublié (Fidélité)"
                )
                if not category:
                    continue

                pos_anchor = (
                    stu_tokens[j1]["start"]
                    if j1 < len(stu_tokens)
                    else len(student_text)
                )

                missing_words = " ".join(ref_words[i1:i2])

                mistakes.append(
                    Mistake(
                        student_word="[OUBLI]",
                        correct_word=missing_words,
                        position_index=pos_anchor,
                        length=0,
                        category_id=category.id,
                        type_rousseau=category.type_rousseau,
                        malus_applied=category.penalty,
                        rule_id_lt="FIDELITY_OMISSION",
                        message=f"Mot(s) manquant(s) : '{missing_words}'",
                        context="[...]",
                    )
                )

        return mistakes

    def correct_submission(self, submission: Submission) -> Submission:
        """Corrige une soumission."""
        text = submission.content_student

        if not submission.dictation:
            from app.models import Dictation

            submission.dictation = self.session.get(Dictation, submission.dictation_id)

        ref_text = (
            submission.dictation.content_reference if submission.dictation else ""
        )

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
                    "language": "fr-FR",
                    "level": "picky",
                    "enabledOnly": "false",
                },
                timeout=20,
            )
            if response.status_code == 200:
                matches = response.json().get("matches", [])
                for match in matches:
                    if match["rule"]["issueType"] == "style":
                        continue

                    category = self._get_or_create_rule_and_category(match)
                    if not category:
                        continue

                    replacements = [r["value"] for r in match.get("replacements", [])]
                    best_correction = replacements[0] if replacements else ""

                    if ref_text and replacements:
                        for rep in replacements:
                            if rep.lower() in ref_text.lower():
                                best_correction = rep
                                break

                    m = Mistake(
                        submission_id=submission.id,
                        student_word=text[
                            match["offset"] : match["offset"] + match["length"]
                        ],
                        correct_word=best_correction,
                        position_index=match["offset"],
                        length=match["length"],
                        category_id=category.id,
                        type_rousseau=category.type_rousseau,
                        malus_applied=category.penalty,
                        rule_id_lt=match["rule"]["id"],
                        message=match["message"],
                        context=match["context"]["text"],
                    )
                    lt_mistakes.append(m)
                    lt_ranges.append(
                        (match["offset"], match["offset"] + match["length"])
                    )
        except Exception as e:
            print(f"⚠️ Warning LT: {e}")

        fidelity_mistakes = []
        if ref_text:
            fidelity_mistakes = self._check_fidelity(ref_text, text, lt_ranges)

        all_mistakes = lt_mistakes + fidelity_mistakes

        total_penalty = 0.0
        scores_breakdown = {}

        all_categories = self.session.exec(select(Category)).all()
        id_to_name = {c.id: c.name for c in all_categories}

        for m in all_mistakes:
            total_penalty += m.malus_applied

            category_name = id_to_name.get(m.category_id, "Autre erreur")

            if category_name not in scores_breakdown:
                scores_breakdown[category_name] = 0.0

            scores_breakdown[category_name] += m.malus_applied

        scores_breakdown = {k: round(v, 2) for k, v in scores_breakdown.items()}

        submission.final_score = round(total_penalty, 2)
        submission.scores = scores_breakdown

        for m in all_mistakes:
            if submission.id:
                m.submission_id = submission.id
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

        clean_text = html_text.replace("\r\n", "\n").replace("\r", "\n")

        return clean_text.replace("\n", "<br>")

    def recalculate_dictation_scores(self, dictation: Dictation):
        """Ré-évalue les fautes d'une dictée selon les règles et catégories actuelles."""
        all_rules = self.session.exec(select(Rule)).all()
        rules_map = {r.lt_rule_id: r for r in all_rules}

        all_categories = self.session.exec(select(Category)).all()
        categories_map = {c.id: c for c in all_categories}

        for sub in dictation.submissions:
            total_penalty = 0.0
            scores_breakdown = {}

            for m in sub.mistakes:
                db_rule = rules_map.get(m.rule_id_lt)

                if not db_rule or not db_rule.is_active:
                    m.malus_applied = 0.0
                    m.category_id = None
                    continue

                category = categories_map.get(db_rule.category_id)
                if not category:
                    continue

                m.category_id = category.id
                m.type_rousseau = category.type_rousseau

                new_penalty = category.penalty
                m.malus_applied = new_penalty

                total_penalty += new_penalty

                if category.name not in scores_breakdown:
                    scores_breakdown[category.name] = 0.0
                scores_breakdown[category.name] += new_penalty

            sub.final_score = round(total_penalty, 2)
            sub.scores = {k: round(v, 2) for k, v in scores_breakdown.items()}

            self.session.add(sub)

        self.session.commit()
