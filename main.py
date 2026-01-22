from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, crud, auth_utils
from app.database import SessionLocal, engine, Base
from dotenv import load_dotenv
import os
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Generator
from fastapi import File, UploadFile
from app import ocr_utils


load_dotenv()

# create tables if not existing
Base.metadata.create_all(bind=engine)

app = FastAPI(title="OCR Backend (Auth)")

from fastapi.middleware.cors import CORSMiddleware


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # during development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Dependency to get DB session
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/auth/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check existing username/email
    if crud.get_user_by_username(db, user_in.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    if crud.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = crud.create_user(db, user_in)
    return user

@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm gives username and password fields (we'll accept username or email)
    identifier = form_data.username
    password = form_data.password

    # first try by email then username
    user = crud.get_user_by_email(db, identifier) or crud.get_user_by_username(db, identifier)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect credentials")

    if not auth_utils.verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect credentials")

    access_token = auth_utils.create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}

# helper to get current user
from fastapi import Security
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = auth_utils.decode_access_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.post("/ocr/simple-pdf")
async def simple_pdf_scan(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pdf_bytes = await file.read()
    text = ocr_utils.extract_text_simple_pdf(pdf_bytes)

    # Save to history
    crud.create_history(
        db,
        user_id=current_user.id,
        file_name=file.filename,
        scan_type="simple_pdf",
        text=text,
    )

    return {"extracted_text": text}



@app.post("/ocr/scanned-pdf")
async def scanned_pdf_scan(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pdf_bytes = await file.read()
    text = ocr_utils.extract_text_scanned_pdf(pdf_bytes)

    crud.create_history(
        db,
        user_id=current_user.id,
        file_name=file.filename,
        scan_type="scanned_pdf",
        text=text,
    )

    return {"extracted_text": text}



@app.post("/ocr/image")
async def image_scan(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    image_bytes = await file.read()
    text = ocr_utils.extract_text_from_image(image_bytes)

    crud.create_history(
        db,
        user_id=current_user.id,
        file_name=file.filename,
        scan_type="image",
        text=text,
    )

    return {"extracted_text": text}



@app.post("/ocr/auto-detect")
async def auto_detect_scan(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content = await file.read()

    text, scan_type = ocr_utils.auto_detect_extract(file.filename, content)

    crud.create_history(
        db,
        user_id=current_user.id,
        file_name=file.filename,
        scan_type=scan_type,
        text=text,
    )

    return {"extracted_text": text}

@app.get("/history", response_model=list[schemas.HistoryOut])
def get_history(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.get_user_history(db, current_user.id)


@app.delete("/history/{history_id}")
def delete_history(
    history_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(models.History).filter(
        models.History.id == history_id,
        models.History.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    db.delete(record)
    db.commit()

    return {"message": "Deleted successfully"}



@app.get("/me", response_model=schemas.UserOut)
def read_me(current_user = Depends(get_current_user)):
    return current_user



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
