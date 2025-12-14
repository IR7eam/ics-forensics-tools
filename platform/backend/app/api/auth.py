from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import Role, create_access_token
from app.utils.users import load_demo_users

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
def issue_token(form_data: OAuth2PasswordRequestForm = Depends()):
    registry = load_demo_users()
    record = registry.get(form_data.username)
    if not record:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    expected_password, role = record
    if expected_password != form_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(username=form_data.username, role=role.value)
    return {"access_token": token, "token_type": "bearer"}
