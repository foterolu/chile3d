import datetime
import json
import os
import zipfile
import io
import geojson_pydantic
from typing import List,Dict
from fastapi import Request, Response,Depends
from schemas.schemas import Archivo,ArchivosEditar,AdminInstitucion
from services.laz_services import LazServices
from services.tif_services import TifServices
from fastapi import File, UploadFile, HTTPException
from fastapi import APIRouter
from globals import *
from routes.login import read_users_me
from bson.objectid import ObjectId
from bson.regex import Regex
from config.database import database

archivos_ruta = APIRouter()
EXTENSIONS = ('.shp' ,'.tif','.tiff','.laz','.las')



@archivos_ruta.get("/files")
async def get_archivos(
    fetch: int = 0,
    skip: int = 0,
    nombre: str = None,
    descripcion: str = None,
    extension: str = None,
    espg: str = None,
    fecha_incio: str = None,
    fecha_fin: str = None,
    url: str = None,
    keyword: str = None,
    topic_category: str = None,
    institucion: str = None,
    cantidad_descargas: int = None
):
    conn = database
    query = {}
    
    if nombre:
        query["nombre"] = {"$regex": Regex(nombre, "i")}
    if descripcion:
        query["descripcion"] = descripcion
    if extension:
        query["extension"] = extension
    if espg:
        query["espg"] = espg
    if fecha_incio and fecha_fin:
        try:
            fecha_incio = datetime.datetime.strptime(fecha_incio, "%Y-%m-%d")
            fecha_fin   = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
        except Exception as e:
            raise HTTPException(status_code=400, detail="Formato de fecha incorrecto")
        query["fecha_creacion"] = {"$gte": fecha_incio, "$lte": fecha_fin}
    if url:
        query["url"] = url
    if keyword:
        query["keyword"] = keyword
    if topic_category:
        query["topic_category"] = topic_category
    if institucion:
        query["institucion"] = institucion
    if cantidad_descargas:
        query["cantidad_descargas"] = cantidad_descargas

    projection = {"_id": 0}
    archivos = conn["archivos"].find(query,projection).skip(skip).limit(fetch)

    return list(archivos)



@archivos_ruta.get('/files/{id}')
async def get_archivo():
    conn = database
    try:
        return conn["archivos"].find_one({"id": ObjectId(id)})
    except Exception as e:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

@archivos_ruta.post("/files/download")
async def file_response(request: Request):
    body = await request.body()
    try:
        data = json.loads(body)['files']
        
        url_list = list(data)
        return zipfiles(url_list)

    except Exception as e:
        raise HTTPException(status_code=400, detail="Error al descargar archivos")
    #return FileResponse()

    

@archivos_ruta.post("/files/polygon",status_code=200,response_model=List[Archivo])
async def buscar_archivos(request: geojson_pydantic.FeatureCollection[geojson_pydantic.Polygon,Dict]):
    conn = database
    body = request
    MyPolygon = geojson_pydantic.FeatureCollection(features=body.features)
    gj = MyPolygon.dict()
    inside = []
    for features in gj['features']:
        polygon_coordinates  =features['geometry']['coordinates']
        
        query = {
            "coordenadas": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": polygon_coordinates,
                       
                    }
                }
            }
        }
        retrieved_documents = list(conn["archivos"].find(query))
        if len(retrieved_documents) > 0:    
            inside.extend(retrieved_documents)
    return inside

      

@archivos_ruta.post("/files",status_code=201)
def subir_archivo(file : List[UploadFile]  = File(...), admin = Depends(read_users_me)):
    os.makedirs(WORKING_DIRECTORY, exist_ok=True)
    admin["admin_id"] = admin["id"]
    admin_institucion = AdminInstitucion(**admin)
    names =[]
    for file in file:
        names.append(file.filename) 
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
        else:
            raise HTTPException(status_code=400, detail="Invalid file extension")
    
    direntry = os.scandir(WORKING_DIRECTORY)
    try:
        for filename in direntry:
            if filename.name in names:
                indexar(filename,admin_institucion)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

def indexar(filename,admin_institucion: AdminInstitucion):
    conn = database
    inside = []
    if "archivos" not in conn.list_collection_names():
        conn.create_collection("archivos")
    extension =  filename.name.split('.')[-1]
    if extension == "tif":
        return TifServices().get_inside_list(filename,admin_institucion)
    elif extension == "laz":
        return LazServices().get_inside_list(filename,admin_institucion)



@archivos_ruta.patch("/files/{id}",status_code=204)
def actualizar_archivo(id: str,archivo: ArchivosEditar, depends = Depends(read_users_me)):
    conn = database
    notNullItems = {k: v for k, v in archivo.dict().items() if v is not None and v != ""}
    fecha_modificacion = datetime.datetime.now()
    notNullItems["fecha_modificacion"] = fecha_modificacion
    response = conn["archivos"].update_one({"id": ObjectId(id)}, {"$set": notNullItems})
    if response.modified_count == 0:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return {"message": "File updated successfully"}

@archivos_ruta.delete("/files/{id}",status_code=204)
def eliminar_archivo(id: str, depends = Depends(read_users_me)):
    conn = database
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


def zipfiles(filenames):
    zip_filename = "archive.zip"
    s = io.BytesIO()
    zf = zipfile.ZipFile(s, "w")
    for fpath in filenames:
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)
        if fname != '':
        # Add file, at correct path 
            zf.write(fpath, fname)
        else:
            for dirname, subdirs, files in os.walk(fpath):
                for filename in files:
                    
                    # Add file, at correct path
                    zf.write(os.path.join(dirname, filename))
    # Must close zip for all contents to be written
    zf.close()
    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = Response(s.getvalue(), media_type="application/x-zip-compressed", headers={
        'Content-Disposition': f'attachment;filename={zip_filename}'
    })
    return resp