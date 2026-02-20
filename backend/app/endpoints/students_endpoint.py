from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from typing import List

from app.database import get_session
from app.models import Student
from app.schemas.students_schema import StudentProgressionResponse, StudentResponse
from app.utils.crypto import decrypt_text

import uuid

router = APIRouter()

@router.get("/", response_model=List[StudentResponse])
def get_students(session: Session = Depends(get_session)):
    """Récupère la liste de tous les étudiants avec leurs noms déchiffrés."""
    
    students_db = session.exec(select(Student)).all()
    
    result = []
    
    for s in students_db:
        prenom_clair = decrypt_text(s.first_name_encrypted) or "Inconnu"
        nom_clair = decrypt_text(s.last_name_encrypted) or "Inconnu"
        
        groupe_clair = s.group.value if s.group else None
        
        result.append({
            "id": s.anonymous_id,
            "first_name": prenom_clair,
            "last_name": nom_clair,
            "promo": s.promo,
            "group": groupe_clair
        })
        
    return result

@router.delete("/{student_uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_uuid: uuid.UUID, session: Session = Depends(get_session)):
    """Supprime un étudiant et toutes ses dictées."""
    
    statement = select(Student).where(Student.anonymous_id == student_uuid)
    student = session.exec(statement).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Étudiant introuvable."
        )
        
    session.delete(student)
    session.commit()
    
    return

@router.get("/stats/progression", response_model=List[StudentProgressionResponse])
def get_students_progression(session: Session = Depends(get_session)):
    """Récupère la progression (Initial vs Final) de tous les étudiants."""
    
    students_db = session.exec(select(Student)).all()
    
    result = []
    
    for s in students_db:
        prenom_clair = decrypt_text(s.first_name_encrypted) or "Inconnu"
        nom_clair = decrypt_text(s.last_name_encrypted) or "Inconnu"
        groupe_clair = s.group.value if s.group else None
        
        score_initial = None
        score_final = None
        
        for sub in s.submissions:
            if sub.assessment_type.name == "INITIAL":
                score_initial = sub.final_score
            elif sub.assessment_type.name == "FINAL":
                score_final = sub.final_score
                
        progress = None
        if score_initial is not None and score_final is not None:
            progress = round(score_final - score_initial, 2)
            
        result.append({
            "id": s.anonymous_id,
            "first_name": prenom_clair,
            "last_name": nom_clair,
            "group": groupe_clair,
            "score_initial": score_initial,
            "score_final": score_final,
            "progress": progress
        })
        
    return result

@router.get("/{student_uuid}", response_model=StudentResponse, status_code=status.HTTP_200_OK)
def get_student_by_id(student_uuid: uuid.UUID, session: Session = Depends(get_session)):
    """Récupère les informations d'un étudiant spécifique via son UUID."""
    
    statement = select(Student).where(Student.anonymous_id == student_uuid)
    student = session.exec(statement).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Étudiant introuvable."
        )
        
    prenom_clair = decrypt_text(student.first_name_encrypted) or "Inconnu"
    nom_clair = decrypt_text(student.last_name_encrypted) or "Inconnu"
    groupe_clair = student.group.value if student.group else None
    
    return {
        "id": student.anonymous_id,
        "first_name": prenom_clair,
        "last_name": nom_clair,
        "promo": student.promo,
        "group": groupe_clair
    }