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



class TifServices:
    def get_inside_list(self, filename,features, inside):
        conn = MongoClient('localhost', 27017)["chile3d"]
        admin_id = 1
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
        espg_code = str(archivo.crs).split(":")[1]
        if conn["archivos"].find_one({"url":filename.path}) == None:
            data = {
                "admin_id": admin_id,
                "nombre": nombre,
                "descripcion": descripcion,
                "extension": extension,
                "espg": espg_code,
                "fecha_creacion": fecha_creacion,
                "fecha_modificacion": fecha_modificacion,
                "minx": minx,
                "miny": miny,
                "maxx": maxx,
                "maxy": maxy,
                "url": filename.path,
                "keyword": keyword,
                "topic_category": topic_category,
                "institucion": institucion,
                "cantidad_descargas": cantidad_descargas

            }
            insert_archivo = Archivo(**data)
            conn["archivos"].insert_one(insert_archivo.dict())
        
        """
        p1 = Point(maxx, maxy)
        p2 = Point(maxx, miny)
        p3 = Point(minx, miny)
        p4 = Point(minx, maxy)
        crs_transform = pyproj.Transformer.from_crs(archivo.crs,"EPSG:4326",always_xy=True)
        polygon = Polygon(features['geometry']['coordinates'][0])

        for point in [p1,p2,p3,p4]:
            point = Point(crs_transform.transform(point.x,point.y))
            
            if polygon.contains(point):
                inside.append(filename.path)
                break
        """
       