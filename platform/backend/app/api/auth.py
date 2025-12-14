from fastapi import APIRouter, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
def issue_token(form_data: OAuth2PasswordRequestForm = None):
    if not form_data:
        raise HTTPException(status_code=400, detail="Missing credentials")
    # Simple placeholder: accept any username/password for now
    token = create_access_token(username=form_data.username, role="admin")
    return {"access_token": token, "token_type": "bearer"}
