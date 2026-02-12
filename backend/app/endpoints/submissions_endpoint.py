from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.database import get_session
from app.models import Submission, Student, Dictation
from app.schemas.submission_schema import SubmissionCreate, SubmissionRead
from app.services.correction_service import CorrectionService

router = APIRouter()

@router.post("/", response_model=SubmissionRead, summary="Corriger une dictée.")
def process_correction(submission_in: SubmissionCreate, db: Session = Depends(get_session)):
    """
    Envoie une copie élève, lance la correction (LanguageTool + Diff) et renvoie la note.
    """
    student = db.get(Student, submission_in.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Étudiant introuvable.")

    dictation = db.get(Dictation, submission_in.dictation_id)
    if not dictation:
        raise HTTPException(status_code=404, detail="Dictée introuvable.")

    submission = Submission(
        student_id=submission_in.student_id,
        dictation_id=submission_in.dictation_id,
        assessment_type=submission_in.assessment_type,
        content_student=submission_in.content_student,
        final_score=0.0,
        scores={}
    )
    
    db.add(submission)
    db.commit()
    db.refresh(submission)

    service = CorrectionService(db)
    
    try:
        corrected_submission = service.correct_submission(submission)
        
        db.add(corrected_submission)
        db.commit()
        db.refresh(corrected_submission)
        
        return corrected_submission

    except Exception as e:
        print(f"❌ Erreur critique correction : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la correction: {str(e)}")

@router.get("/{submission_id}", response_model=SubmissionRead, summary="Consulter un résultat.")
def get_correction_result(submission_id: int, db: Session = Depends(get_session)):
    """Récupère une copie déjà corrigée."""
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Copie introuvable.")
    return submission