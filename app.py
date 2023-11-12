
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routes.archivos import archivos_ruta
from routes.institucion import institucion_ruta
from routes.admin import admin_ruta
from routes.login import login_ruta
from config.database import mongodb_client
from globals import *
from dotenv import dotenv_values
import json
import os
import source.file_processing as fp

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
        return {"exception": "failed", "status" : e}

