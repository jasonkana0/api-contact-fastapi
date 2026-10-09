from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional

# DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./contacts.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ContactDB(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    __table_args__ = (UniqueConstraint('email', name='uq_email'),)

Base.metadata.create_all(bind=engine)

# Pydantic
class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None

class Contact(ContactCreate):
    id: int
    class Config:
        from_attributes = True

# App
app = FastAPI(title="S2 API Contacts - FOR12A26-260")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"status": "OK", "project": "FOR12A26-260"}

@app.post("/contacts", response_model=Contact, status_code=201)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    exists = db.query(ContactDB).filter(ContactDB.email == contact.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    db_contact = ContactDB(**contact.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@app.get("/contacts", response_model=List[Contact])
def list_contacts(db: Session = Depends(get_db)):
    return db.query(ContactDB).all()

@app.get("/contacts/{contact_id}", response_model=Contact)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    c = db.query(ContactDB).filter(ContactDB.id == contact_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contact non trouvé")
    return c

@app.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    c = db.query(ContactDB).filter(ContactDB.id == contact_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contact non trouvé")
    db.delete(c)
    db.commit()
    return {"message": "Supprimé"}