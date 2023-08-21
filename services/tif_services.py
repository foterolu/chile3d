import geojson
import subprocess as sp
import json
import pyproj
import os
import zipfile
import io
import pdb
import rasterio
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from PIL.TiffTags import TAGS
from pymongo import MongoClient

from rasterio.enums import Resampling
from rasterio import Affine, MemoryFile
from rasterio.warp import reproject, Resampling
from contextlib import contextmanager
from services.laz_services import LazServices
from services.shp_services import ShapefileServices
from schemas.schemas import Archivo
from datetime import datetime

from osgeo import gdal,osr
from globals import *



class TifServices:
    def get_inside_list(self, filename,features, inside, admin_insitucion):
   
        conn = MongoClient(MONGO_STRING)["chile3d"]
    
        nombre = filename.name
        descripcion = "descripcion"
        extension =  "tif"
        espg_code = ""
        fecha_creacion = datetime.utcnow()
        fecha_modificacion = datetime.utcnow()
        minx = 0
        miny = 0
        maxx = 0
        maxy = 0
        url = "url"
        keyword = "keyword"
        topic_category = "topic_category"
        institucion = "institucion"
        cantidad_descargas = 0

        archivo = rasterio.open(filename.path)
       
        z = archivo.read()[0]
        maxx = archivo.bounds.right
        maxy = archivo.bounds.top
        minx = archivo.bounds.left
        miny = archivo.bounds.bottom
        p1 = Point(maxx, maxy)
        p2 = Point(minx, miny)
        crs = pyproj.CRS(archivo.crs)
        crs_transform = pyproj.Transformer.from_crs(crs,"EPSG:4326",always_xy=True)
        p1 = crs_transform.transform(p1.x, p1.y)
        p2 = crs_transform.transform(p2.x, p2.y)
        maxx = p1[0]
        maxy = p1[1]
        minx = p2[0]
        miny = p2[1]
        coordinates = [[minx, miny], [minx, maxy], [maxx, maxy], [maxx, miny], [minx, miny]]
        if conn["archivos"].find_one({"url":filename.path}) == None:
            data = {
                "admin": admin_insitucion.dict(),
                "nombre": nombre,
                "descripcion": descripcion,
                "extension": extension,
                "espg": crs.to_epsg(),
                "fecha_creacion": fecha_creacion,
                "fecha_modificacion": fecha_modificacion,
                "minx": minx,
                "miny": miny,
                "maxx": maxx,
                "maxy": maxy,
                "coordenadas": coordinates,
                "url": filename.path,
                "keyword": keyword,
                "topic_category": topic_category,
                "institucion": institucion,
                "cantidad_descargas": cantidad_descargas
            }
            insert_archivo = Archivo(**data)
            inserted_file = conn["archivos"].insert_one(insert_archivo.dict())
            return inserted_file
        else:
            raise Exception("El archivo ya existe en la base de datos")
    
            
       
       