from pymongo import MongoClient
from fastapi import APIRouter, HTTPException, Depends
from schemas.schemas import Institucion,Institucion_Editar
from typing import List,Dict
from datetime import datetime
from bson.objectid import ObjectId
from fastapi.security import OAuth2PasswordBearer
from routes.login import read_users_me

from globals import *



institucion_ruta = APIRouter(dependencies=[Depends(read_users_me)])

@institucion_ruta.get('/institucion/obtener/texto/{nombre}', response_model=List[Institucion],status_code=200)
async def get_institucion(nombre: str,depends = Depends(read_users_me)):
    conn = MongoClient(MONGO_STRING)["chile3d"]
    index = conn["institucion"].create_index([('nombre', 'text')])
    instituciones = list(conn["institucion"].find({"$text": {"$search": nombre}}))
    return instituciones

@institucion_ruta.get('/institucion', response_model=List[Institucion],status_code=200)
async def get_institucion(depends = Depends(read_users_me)):
    db = MongoClient(MONGO_STRING)["chile3d"]
    instituciones = list(db.institucion.find({}))
    return instituciones

@institucion_ruta.get('/institucion/obtener/id/{id}', response_model=Institucion,status_code=200)
async def get_institucion(id: str,depends = Depends(read_users_me)):
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
async def crear_institucion(institucion: Institucion,depends = Depends(read_users_me)):
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
async def update_institucion(id: str, institucion: Institucion_Editar,depends = Depends(read_users_me)):
    db = MongoClient(MONGO_STRING)["chile3d"]
    institucion = institucion.dict()
    notNullItems = {k: v for k, v in institucion.dict().items() if v is not None and v != ""}
    institucion['updated_at'] = datetime.utcnow()
    if db.institucion.update_one({"_id": id}, {"$set": notNullItems}):
        return institucion  
    else:
        raise HTTPException(status_code=404, detail="Institucion no encontrada")
    

@institucion_ruta.delete('/institucion/eliminar/{id}',status_code=204)
async def delete_institucion(id: str, depends = Depends(read_users_me)):
    db = MongoClient(MONGO_STRING)["chile3d"]
    if db.institucion.delete_one({"_id": id}):
        return {"message": "Institucion eliminada"}
    else:
        raise HTTPException(status_code=404, detail="Institucion no encontrada")
   
   
