from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.utils.auth import ADMIN_PASSWORD, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Route de connexion.
    On utilise OAuth2PasswordRequestForm qui attend un champ 'username' et 'password'.
    Ici, on ignore le username, on vérifie juste le mot de passe.
    """
    if form_data.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": "admin"})

    return {"access_token": access_token, "token_type": "bearer"}
