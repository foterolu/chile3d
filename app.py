import geojson
import subprocess as sp
import json
import pyproj
import os
import zipfile
import io
import pdb
import rasterio
import source.file_processing as fp

from fastapi import FastAPI, Request, Response, HTTPException
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
from services.laz_services import LazServices
from services.shp_services import ShapefileServices
from services.tif_services import TifServices
from routes.archivos import archivos_ruta
from routes.institucion import institucion_ruta
from routes.admin import admin_ruta
from routes.login import login_ruta
from globals import *

from osgeo import gdal,osr

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# poligino de datos de muestra extraidos del portal de descargas CNIG WSG84,
# almacenado temporalmente en storage/
DATA_POLYGON = [
                        [-3.723834 , 40.436867],
                        [-3.723805 , 40.405078],
                        [-3.670911, 40.404709],
                        [-3.672853, 40.436128],
                        [-3.723834 , 40.436867]
                ]
app.include_router(institucion_ruta,tags=["Institutions"])
app.include_router(archivos_ruta,tags=["Files"])
app.include_router(admin_ruta,tags=["Admins"])
app.include_router(login_ruta,tags=["Login"])

#check if DIRECTORY exists if not create it
if not os.path.exists(DIRECTORY):
    os.makedirs(DIRECTORY)
if not os.path.exists(WORKING_DIRECTORY):
    os.makedirs(WORKING_DIRECTORY)
if not os.path.exists(DIRECTORY + 'tif/'):
    os.makedirs(DIRECTORY + 'tif/')
if not os.path.exists(DIRECTORY + 'laz/'):
    os.makedirs(DIRECTORY + 'laz/')
if not os.path.exists(DIRECTORY + 'las/'):
    os.makedirs(DIRECTORY + 'las/')
    



def zipfiles(filenames):
    zip_filename = "archive.zip"
    s = io.BytesIO()
    zf = zipfile.ZipFile(s, "w")
    for fpath in filenames:
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)
        print(fdir)
        if fname != '':
        # Add file, at correct path 
            zf.write(fpath, fname)
        else:
            for dirname, subdirs, files in os.walk(fpath):
                print(subdirs)
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



@archivos_ruta.post("/files/descargar")
async def file_response(request: Request):
    body = await request.body()
    try:
        data = json.loads(body)['files']
        
        url_list = list(data)
        return zipfiles(url_list)

    except Exception as e:
        raise HTTPException(status_code=400, detail="Error al descargar archivos")
    #return FileResponse()

# Reduce resolution of a single raster TIFF file
@app.post("/process")
async def file_process(request: Request):
    body = await request.body()
    try:
        data = json.loads(body)['files']
        scale = json.loads(body)['scale']
        #url_list = list(data)
        file_name = fp.resample_file(data, scale)
        return {"resample_file" : str(file_name)}
    except Exception as e:
        print(e)
        return {"exception": "failed", "status" : e}

