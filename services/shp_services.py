import subprocess as sp
import os
import json
import fiona
import pyproj
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from pymongo import MongoClient
from schemas.schemas import Archivo
from datetime import datetime
from globals import *
MUST_IN_EXTENSIONS = ['.shp' , '.shx', '.dbf']

class ShapefileServices:
    def get_inside_list(self, folder,features,inside):
        conn = MongoClient(MONGO_STRING)["chile3d"]
       
        for filename in os.listdir(folder):
            admin_id = 1
            nombre = filename
            descripcion = "descripcion"
            extension =  "shp"
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
            if filename.endswith('.shp'):
                data = fiona.open(folder.path + "/" + filename)
                bbox, crs = data.bounds, data.crs
                espg_code = crs["init"].split(":")[1]
                
                minx = bbox[0]
                miny = bbox[1]
                maxx = bbox[2]
                maxy = bbox[3]
                p1 = Point(maxx, maxy)
                p2 = Point(minx, miny)
                crs_transform = pyproj.Transformer.from_crs(espg_code,"EPSG:4326",always_xy=True)
                p1 = crs_transform.transform(p1.x, p1.y)
                p2 = crs_transform.transform(p2.x, p2.y)
                maxx = p1[0]
                maxy = p1[1]
                minx = p2[0]
                miny = p2[1]
                
                if conn["archivos"].find_one({"url":folder.path}) == None:
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
                    "url": folder.path,
                    "keyword": keyword,
                    "topic_category": topic_category,
                    "institucion": institucion,
                    "cantidad_descargas": cantidad_descargas

                }
                    insert_archivo = Archivo(**data)
                    conn["archivos"].insert_one(insert_archivo.dict())

            
        return inside
    def check_shp_files(self,folder):
        files = os.listdir(folder)
        shp_files = MUST_IN_EXTENSIONS[:]
        for file in files:
            if file.endswith('.shp'):
                shp_files.remove('.shp')
            elif file.endswith('.shx'):
                shp_files.remove('.shx')
            elif file.endswith('.dbf'):
                shp_files.remove('.dbf')
        if len(shp_files) == 0:
            return True
        else:
            return False