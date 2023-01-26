from pymongo import MongoClient
from fastapi import APIRouter, HTTPException, Depends
from schemas.schemas import Institucion
from typing import List,Dict
from datetime import datetime
from bson.objectid import ObjectId
from fastapi.security import OAuth2PasswordBearer

from globals import *



institucion_ruta = APIRouter()

@institucion_ruta.get('/institucion', response_model=List[Institucion],status_code=200)
async def get_institucion():
    db = MongoClient(MONGO_STRING)["chile3d"]
    instituciones = list(db.institucion.find({}))

    return instituciones

@institucion_ruta.get('/institucion/obtener/{id}', response_model=Institucion,status_code=200)
async def get_institucion(id: str):
    try:
        db = MongoClient(MONGO_STRING)["chile3d"]
        institucion = db.institucion.find_one({"id": ObjectId(id)})
        if institucion:

            return institucion
        else:
            raise HTTPException(status_code=404, detail="Institucion no encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@institucion_ruta.post('/institucion/crear', response_model=Institucion,status_code=201)
async def crear_institucion(institucion: Institucion):
    db = MongoClient(MONGO_STRING)["chile3d"]
    institucion = institucion.dict()
    email = institucion['email']
    if db.institucion.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email ya existe")
    else:
        institucion['created_at'] = datetime.utcnow()
        db.institucion.insert_one(institucion)
        return institucion
  
    

@institucion_ruta.put('/institucion/actualizar/{id}',status_code=204)
async def update_institucion(id: str, institucion: Institucion):
    db = MongoClient(MONGO_STRING)["chile3d"]
    institucion = institucion.dict()
    institucion['updated_at'] = datetime.utcnow()
    if db.institucion.update_one({"_id": id}, {"$set": institucion}):

        return institucion
    else:
        raise HTTPException(status_code=404, detail="Institucion no encontrada")
   
   
