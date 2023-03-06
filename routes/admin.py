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
from routes.login import read_users_me




pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
admin_ruta = APIRouter(dependencies=[Depends(read_users_me)])



SECRET_KEY = "446a1b491cdb18e85bb19c27ee7283f155fbf55573fc6ea39b3c1e551e4eb04c"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


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



@admin_ruta.get('/admin', response_model=List[Admin],status_code=200)
async def get_admin():
    db = MongoClient(MONGO_STRING)["chile3d"]
    admins = list(db["admin"].find({}))

    return admins

@admin_ruta.get('/admin/obtener/{id}', response_model=Admin,status_code=200)
async def get_admin(id: str):
    try:
        db = MongoClient(MONGO_STRING)["chile3d"]
        admin = db["admin"].find_one({"id": ObjectId(id)})
        if admin:

            return admin
        else:
            raise HTTPException(status_code=404, detail="Admin no encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@admin_ruta.post('/admin/crear', response_model=Admin,status_code=201)
async def crear_admin(admin: Admin):
    db = MongoClient(MONGO_STRING)["chile3d"]
    admin = admin.dict()
    if db["admin"].find_one({"email": admin["email"]}) == None:
        admin["password"] = Hasher.get_password_hash(admin["password"])
        admin['created_at'] = datetime.utcnow()
        db["admin"].insert_one(admin)
        return admin
    else:
        raise HTTPException(status_code=400, detail="Email ya existe")
    

@admin_ruta.put('/admin/actualizar/{id}',status_code=204)
async def update_admin(id: str, admin: Admin):
    db = MongoClient(MONGO_STRING)["chile3d"]
    admin = admin.dict()
    admin['updated_at'] = datetime.utcnow()
    db["admin"].update