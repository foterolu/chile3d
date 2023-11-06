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
from config.database import database, mongodb_client
from globals import *
from dotenv import dotenv_values
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

config = dotenv_values(".env")


@app.on_event("shutdown")
def shutdown_db_client():
    mongodb_client.close()

            
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

