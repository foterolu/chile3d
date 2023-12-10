import pyproj
import rasterio
from shapely.geometry import Point
from schemas.schemas import Archivo
from schemas.schemas import Archivo
from datetime import datetime
from globals import *
from config.database import database


class TifServices:
    def get_inside_list(self, filename, admin_institucion):
        conn = database
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
        institucion =  admin_institucion.dict()["institucion"]
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
        coordinates = [[[minx, miny], [minx, maxy], [maxx, maxy], [maxx, miny], [minx, miny]]]
        geometry = {
            "type": "Polygon",
            "coordinates": coordinates
        }
        
       
        if conn["archivos"].find_one({"url":filename.path}) == None:
            data = {
                "admin": admin_institucion.dict(),
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
                "coordenadas": geometry,
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
    
            
       
       