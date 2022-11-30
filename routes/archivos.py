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
from typing import List,Dict
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from PIL.TiffTags import TAGS
from pymongo import MongoClient
import geojson_pydantic

from schemas.schemas import Archivo
from services.laz_services import LazServices
from services.shp_services import ShapefileServices
from services.tif_services import TifServices

from fastapi import APIRouter


archivos_ruta = APIRouter()
DIRECTORY = 'storage/'

@archivos_ruta.get('/archivos')
async def get_all_archivos():
    return "todos los archivos"

@archivos_ruta.get('/archivos/{id}')
async def get_archivo():
    return "archivo con id: "

@archivos_ruta.post('/archivos/indexar',status_code=201)
async def read_geojson(request: Request):
    conn = MongoClient('localhost', 27017)["chile3d"]
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
                    #GeoTiff
                    if extension == "tif":
                        TifServices().get_inside_list(filename,[],inside)
                    elif extension == "laz":
                        #se utiliza pdal para extraer metadata de los archivos laz
                        #se extrae la proyección de los archivos laz, que es un WKT de OGC
                        LazServices().get_inside_list(filename,[],inside)
                
    return {"status": "ok"}

@archivos_ruta.get("/archivos/buscar/poligono",status_code=200,response_model=List[Archivo])
async def buscar_archivos(request: geojson_pydantic.FeatureCollection[geojson_pydantic.Polygon,Dict]):
    conn = MongoClient('localhost', 27017)["chile3d"]
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
            crs_transform = pyproj.Transformer.from_crs("EPSG:" + archivo["espg"], "EPSG:4326")

            for point in [p1, p2, p3, p4]:
                point = Point(crs_transform.transform(point.x,point.y))
                if archivo["extension"] == "shapefile":
                    point = point
                if archivo["extension"] == "laz" or archivo["extension"] == "tif":
                    point = Point(point.y, point.x)
                if polygon.contains(point):
                    inside.append(modelo)
                    break

    return inside             
  

