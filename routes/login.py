from pymongo import MongoClient
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from schemas.schemas import Admin
from typing import List,Dict,Union
from datetime import datetime,timedelta
from bson.objectid import ObjectId
from passlib.context import CryptContext
from pydantic import BaseModel
from jose import JWTError, jwt
from globals import *
from config.database import database


ouath2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
login_ruta = APIRouter()

SECRET_KEY = "446a1b491cdb18e85bb19c27ee7283f155fbf55573fc6ea39b3c1e551e4eb04c"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120


class Hasher():
    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)
    def get_password_hash(password):
       
        return pwd_context.hash(password)
class Token(BaseModel):
    access_token: str
    token_type: str
class TokenData(BaseModel):
    username: Union[str, None] = None

async def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token : str = Depends(ouath2_scheme)):
    db = database
    credential_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credential_exception
        token_data = TokenData(username=email)
    except JWTError:
        raise credential_exception
    admin = db["admin"].find_one({"email" : token_data.username})
    if admin is None:
        raise credential_exception
    admin["password"] = ""
    return admin


async def get_current_active_admin(current_admin: Admin = Depends(get_current_user)):
    if current_admin is None:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")
    return current_admin




async def authenticate_admin(form_data: OAuth2PasswordRequestForm = Depends()):
    db = database
    admin = db["admin"].find_one({"email": form_data.username})
    if admin == None:
        raise HTTPException(status_code=400, detail="Email o Password incorrecto")
    password = Hasher.verify_password(form_data.password, admin['password'])
    if not password:
        raise HTTPException(status_code=400, detail="Email o Password incorrecto")
    return admin

async def get_current_user(token: str = Depends(ouath2_scheme)):
    db = database
    admin = db["admin"].find_one({"email" : token})
    return admin

@login_ruta.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    admin = await authenticate_admin(form_data)
    if not admin:
        raise HTTPException(status_code=400, detail="Email o Password incorrecto")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": admin["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@login_ruta.get('/admin/yo', response_model=Admin,status_code=200)
async def read_users_me(current_admin: Admin = Depends(get_current_active_admin)):
    return current_admin
