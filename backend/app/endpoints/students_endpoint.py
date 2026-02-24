from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from typing import List

from app.database import get_session
from app.models import Student
from app.schemas.student_schema import StudentCreate, StudentProgressionResponse, StudentResponse, StudentUpdate
from app.utils.crypto import decrypt_text, encrypt_text

import uuid

router = APIRouter()

def _get_val(field):
    """Fonction utilitaire pour extraire la valeur d'un Enum proprement s'il existe."""
    return field.value if field and hasattr(field, 'value') else field

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
            "group": _get_val(s.group),
            "appetence_level": _get_val(s.appetence_level),
            "has_library": _get_val(s.has_library),
            "reading_support": _get_val(s.reading_support),
            "reading_works": _get_val(s.reading_works),
            "motive": _get_val(s.motive),
            "parent_1_degree": _get_val(s.parent_1_degree),
            "parent_1_csp": _get_val(s.parent_1_csp),
            "parent_2_degree": _get_val(s.parent_2_degree),
            "parent_2_csp": _get_val(s.parent_2_csp),
            "declared_level": _get_val(s.declared_level)
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
    
    return {
        "id": student.anonymous_id,
        "first_name": prenom_clair,
        "last_name": nom_clair,
        "promo": student.promo,
        "group": _get_val(student.group),
        "appetence_level": _get_val(student.appetence_level),
        "has_library": _get_val(student.has_library),
        "reading_support": _get_val(student.reading_support),
        "reading_works": _get_val(student.reading_works),
        "motive": _get_val(student.motive),
        "parent_1_degree": _get_val(student.parent_1_degree),
        "parent_1_csp": _get_val(student.parent_1_csp),
        "parent_2_degree": _get_val(student.parent_2_degree),
        "parent_2_csp": _get_val(student.parent_2_csp),
        "declared_level": _get_val(student.declared_level)
    }

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(student_in: StudentCreate, session: Session = Depends(get_session)):
    """Crée un nouvel étudiant avec toutes ses données sociodémographiques."""
    
    prenom_enc = encrypt_text(student_in.first_name)
    nom_enc = encrypt_text(student_in.last_name)
    
    new_student = Student(
        anonymous_id=uuid.uuid4(),
        first_name_encrypted=prenom_enc,
        last_name_encrypted=nom_enc,
        promo=student_in.promo,
        group=student_in.group,
        appetence_level=student_in.appetence_level,
        has_library=student_in.has_library,
        reading_support=student_in.reading_support,
        reading_works=student_in.reading_works,
        motive=student_in.motive,
        parent_1_degree=student_in.parent_1_degree,
        parent_1_csp=student_in.parent_1_csp,
        parent_2_degree=student_in.parent_2_degree,
        parent_2_csp=student_in.parent_2_csp,
        declared_level=student_in.declared_level
    )
    
    session.add(new_student)
    session.commit()
    session.refresh(new_student)
    
    return {
        "id": new_student.anonymous_id,
        "first_name": student_in.first_name,
        "last_name": student_in.last_name,
        "promo": new_student.promo,
        "group": _get_val(new_student.group),
        "appetence_level": _get_val(new_student.appetence_level),
        "has_library": _get_val(new_student.has_library),
        "reading_support": _get_val(new_student.reading_support),
        "reading_works": _get_val(new_student.reading_works),
        "motive": _get_val(new_student.motive),
        "parent_1_degree": _get_val(new_student.parent_1_degree),
        "parent_1_csp": _get_val(new_student.parent_1_csp),
        "parent_2_degree": _get_val(new_student.parent_2_degree),
        "parent_2_csp": _get_val(new_student.parent_2_csp),
        "declared_level": _get_val(new_student.declared_level)
    }

@router.patch("/{student_uuid}", response_model=StudentResponse, status_code=status.HTTP_200_OK)
def update_student(student_uuid: uuid.UUID, student_in: StudentUpdate, session: Session = Depends(get_session)):
    """Met à jour les informations d'un étudiant existant."""
    
    statement = select(Student).where(Student.anonymous_id == student_uuid)
    db_student = session.exec(statement).first()
    
    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Étudiant introuvable."
        )
        
    update_data = student_in.model_dump(exclude_unset=True)
    
    if "first_name" in update_data and update_data["first_name"] is not None:
        db_student.first_name_encrypted = encrypt_text(update_data["first_name"])
        del update_data["first_name"]
        
    if "last_name" in update_data and update_data["last_name"] is not None:
        db_student.last_name_encrypted = encrypt_text(update_data["last_name"])
        del update_data["last_name"]
        
    for key, value in update_data.items():
        setattr(db_student, key, value)
        
    session.add(db_student)
    session.commit()
    session.refresh(db_student)
    
    prenom_clair = decrypt_text(db_student.first_name_encrypted) or "Inconnu"
    nom_clair = decrypt_text(db_student.last_name_encrypted) or "Inconnu"
    
    return {
        "id": db_student.anonymous_id,
        "first_name": prenom_clair,
        "last_name": nom_clair,
        "promo": db_student.promo,
        "group": _get_val(db_student.group),
        "appetence_level": _get_val(db_student.appetence_level),
        "has_library": _get_val(db_student.has_library),
        "reading_support": _get_val(db_student.reading_support),
        "reading_works": _get_val(db_student.reading_works),
        "motive": _get_val(db_student.motive),
        "parent_1_degree": _get_val(db_student.parent_1_degree),
        "parent_1_csp": _get_val(db_student.parent_1_csp),
        "parent_2_degree": _get_val(db_student.parent_2_degree),
        "parent_2_csp": _get_val(db_student.parent_2_csp),
        "declared_level": _get_val(db_student.declared_level)
    }