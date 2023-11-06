

import geojson
import subprocess as sp
import json
import os
import pyproj
import os
import zipfile
import io
import pdb

from osgeo import gdal,osr
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from pymongo import MongoClient
from schemas.schemas import Archivo
from datetime import datetime
from globals import *
from config.database import database


class LazServices:
    def get_metadata(self, filename):
        
        metadata = sp.run(['pdal', 'info','--metadata', filename], stderr=sp.PIPE, stdout=sp.PIPE)
        metadata = metadata.stdout.decode()
                #se transforma el poligono de los archivos laz de ETRS89 / UTM zone 30N  a WSG84
        metadata = str(metadata).replace("'", '"')
        metadata = json.loads(metadata)
        return metadata

    def get_inside_list(self,filename,features,inside,admin_institucion):
        conn = database
        admin_id = 1
        nombre = filename.name
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
        try:
            metadata = self.get_metadata(filename)
            spatial = metadata['metadata']['comp_spatialreference']
            if spatial != '':
                srs = osr.SpatialReference(wkt=spatial)
                espg_code = srs.GetAttrValue('AUTHORITY',1)

                #se extrae bbox de los archivos laz y se transforma a WSG84 para indexar en mongo
                maxx = metadata['metadata']['maxx']
                maxy = metadata['metadata']['maxy']
                minx = metadata['metadata']['minx']
                miny = metadata['metadata']['miny']
                p1 = Point(maxx, maxy)
                p2 = Point(minx, miny)
                crs_transform = pyproj.Transformer.from_crs("EPSG:" +espg_code,"EPSG:4326",always_xy=True)
                p1 = crs_transform.transform(p1.x, p1.y)
                p2 = crs_transform.transform(p2.x, p2.y)
                maxx = p1[0]
                maxy = p1[1]
                minx = p2[0]
                miny = p2[1]
                coordinates =  [[[minx, miny], [minx, maxy], [maxx, maxy], [maxx, miny], [minx, miny]]]
                geometry = {
                    "type": "Polygon",
                    "coordinates": coordinates
                }
                admin_institucion = admin_institucion.dict()
                if conn["archivos"].find_one({"url": DIRECTORY + "laz/" + filename.name}) == None:
                    data = {
                    "admin":admin_institucion ,
                    "nombre": nombre,
                    "descripcion": descripcion,
                    "extension": extension,
                    "espg": "EPSG:" +espg_code,
                    "fecha_creacion": fecha_creacion,
                    "fecha_modificacion": fecha_modificacion,
                    "minx": minx,
                    "miny": miny,
                    "maxx": maxx,
                    "maxy": maxy,
                    "coordenadas": geometry,
                    "url": filename.path,
                    "keyword": keyword,
                    "topic_category": topic_category,
                    "institucion": admin_institucion["institucion"],
                    "cantidad_descargas": cantidad_descargas

                }
                    insert_archivo = Archivo(**data)
              
                    return conn["archivos"].insert_one(insert_archivo.dict())
                else:
                    raise Exception("El archivo ya existe en la base de datos")
        except Exception as e:
            raise Exception("Error al extraer metadata del archivo laz")
        return inside