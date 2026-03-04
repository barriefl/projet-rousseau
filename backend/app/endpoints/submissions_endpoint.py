import socket
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import Dictation, Mistake, Student, Submission
from app.schemas.submission_schema import SubmissionCreate, SubmissionResponse
from app.services.correction_service import CorrectionService

router = APIRouter()


@router.post(
    "/", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED
)
def create_submission(
    sub_in: SubmissionCreate, session: Session = Depends(get_session)
):

    student = session.exec(
        select(Student).where(Student.anonymous_id == sub_in.student_uuid)
    ).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Étudiant introuvable."
        )

    dictation = session.get(Dictation, sub_in.dictation_id)
    if not dictation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dictée introuvable."
        )

    submission = Submission(
        student_id=student.id,
        dictation_id=dictation.id,
        assessment_type=sub_in.assessment_type,
        content_student=sub_in.content_student,
        scores={},
    )

    session.add(submission)
    session.flush()

    lt_host_docker = "languagetool"
    lt_host_windows = "host.docker.internal"
    lt_url = "http://127.0.0.1:8010/v2/check"

    try:
        socket.gethostbyname(lt_host_docker)
        lt_url = f"http://{lt_host_docker}:8081/v2/check"
    except socket.gaierror:
        try:
            socket.gethostbyname(lt_host_windows)
            lt_url = f"http://{lt_host_windows}:8010/v2/check"
        except socket.gaierror:
            pass

    correction_service = CorrectionService(session, lt_url=lt_url)

    try:
        correction_service.correct_submission(submission)
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la correction : {str(e)}"
        )

    session.commit()
    session.refresh(submission)

    return {
        "message": "Dictée importée et analysée avec succès !",
        "submission_id": submission.id,
    }


@router.post(
    "/bulk",
    response_model=List[SubmissionResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_bulk_submissions(
    submissions_in: List[SubmissionCreate], session: Session = Depends(get_session)
):
    """Importe plusieurs copies d'un coup pour éviter de saturer le serveur."""
    lt_host_docker = "languagetool"
    lt_host_windows = "host.docker.internal"
    lt_url = "http://127.0.0.1:8010/v2/check"

    try:
        socket.gethostbyname(lt_host_docker)
        lt_url = f"http://{lt_host_docker}:8081/v2/check"
    except socket.gaierror:
        try:
            socket.gethostbyname(lt_host_windows)
            lt_url = f"http://{lt_host_windows}:8010/v2/check"
        except socket.gaierror:
            pass

    correction_service = CorrectionService(session, lt_url=lt_url)

    student_uuids = [sub.student_uuid for sub in submissions_in]
    students_db = session.exec(
        select(Student).where(Student.anonymous_id.in_(student_uuids))
    ).all()
    student_map = {s.anonymous_id: s.id for s in students_db}

    created_submissions = []

    for sub_in in submissions_in:
        student_id = student_map.get(sub_in.student_uuid)
        if not student_id:
            continue

        statement = select(Submission).where(
            Submission.student_id == student_id,
            Submission.dictation_id == sub_in.dictation_id,
            Submission.assessment_type == sub_in.assessment_type,
        )
        existing_sub = session.exec(statement).first()

        if existing_sub:
            existing_sub.content_student = sub_in.content_student
            existing_sub.final_score = 0.0
            existing_sub.scores = {}
            if hasattr(existing_sub, "html_text"):
                existing_sub.html_text = None

            if hasattr(existing_sub, "mistakes"):
                for mistake in existing_sub.mistakes:
                    session.delete(mistake)

            session.add(existing_sub)
            target_submission = existing_sub
        else:
            target_submission = Submission(
                student_id=student_id,
                dictation_id=sub_in.dictation_id,
                content_student=sub_in.content_student,
                assessment_type=sub_in.assessment_type,
                final_score=0.0,
                scores={},
            )
            session.add(target_submission)

        session.flush()

        try:
            correction_service.correct_submission(target_submission)
        except Exception as e:
            print(f"⚠️ Erreur de correction pour l'étudiant ID {student_id}: {e}")

        created_submissions.append((target_submission, sub_in.student_uuid))

    session.commit()

    result = []
    for sub, s_uuid in created_submissions:
        session.refresh(sub)
        result.append(
            {
                "id": sub.id,
                "created_at": sub.created_at.isoformat(),
                "student_uuid": s_uuid,
                "dictation_id": sub.dictation_id,
                "content_student": sub.content_student,
                "assessment_type": sub.assessment_type,
                "final_score": sub.final_score,
                "scores": sub.scores,
            }
        )

    return result


@router.get(
    "/", response_model=List[SubmissionResponse], status_code=status.HTTP_200_OK
)
def get_all_submissions(
    student_uuid: Optional[str] = None, session: Session = Depends(get_session)
):

    if student_uuid:
        student = session.exec(
            select(Student).where(Student.anonymous_id == student_uuid)
        ).first()

        if not student:
            return []

        statement = select(Submission).where(Submission.student_id == student.id)
        submissions = session.exec(statement).all()
    else:
        submissions = session.exec(select(Submission)).all()

    return [
        {
            "id": sub.id,
            "created_at": sub.created_at.isoformat(),
            "student_uuid": sub.student.anonymous_id,
            "dictation_id": sub.dictation_id,
            "assessment_type": sub.assessment_type,
            "content_student": sub.content_student,
            "final_score": sub.final_score,
            "scores": sub.scores,
        }
        for sub in submissions
    ]


@router.get("/{submission_id}", response_model=dict, status_code=status.HTTP_200_OK)
def get_submission_by_id(submission_id: int, session: Session = Depends(get_session)):
    sub = session.get(Submission, submission_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Copie introuvable."
        )

    mistakes = session.exec(
        select(Mistake).where(Mistake.submission_id == sub.id)
    ).all()

    correction_service = CorrectionService(session)
    html_text = correction_service.generate_html_text(sub.content_student, mistakes)

    return {
        "id": sub.id,
        "student_uuid": sub.student.anonymous_id if sub.student else None,
        "dictation_id": sub.dictation_id,
        "assessment_type": sub.assessment_type.value
        if hasattr(sub.assessment_type, "value")
        else sub.assessment_type,
        "content_student": sub.content_student,
        "final_score": sub.final_score,
        "scores": sub.scores,
        "html_text": html_text,
        "mistakes": [
            {
                "student_word": m.student_word,
                "correct_word": m.correct_word,
                "malus_applied": m.malus_applied,
                "type_rousseau": m.type_rousseau.value
                if hasattr(m.type_rousseau, "value")
                else m.type_rousseau,
                "message": m.message,
                "rule_id_lt": m.rule_id_lt,
                "position_index": m.position_index,
            }
            for m in mistakes
        ],
    }
