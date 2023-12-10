from datetime import datetime
from typing import List, Union
from bson.objectid import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel
from config.database import database
from globals import *
from routes.login import read_users_me
from schemas.schemas import Admin,AdminGet,AdminEditar

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
admin_ruta = APIRouter()



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



@admin_ruta.get('/admin', response_model=List[AdminGet],status_code=200)
async def get_admin(
    fetch: int = 0,
    skip: int = 0,
    institucion_id: str = None,
    nombre: str = None,
    email: str = None,
    rut: str = None,
    celular: str = None,
    institucion: str = None,
    area_trabajo: str = None,
    superadmin = Depends(read_users_me)
):
    db = database
    query = {}
    if db["admin"].find_one({"email": superadmin["email"]})["is_superadmin"] == False:
        raise HTTPException(status_code=401, detail="No autorizado")
    if institucion_id:
        query["institucion_id"] = institucion_id
    if nombre:
        query["nombre"] = {"$regex": f".*{nombre}.*", "$options": "i"}
    if email:
        query["email"] = {"$regex": f".*{email}.*", "$options": "i"}
    if rut:
        query["rut"] = {"$regex": f".*{rut}.*", "$options": "i"}
    if celular:
        query["celular"] = {"$regex": f".*{celular}.*", "$options": "i"}
    if institucion:
        query["institucion"] = {"$regex": f".*{institucion}.*", "$options": "i"}
    if area_trabajo:
        query["area_trabajo"] = {"$regex": f".*{area_trabajo}.*", "$options": "i"}
    
    projection = {"password": 0,"is_superadmin": 0,"created_at": 0}
    admins = list(db["admin"].find(query,projection).skip(skip).limit(fetch))
    return admins

@admin_ruta.get('/admin/{id}',status_code=200)
async def get_admin(id: str,superadmin = Depends(read_users_me)):
    db = database
    if db["admin"].find_one({"email": superadmin["email"]})["is_superadmin"] == False:
        raise HTTPException(status_code=401, detail="No autorizado")
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Id no válido")

    admin = db["admin"].find_one({"id": ObjectId(id)})
    if admin:
        return list(admin)
    return HTTPException(status_code=404, detail="Admin no encontrado")





@admin_ruta.post('/admin', response_model=Admin,status_code=201)
async def crear_admin(admin: Admin,superadmin = Depends(read_users_me)):
    db = database
    if db["admin"].find_one({"email": superadmin["email"]})["is_superadmin"] == False:
        raise HTTPException(status_code=401, detail="No autorizado")
    admin = admin.dict()
    if db["admin"].find_one({"email": admin["email"]}) == None:
        admin["password"] = Hasher.get_password_hash(admin["password"])
        admin['created_at'] = datetime.utcnow()
        db["admin"].insert_one(admin)
        return admin
    else:
        raise HTTPException(status_code=400, detail="Email ya existe")
    

@admin_ruta.put('/admin/{id}',response_model=AdminGet)
async def update_admin(id: str, admin: AdminEditar,superadmin = Depends(read_users_me)):
    db = database
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Id no válido")
    if db["admin"].find_one({"email": superadmin["email"]})["is_superadmin"] == False:
        raise HTTPException(status_code=401, detail="No autorizado")

    admin = admin.dict()
    admin["updated_at"] = datetime.utcnow()
    admin["institucion"] = db["institucion"].find_one({"id": ObjectId(admin["institucion_id"])})["nombre"]
    update = db["admin"].update_one({"id": ObjectId(id)}, {"$set": admin})
    updated_obj = db["admin"].find_one({"id": ObjectId(id)})
    if update.modified_count > 0:
        return updated_obj
    return HTTPException(status_code=404, detail="Admin no encontrado")

@admin_ruta.delete('/admin/{id}',status_code=204)
async def delete_admin(id: str, superadmin = Depends(read_users_me)):
    db = database
    if db["admin"].find_one({"email": superadmin["email"]})["is_superadmin"] == False:
        raise HTTPException(status_code=401, detail="No autorizado")
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Id no válido")
    deleted_admin = db["admin"].delete_one({"id": ObjectId(id)})
    if deleted_admin.deleted_count > 0:
        return {"message": "Admin eliminado"}
    else:
        raise HTTPException(status_code=404, detail="Admin no encontrado")
