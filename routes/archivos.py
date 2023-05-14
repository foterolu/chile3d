
from typing import List,Dict
from fastapi import FastAPI, Request, Response,Depends
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from PIL.TiffTags import TAGS
from pymongo import MongoClient
from schemas.schemas import Archivo,Archivo_edit,Admin_institucion
from services.laz_services import LazServices
from services.shp_services import ShapefileServices
from services.tif_services import TifServices
from fastapi import File, UploadFile, HTTPException
from fastapi import APIRouter
from globals import *
from routes.login import read_users_me
from pathlib import Path
from bson.objectid import ObjectId
import datetime
import geojson
import subprocess as sp
import json
import pyproj
import os
import zipfile
import io
import pdb
import requests
import rasterio
import geojson_pydantic

archivos_ruta = APIRouter()
EXTENSIONS = ('.shp' ,'.tif','.tiff','.laz','.las')


@archivos_ruta.get('/archivos/obtener/texto/{nombre}', response_model=List[Archivo],status_code=200)
async def get_archivos(nombre: str, depends = Depends(read_users_me)):
    conn = MongoClient(MONGO_STRING)["chile3d"]
    index = conn["archivos"].create_index([('nombre', 'text')])
    archivos = list(conn["archivos"].find({"$text": {"$search": nombre}}))
    return archivos


@archivos_ruta.get('/archivos/{pagina}/{cantidad}', response_model=List[Archivo],status_code=200)
async def get_all_archivos(
    pagina: int = 0,
    cantidad: int = 10,
):
    conn = MongoClient(MONGO_STRING)["chile3d"]
    data = list(conn["archivos"].find().skip(pagina).limit(cantidad))
    return data


@archivos_ruta.get('/archivos/{id}')
async def get_archivo():
    conn = MongoClient(MONGO_STRING)["chile3d"]

    return conn["archivos"].find_one({"id": ObjectId(id)})

@archivos_ruta.post("/archivos/descargar")
async def file_response(request: Request):
    body = await request.body()
    try:
        data = json.loads(body)['files']
        
        url_list = list(data)
        return zipfiles(url_list)

    except Exception as e:
        raise HTTPException(status_code=400, detail="Error al descargar archivos")
    #return FileResponse()

    

@archivos_ruta.post("/archivos/buscar/poligono",status_code=200,response_model=List[Archivo])
async def buscar_archivos(request: geojson_pydantic.FeatureCollection[geojson_pydantic.Polygon,Dict]):
    conn = MongoClient(MONGO_STRING)["chile3d"]
    #TODO: agregar query within
    data = list(conn["archivos"].find())
    inside = []
    body = request
    MyPolygon = geojson_pydantic.FeatureCollection(features=body.features)
    gj = MyPolygon.dict()

    for features in gj['features']:
        
        for archivo in data:
            modelo = Archivo(**archivo)
            minx = archivo["minx"]
            miny = archivo["miny"]
            maxx = archivo["maxx"]
            maxy = archivo["maxy"]
            p1 = Point(minx, miny)
            p2 = Point(minx, maxy)
            p3 = Point(maxx, maxy)
            p4 = Point(maxx, miny)
            polygon = Polygon(features['geometry']['coordinates'][0])
       
            for point in [p1, p2, p3, p4]:
                if polygon.contains(point):
                    inside.append(modelo)
                    break
    return inside    

@archivos_ruta.post("/archivos/subir",status_code=201)
def subir_archivo(file : UploadFile  = File(...), admin = Depends(read_users_me)):
    os.makedirs(WORKING_DIRECTORY, exist_ok=True)
    print(admin)
    admin["admin_id"] = admin["id"]
    admin_institucion = Admin_institucion(**admin)
    name = file.filename
    if file.filename.lower().endswith(EXTENSIONS):
        try:
            contents = file.file.read()
            if file.filename.lower().endswith('.zip'): 
                pass
            elif file.filename.lower().endswith('.tif'):
                with open(WORKING_DIRECTORY+ file.filename, 'wb') as f:
                    f.write(contents)
            elif file.filename.lower().endswith('.laz'):
                with open(WORKING_DIRECTORY + file.filename, 'wb') as f:
                    f.write(contents)
        
        except Exception:
            return {"message": "There was an error uploading the file"}
        finally:
            file.file.close()

        #se indexa el archivo subido
       
        direntry = os.scandir(WORKING_DIRECTORY)
        try:
            for filename in direntry:
                if filename.name == name:
                    indexar(filename,admin_institucion)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    else:
        raise HTTPException(status_code=400, detail="Invalid file extension")
    

def indexar(filename,admin_institucion):
    conn = MongoClient(MONGO_STRING)["chile3d"]
    inside = []
    if "archivos" not in conn.list_collection_names():
        conn.create_collection("archivos")
    extension =  filename.name.split('.')[-1]
    if extension == "tif":
        return TifServices().get_inside_list(filename,[],inside,admin_institucion)
    elif extension == "laz":
        #se utiliza pdal para extraer metadata de los archivos laz
        #se extrae la proyección de los archivos laz, que es un WKT de OGC
        return LazServices().get_inside_list(filename,[],inside,admin_institucion)



@archivos_ruta.patch("/archivos/{id}",status_code=204)
def actualizar_archivo(id: str,archivo: Archivo_edit, depends = Depends(read_users_me)):
    conn = MongoClient(MONGO_STRING)["chile3d"]
    notNullItems = {k: v for k, v in archivo.dict().items() if v is not None and v != ""}
    fecha_modificacion = datetime.datetime.now()
    notNullItems["fecha_modificacion"] = fecha_modificacion
    response = conn["archivos"].update_one({"id": ObjectId(id)}, {"$set": notNullItems})
    if response.modified_count == 0:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return {"message": "Archivo actualizado"}

@archivos_ruta.delete("/archivos/{id}",status_code=204)
def eliminar_archivo(id: str, depends = Depends(read_users_me)):
    conn = MongoClient(MONGO_STRING)["chile3d"]
    archivo = conn["archivos"].find_one({"id": ObjectId(id)})
    url = archivo["url"]
    #remove from working directory
    direntry = os.scandir(WORKING_DIRECTORY)
    try:
        for filename in direntry:
            if filename.name == url.split('/')[-1]:
                os.remove(filename.path)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error al eliminar archivo")
    
    response = conn["archivos"].delete_one({"id": ObjectId(id)})
    if response.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return {"message": "Archivo eliminado"}