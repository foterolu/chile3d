from pymongo import MongoClient
from fastapi import APIRouter, HTTPException, Depends
from schemas.schemas import Institucion,InstitucionEditar
from typing import List,Dict
from datetime import datetime
from bson.objectid import ObjectId
from fastapi.security import OAuth2PasswordBearer
from routes.login import read_users_me

from globals import *



institucion_ruta = APIRouter(dependencies=[Depends(read_users_me)])


@institucion_ruta.get('/institutions', response_model=List[Institucion],status_code=200)
async def get_institucion( nombre: str = None,
    descripcion: str = None,
    sitio_web: str = None,
    email: str = None,
    telefono: str = None,
    direccion: str = None,
    area_trabajo: str = None,
    tipo_institucion: str = None,
    fecha_incio: str = None,
    fecha_fin: str = None,
):
    conn=  MongoClient(MONGO_STRING)["chile3d"]["institucion"]
    query = {}

    if nombre:
        query["nombre"] = nombre
    if descripcion:
        query["descripcion"] = descripcion
    if sitio_web:
        query["sitio_web"] = sitio_web
    if email:
        query["email"] = email
    if telefono:
        query["telefono"] = telefono
    if direccion:
        query["direccion"] = direccion
    if area_trabajo:
        query["area_trabajo"] = area_trabajo
    if tipo_institucion:
        query["tipo_institucion"] = tipo_institucion
    if fecha_incio and fecha_fin:
        try:
            fecha_incio = datetime.strptime(fecha_incio, '%Y-%m-%d')
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
            query["created_at"] = {"$gte": fecha_incio, "$lt": fecha_fin}
        except Exception as e:
            raise HTTPException(status_code=400, detail="Formato de fecha incorrecto")

    return list(
        conn.find(query)
    )

@institucion_ruta.get('/institutions/{id}', response_model=Institucion,status_code=200)
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

@institucion_ruta.post('/institutions', response_model=Institucion,status_code=201)
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
  
    

@institucion_ruta.put('/institutions/{id}',status_code=204)
async def update_institucion(id: str, institucion: InstitucionEditar,depends = Depends(read_users_me)):
    db = MongoClient(MONGO_STRING)["chile3d"]
    institucion = institucion.dict()
    notNullItems = {k: v for k, v in institucion.items() if v is not None and v != ""}
    institucion['updated_at'] = datetime.utcnow()
    result = db.institucion.update_one({"id": ObjectId(id)}, {"$set": notNullItems})
    if result.matched_count >0:
        return institucion  
    else:
        raise HTTPException(status_code=404, detail="Institucion no encontrada")
    

@institucion_ruta.delete('/institutions/{id}',status_code=204)
async def delete_institucion(id: str, depends = Depends(read_users_me)):
    db = MongoClient(MONGO_STRING)["chile3d"]
    if db.institucion.delete_one({"id": ObjectId(id)}):
        return {"message": "Institucion eliminada"}
    else:
        raise HTTPException(status_code=404, detail="Institucion no encontrada")
   
   
