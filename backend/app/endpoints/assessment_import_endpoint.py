from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session

from app.database import get_session
from app.schemas.assessment_schema import (
    AssessmentExecuteRequest,
    AssessmentPreviewResponse,
    AssessmentType,
)
from app.services.assessment_import_service import AssessmentImportService

router = APIRouter(prefix="/import/assessments", tags=["Importation Evaluations"])


@router.post(
    "/preview", response_model=AssessmentPreviewResponse, status_code=status.HTTP_200_OK
)
async def preview_assessment_import(
    promotion_id: int = Form(...),
    tool_id: int = Form(...),
    assessment_type: AssessmentType = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier doit être au format CSV.",
        )

    try:
        file_content = await file.read()
        service = AssessmentImportService(session)
        return service.analyze_file(
            promotion_id, tool_id, assessment_type, file_content
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/execute")
def execute_assessment_import(
    request: AssessmentExecuteRequest, session: Session = Depends(get_session)
) -> Dict[str, Any]:
    try:
        service = AssessmentImportService(session)
        return service.execute_import(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur d'enregistrement : {str(e)}",
        )
