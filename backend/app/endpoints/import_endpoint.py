from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session

from app.database import get_session
from app.schemas.import_schema import ImportExecuteRequest, ImportPreviewResponse
from app.services.import_service import ImportService

router = APIRouter(prefix="/import", tags=["Importation"])


@router.post(
    "/preview", response_model=ImportPreviewResponse, status_code=status.HTTP_200_OK
)
async def preview_import(
    promotion_id: int = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """
    Étape 1 : Reçoit le fichier CSV, l'analyse et renvoie un aperçu des
    correspondances (Levenshtein) et des groupes à créer, sans rien sauvegarder.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier doit être au format CSV.",
        )

    try:
        file_content = await file.read()

        service = ImportService(session)
        preview_result = service.analyze_import(promotion_id, file_content)

        return preview_result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur lors de l'analyse du fichier : {str(e)}",
        )


@router.post("/execute", status_code=status.HTTP_200_OK)
def execute_import(
    request: ImportExecuteRequest, session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Étape 2 : Reçoit les choix validés par l'utilisateur (JSON) et exécute l'importation (création/mise à jour) de manière sécurisée (Transaction).
    """
    try:
        service = ImportService(session)
        result = service.execute_import(request)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur critique lors de la sauvegarde, tout a été annulé. Détails : {str(e)}",
        )
