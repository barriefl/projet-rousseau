from unittest.mock import MagicMock, patch

import pytest
import requests
from fastapi import status
from sqlalchemy.orm.attributes import set_committed_value
from sqlmodel import select

from app.models import Category, Dictation, Mistake, MistakeType, Rule, Submission
from app.models.entities import Student
from app.models.enums import AssessmentType
from app.services.correction_service import CorrectionService
from app.utils.crypto import encrypt_text


# ---------------------------------------------------------
# FIXTURES.
# ---------------------------------------------------------
@pytest.fixture
def service(session):
    """Initialise le service avec la session de test."""
    return CorrectionService(session)


@pytest.fixture
def setup_dictation_data(session):
    """Prépare une dictée et une soumission."""
    student = Student(
        first_name_encrypted=encrypt_text("Jean"),
        last_name_encrypted=encrypt_text("TEST"),
        promotion_id=1,
    )
    session.add(student)
    session.flush()

    dictation = Dictation(
        title="Dictée de Test", content_reference="Le petit chat dort."
    )
    session.add(dictation)
    session.flush()

    submission = Submission(
        student_id=student.id,
        dictation_id=dictation.id,
        content_student="Le gros chien mange.",
        dictation=dictation,
        assessment_type=AssessmentType.INITIAL,
    )
    session.add(submission)
    session.commit()
    return dictation, submission


# ---------------------------------------------------------
# TEST FIDÉLITÉ (SUBSTITUTION, AJOUT, OUBLI).
# ---------------------------------------------------------
def test_check_fidelity_logic(service):
    """Vérifie que les trois types de fautes de fidélité sont détectés."""
    # ARRANGE.
    ref = "Le chat dort."
    student = "Le gros dort."
    ranges = []

    # ACT.
    mistakes = service._check_fidelity(ref, student, ranges)

    # ASSERT.
    assert len(mistakes) > 0
    types = [m.rule_id_lt for m in mistakes]
    assert "FIDELITY_SUBSTITUTION" in types or "FIDELITY_OMISSION" in types


def test_check_fidelity_omission(service):
    """Teste spécifiquement l'oubli de mots."""
    # ARRANGE.
    ref = "Un deux trois"
    stu = "Un trois"

    # ACT.
    mistakes = service._check_fidelity(ref, stu, [])

    # ASSERT.
    assert any(m.rule_id_lt == "FIDELITY_OMISSION" for m in mistakes)
    assert any("deux" in m.correct_word for m in mistakes)


def test_fidelity_insertion_and_inactive_rule(service, session, setup_dictation_data):
    """Couvre le CAS 2 (Insertion) et les règles de fidélité inactives."""
    # ARRANGE.
    _, _ = setup_dictation_data
    ref = "Le chat"
    student = "Le chat noir"

    service._get_or_create_custom_rule_and_category("FIDELITY_ADDITION", "Add")
    rule = session.exec(
        select(Rule).where(Rule.lt_rule_id == "FIDELITY_ADDITION")
    ).first()
    rule.is_active = False
    session.add(rule)
    session.commit()

    # ACT.
    mistakes = service._check_fidelity(ref, student, [])

    # ASSERT.
    assert len(mistakes) == 0


def test_fidelity_substitution_and_deletion_inactive(
    service, session, setup_dictation_data
):
    """Couvre les 'continue' du CAS 1 (Substitution) et CAS 3 (Suppression)."""
    # ARRANGE.
    for r_id in ["FIDELITY_SUBSTITUTION", "FIDELITY_OMISSION"]:
        service._get_or_create_custom_rule_and_category(r_id, "Desc")
        rule = session.exec(select(Rule).where(Rule.lt_rule_id == r_id)).first()
        rule.is_active = False
        session.add(rule)
    session.commit()

    # ACT.
    mistakes = service._check_fidelity("Le chat dort.", "Le chien.", [])

    # ASSERT.
    assert len(mistakes) == 0


def test_fidelity_insertion_active(service, session, setup_dictation_data):
    """Vérifie que les mots ajoutés sont bien enregistrés quand la règle est active."""
    # ARRANGE.
    _, _ = setup_dictation_data
    ref = "Le petit chat"
    student = "Le petit chat noir"

    service._get_or_create_custom_rule_and_category("FIDELITY_ADDITION", "Add")
    rule = session.exec(
        select(Rule).where(Rule.lt_rule_id == "FIDELITY_ADDITION")
    ).first()
    rule.is_active = True
    session.add(rule)
    session.commit()

    # ACT.
    mistakes = service._check_fidelity(ref, student, [])

    # ASSERT.
    assert len(mistakes) == 1
    assert mistakes[0].rule_id_lt == "FIDELITY_ADDITION"
    assert mistakes[0].student_word == "noir"
    assert mistakes[0].message == "Mot ajouté (ne figure pas dans le texte)"


def test_fidelity_omission_inactive(service, session, setup_dictation_data):
    """Couvre le 'if not category: continue' du CAS 3 (Oubli)."""
    # ARRANGE.
    _, _ = setup_dictation_data
    ref = "Le petit chat"
    student = "Le chat"

    service._get_or_create_custom_rule_and_category("FIDELITY_OMISSION", "Oubli")
    rule = session.exec(
        select(Rule).where(Rule.lt_rule_id == "FIDELITY_OMISSION")
    ).first()
    rule.is_active = False
    session.add(rule)
    session.commit()

    # ACT.
    mistakes = service._check_fidelity(ref, student, [])

    # ASSERT.
    assert len(mistakes) == 0


# ---------------------------------------------------------
# TEST AUTO-CRÉATION RÈGLES ET CATÉGORIES (LT).
# ---------------------------------------------------------
def test_get_or_create_rule_and_category(service, session):
    """Vérifie que le service crée les règles inconnues en base."""
    # ARRANGE.
    match = {
        "rule": {
            "id": "NEW_RULE_ID",
            "category": {"id": "NEW_CAT", "name": "Nouvelle Catégorie"},
        },
        "message": "Erreur de test",
    }

    # ACT.
    category = service._get_or_create_rule_and_category(match)

    # ASSERT.
    assert category.lt_category_id == "NEW_CAT"
    db_rule = session.exec(select(Rule).where(Rule.lt_rule_id == "NEW_RULE_ID")).first()
    assert db_rule is not None
    assert db_rule.category_id == category.id


# ---------------------------------------------------------
# TEST CORRECTION COMPLÈTE AVEC MOCK API.
# ---------------------------------------------------------
def test_correct_submission_full_flow(service, setup_dictation_data, monkeypatch):
    """Vérifie le flux complet : Appel API LT + Calcul Scores."""
    # ARRANGE.
    _, submission = setup_dictation_data

    mock_response = MagicMock()
    mock_response.status_code = status.HTTP_200_OK
    mock_response.json.return_value = {
        "matches": [
            {
                "offset": 3,
                "length": 4,
                "rule": {
                    "id": "GENDER_BIAS",
                    "issueType": "grammar",
                    "category": {"id": "GRAMMAR", "name": "Grammaire"},
                },
                "message": "Erreur LT",
                "context": {"text": "Le gros chien"},
            }
        ]
    }
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: mock_response)

    # ACT.
    result = service.correct_submission(submission)

    # ASSERT.
    assert result.final_score > 0
    assert len(result.scores) > 0
    assert len(result.mistakes) > 0


def test_correct_submission_advanced_logic(
    service, session, setup_dictation_data, monkeypatch
):
    """Couvre le chargement de dictée, les types 'style' et la sélection de correction."""
    # ARRANGE.
    dictation, _ = setup_dictation_data

    sub = Submission(
        content_student="Le chate.",
        dictation_id=dictation.id,
        assessment_type=AssessmentType.INITIAL,
        student_id=1,
    )
    session.add(sub)
    session.commit()
    session.expire(sub, ["dictation"])

    mock_res = MagicMock()
    mock_res.status_code = status.HTTP_200_OK
    mock_res.json.return_value = {
        "matches": [
            {
                "rule": {
                    "id": "STYLE_ERR",
                    "issueType": "style",
                    "category": {"id": "S", "name": "S"},
                },
                "message": "Style",
                "offset": 0,
                "length": 2,
                "context": {"text": "Le"},
            },
            {
                "rule": {
                    "id": "CHAT_ERR",
                    "issueType": "grammar",
                    "category": {"id": "C", "name": "C"},
                },
                "message": "Erreur",
                "offset": 3,
                "length": 5,
                "context": {"text": "Le chate"},
                "replacements": [{"value": "chien"}, {"value": "chat"}],
            },
        ]
    }
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: mock_res)

    # ACT.
    result = service.correct_submission(sub)

    # ASSERT.
    assert result.dictation is not None
    assert result.mistakes[0].correct_word == "chat"
    assert len([m for m in result.mistakes if m.rule_id_lt == "STYLE_ERR"]) == 0


def test_correct_submission_inactive_category(
    service, session, setup_dictation_data, monkeypatch
):
    """Couvre le 'if not category: continue' dans la boucle LT."""
    # ARRANGE.
    dictation, _ = setup_dictation_data

    submission = Submission(
        student_id=1,
        dictation_id=dictation.id,
        content_student=dictation.content_reference,
        assessment_type=AssessmentType.INITIAL,
    )
    session.add(submission)
    session.commit()

    mock_res = MagicMock()
    mock_res.status_code = status.HTTP_200_OK
    mock_res.json.return_value = {
        "matches": [
            {
                "rule": {
                    "id": "RULE_TO_HIDE",
                    "issueType": "grammar",
                    "category": {"id": "CAT_HIDE", "name": "H"},
                },
                "message": "Err",
                "offset": 0,
                "length": 2,
                "context": {"text": "Le"},
            }
        ]
    }
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: mock_res)

    service._get_or_create_rule_and_category(mock_res.json.return_value["matches"][0])
    rule = session.exec(select(Rule).where(Rule.lt_rule_id == "RULE_TO_HIDE")).first()
    rule.is_active = False
    session.add(rule)
    session.commit()

    # ACT.
    result = service.correct_submission(submission)

    # ASSERT.
    assert len(result.mistakes) == 0


def test_correct_submission_manual_dictation_load(
    service, session, setup_dictation_data
):
    """Vérifie que la dictée est chargée manuellement si la relation est absente."""
    # ARRANGE.
    dictation, _ = setup_dictation_data

    sub = Submission(
        content_student="Le chat",
        dictation_id=dictation.id,
        assessment_type=AssessmentType.INITIAL,
        student_id=1,
    )
    session.add(sub)
    session.commit()

    session.expire(sub, ["dictation"])

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"matches": []}
    with patch("requests.post", return_value=mock_res):
        # ACT.
        service.correct_submission(sub)

    # ASSERT.
    assert sub.dictation is not None
    assert sub.dictation.id == dictation.id


# ---------------------------------------------------------
# TEST GÉNÉRATION HTML.
# ---------------------------------------------------------
def test_generate_html_text(service):
    """Vérifie que les balises span sont correctement insérées à l'envers."""
    # ARRANGE.
    text = "Le chat dort."
    mistake = Mistake(
        position_index=3,
        length=4,
        message="Pas beau",
        correct_word="chien",
        type_rousseau=MistakeType.AUTRE,
        malus_applied=1.0,
    )

    # ACT.
    html = service.generate_html_text(text, [mistake])

    # ASSERT.
    assert '<span class="faute"' in html
    assert 'data-corr="chien"' in html
    assert 'DATA-TYPE="MISTAKETYPE.AUTRE"' in html.upper()
    assert "chat" in html


# ---------------------------------------------------------
# TEST RECALCUL DES SCORES.
# ---------------------------------------------------------
def test_recalculate_dictation_scores(service, session, setup_dictation_data):
    """Vérifie que le changement de pénalité met à jour les scores."""
    # ARRANGE.
    dictation, submission = setup_dictation_data

    cat = Category(
        lt_category_id="TEST_CAT",
        name="Test",
        penalty=2.0,
        type_rousseau=MistakeType.AUTRE,
    )
    session.add(cat)
    session.flush()

    rule = Rule(
        lt_rule_id="TEST_RULE", category_id=cat.id, description="Desc", is_active=True
    )
    session.add(rule)
    session.flush()

    mistake = Mistake(
        submission_id=submission.id,
        rule_id_lt="TEST_RULE",
        category_id=cat.id,
        malus_applied=1.0,
        student_word="test",
        correct_word="test_ok",
        position_index=0,
        length=4,
        message="Message de test",
        context="test",
        type_rousseau=MistakeType.AUTRE,
    )
    session.add(mistake)
    session.commit()

    cat.penalty = 5.0
    session.add(cat)
    session.commit()

    # ACT.
    service.recalculate_dictation_scores(dictation)
    session.refresh(submission)

    # ASSERT.
    assert submission.final_score == 5.0


def test_recalculate_scores_with_inactive_rules(service, session, setup_dictation_data):
    """Couvre les branches 'not db_rule' et 'not rule.is_active' du recalcul."""
    # ARRANGE.
    dictation, submission = setup_dictation_data

    cat = Category(
        lt_category_id="CAT_X", name="X", penalty=1.0, type_rousseau=MistakeType.AUTRE
    )
    session.add(cat)
    session.flush()
    rule = Rule(
        lt_rule_id="RULE_X", category_id=cat.id, description="D", is_active=True
    )
    session.add(rule)
    session.flush()

    m = Mistake(
        submission_id=submission.id,
        rule_id_lt="RULE_X",
        category_id=cat.id,
        malus_applied=1.0,
        student_word="a",
        correct_word="b",
        position_index=0,
        length=1,
        message="M",
        context="C",
        type_rousseau=MistakeType.AUTRE,
    )
    session.add(m)
    session.commit()

    rule.is_active = False
    session.add(rule)
    session.commit()

    # ACT.
    service.recalculate_dictation_scores(dictation)
    session.refresh(m)

    # ASSERT.
    assert m.malus_applied == 0.0
    assert m.category_id is None


def test_recalculate_scores_missing_category(service, session, setup_dictation_data):
    """Vérifie que le recalcul ignore une faute si sa catégorie est introuvable."""
    # ARRANGE.
    dictation, submission = setup_dictation_data

    rule = Rule(
        lt_rule_id="GHOST_RULE",
        category_id=999,
        description="Règle sans catégorie",
        is_active=True,
    )
    session.add(rule)
    session.flush()

    m = Mistake(
        submission_id=submission.id,
        rule_id_lt="GHOST_RULE",
        category_id=None,
        malus_applied=1.5,
        student_word="x",
        correct_word="y",
        position_index=0,
        length=1,
        message="m",
        context="c",
        type_rousseau=MistakeType.AUTRE,
    )
    session.add(m)
    session.commit()

    # ACT.
    service.recalculate_dictation_scores(dictation)
    session.refresh(m)

    # ASSERT.
    assert m.malus_applied == 1.5


# ---------------------------------------------------------
# TEST CAS LIMITES (EDGE CASES).
# ---------------------------------------------------------
def test_correct_submission_empty_text(service, setup_dictation_data):
    """Vérifie qu'un texte vide donne un score de 0."""
    # ARRANGE.
    _, submission = setup_dictation_data
    submission.content_student = ""

    # ACT.
    result = service.correct_submission(submission)

    # ASSERT.
    assert result.final_score == 0.0


def test_correct_submission_lt_error(service, setup_dictation_data, monkeypatch):
    """Vérifie que le service continue même si LT crash (grâce au try/except)."""
    # ARRANGE.
    _, submission = setup_dictation_data

    def mock_post_fail(*args, **kwargs):
        raise Exception("LT Offline")

    monkeypatch.setattr(requests, "post", mock_post_fail)

    # ACT.
    result = service.correct_submission(submission)

    # ASSERT.
    assert result.final_score >= 0


# ---------------------------------------------------------
# TEST COVERAGE : INSERTION.
# ---------------------------------------------------------
def test_coverage_fidelity_insertion(service, session, setup_dictation_data):
    """Force l'entrée dans le bloc 'elif tag == insert'."""
    # ARRANGE.
    _, _ = setup_dictation_data
    ref = "Le chat"
    student = "Le chat noir"

    service._get_or_create_custom_rule_and_category("FIDELITY_ADDITION", "Add")

    # ACT.
    mistakes = service._check_fidelity(ref, student, [])

    # ASSERT.
    assert len(mistakes) == 1
    assert mistakes[0].rule_id_lt == "FIDELITY_ADDITION"
    assert mistakes[0].student_word == "noir"


def test_coverage_manual_dictation_load(service, session, setup_dictation_data):
    """Force l'entrée dans le bloc 'if not submission.dictation'."""
    # ARRANGE.
    dictation, _ = setup_dictation_data

    sub = Submission(
        student_id=1,
        dictation_id=dictation.id,
        content_student=dictation.content_reference,
        assessment_type=AssessmentType.INITIAL,
    )
    session.add(sub)
    session.commit()
    session.refresh(sub)

    set_committed_value(sub, "dictation", None)

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"matches": []}

    with patch("requests.post", return_value=mock_res):
        # ACT.
        service.correct_submission(sub)

    # ASSERT.
    assert sub.dictation is not None
    assert sub.dictation.id == dictation.id
