from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
import uuid

from app.database import get_session
from app.models import Submission, Student, Dictation
from app.schemas.submission_schema import SubmissionCreate, SubmissionResponse

router = APIRouter()

@router.post("/", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_submission(sub_in: SubmissionCreate, session: Session = Depends(get_session)):
    
    student = session.exec(select(Student).where(Student.anonymous_id == sub_in.student_uuid)).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Étudiant introuvable.")

    dictation = session.get(Dictation, sub_in.dictation_id)
    if not dictation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dictée introuvable.")

    new_submission = Submission(
        student_id=student.id,
        dictation_id=dictation.id,
        assessment_type=sub_in.assessment_type,
        content_student=sub_in.content_student
    )
    
    session.add(new_submission)
    session.commit()
    session.refresh(new_submission)
    
    return {
        "id": new_submission.id,
        "student_uuid": student.anonymous_id,
        "dictation_id": new_submission.dictation_id,
        "assessment_type": new_submission.assessment_type,
        "content_student": new_submission.content_student,
        "final_score": new_submission.final_score,
        "scores": new_submission.scores
    }

@router.get("/", response_model=List[SubmissionResponse], status_code=status.HTTP_200_OK)
def get_all_submissions(session: Session = Depends(get_session)):
    submissions_db = session.exec(select(Submission)).all()
    
    result = []
    for sub in submissions_db:
        student_uuid = sub.student.anonymous_id if sub.student else None
        
        result.append({
            "id": sub.id,
            "student_uuid": student_uuid,
            "dictation_id": sub.dictation_id,
            "assessment_type": sub.assessment_type,
            "content_student": sub.content_student,
            "final_score": sub.final_score,
            "scores": sub.scores
        })
        
    return result

@router.get("/{submission_id}", response_model=SubmissionResponse, status_code=status.HTTP_200_OK)
def get_submission_by_id(submission_id: int, session: Session = Depends(get_session)):
    sub = session.get(Submission, submission_id)
    
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Copie introuvable.")
        
    return {
        "id": sub.id,
        "student_uuid": sub.student.anonymous_id,
        "dictation_id": sub.dictation_id,
        "assessment_type": sub.assessment_type,
        "content_student": sub.content_student,
        "final_score": sub.final_score,
        "scores": sub.scores
    }