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
from schemas.schemas import Archivo
from services.laz_services import LazServices
from services.shp_services import ShapefileServices
from services.tif_services import TifServices
from fastapi import File, UploadFile, HTTPException
from fastapi import APIRouter
from globals import *
from routes.login import read_users_me
from pathlib import Path


archivos_ruta = APIRouter()
EXTENSIONS = ('.shp' ,'.tif','.tiff','.laz','.las')


@archivos_ruta.get('/archivos')
async def get_all_archivos():
    return "todos los archivos"

@archivos_ruta.get('/archivos/{id}')
async def get_archivo():
    return "archivo con id: "

@archivos_ruta.post('/archivos/indexar',status_code=201)
async def read_geojson(request: Request):
    conn = MongoClient(MONGO_STRING)["chile3d"]
    inside = []
    if "archivos" not in conn.list_collection_names():
        conn.create_collection("archivos")
   
    
    for dir in os.scandir(DIRECTORY):
        #shapefile son varios archvios contenidos en una misma carpeta
        if dir.name == "shapefiles":
            for folder in os.scandir(dir.path):
                if folder.is_dir():
                    ShapefileServices().get_inside_list(folder,[],inside)
        if dir.is_dir():
            for filename in os.scandir(dir.path):
                if filename.is_file():
                    extension =  filename.name.split('.')[-1]
                    print(filename)
                    #GeoTiff
                    if extension == "tif":
                        TifServices().get_inside_list(filename,[],inside)
                    elif extension == "laz":
                        #se utiliza pdal para extraer metadata de los archivos laz
                        #se extrae la proyección de los archivos laz, que es un WKT de OGC
                        LazServices().get_inside_list(filename,[],inside)
                
    return {"status": "ok"}

def indexar(filename):
    conn = MongoClient(MONGO_STRING)["chile3d"]
    inside = []
    if "archivos" not in conn.list_collection_names():
        conn.create_collection("archivos")
    extension =  filename.name.split('.')[-1]
    if extension == "tif":
        TifServices().get_inside_list(filename,[],inside)
    elif extension == "laz":
        #se utiliza pdal para extraer metadata de los archivos laz
        #se extrae la proyección de los archivos laz, que es un WKT de OGC
        LazServices().get_inside_list(filename,[],inside)
    
    return {"status": "ok"}

@archivos_ruta.post("/archivos/buscar/poligono",status_code=200,response_model=List[Archivo])
async def buscar_archivos(request: geojson_pydantic.FeatureCollection[geojson_pydantic.Polygon,Dict]):
    conn = MongoClient(MONGO_STRING)["chile3d"]
    #IMPORTANT: agregar query within
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
def subir_archivo(file : UploadFile  = File(...)):
    os.makedirs(WORKING_DIRECTORY, exist_ok=True)
   
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
                indexar(filename)
                
        except Exception as e:
            os.remove(filename.path)
            raise HTTPException(status_code=400, detail=str(e))

    else:
        raise HTTPException(status_code=400, detail="Invalid file extension")
    
  

