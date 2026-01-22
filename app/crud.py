from sqlalchemy.orm import Session
from . import models, schemas, auth_utils
from .models import History


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed = auth_utils.hash_password(user.password)
    db_user = models.User(username=user.username, email=user.email, password_hash=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_history(db, user_id: int, file_name: str, scan_type: str, text: str):
    record = History(
        user_id=user_id,
        file_name=file_name,
        scan_type=scan_type,
        extracted_text=text
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_user_history(db, user_id: int):
    return db.query(History).filter(History.user_id == user_id).order_by(History.id.desc()).all()

def delete_history(db, history_id: int, user_id: int):
    record = db.query(History).filter(
        History.id == history_id,
        History.user_id == user_id
    ).first()
    if record:
        db.delete(record)
        db.commit()
    return record
