import geojson
import subprocess as sp
import json
import pyproj
import os
import zipfile
import io
import pdb
import rasterio
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
from contextlib import contextmanager
from services.laz_services import LazServices
from services.shp_services import ShapefileServices
from services.tif_services import TifServices
from routes.archivos import archivos_ruta
from routes.institucion import institucion_ruta
from routes.admin import admin_ruta
from routes.login import login_ruta

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
DIRECTORY = 'storage/'
app.include_router(institucion_ruta,tags=["institucion"])
app.include_router(archivos_ruta,tags=["archivo"])
app.include_router(admin_ruta,tags=["admin"])
app.include_router(login_ruta,tags=["login"])


  



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



@archivos_ruta.post("/archivos/descargar")
async def file_response(request: Request):
    body = await request.body()
    try:
        data = json.loads(body)['files']
        
        url_list = list(data)
        return zipfiles(url_list)

    except Exception as e:
        raise HTTPException(status_code=400, detail="Error al descargar archivos")
    #return FileResponse()

@app.post("/process")
async def file_process(request: Request):
    body = await request.body()
    try:
        data = json.loads(body)['files']
        scale = json.loads(body)['scale']
        #url_list = list(data)
        file_name = resample_file(data, scale)
        return {"resample_file" : str(file_name)}
    except Exception as e:
        print(e)
        return {"exception": "failed", "status" : e}
    #return FileResponse()


@contextmanager
def resample_raster(raster, scale=2):
    t = raster.transform
    transform = Affine(t.a / scale, t.b, t.c, t.d, t.e / scale, t.f)
    height = int(raster.height * scale)
    width  = int(raster.width  * scale)
    profile = raster.profile
    profile.update(transform=transform, driver='GTiff', height=height, width=width)
    data = raster.read(
            out_shape=(raster.count, height, width),
            resampling=Resampling.bilinear)

    with MemoryFile() as memfile:
        with memfile.open(**profile) as dataset:
            dataset.write(data)
            del data
        with memfile.open() as dataset: 
            yield dataset


def resample_file(filename, scale=2):
    print(f'Processing {filename}')
    print(f'Scale: {scale}\n')
    print(f'Original File Size: {os.path.getsize(filename)/(1024*1024)} MB')
    with rasterio.open(filename, compress='lzw', tiled=True) as src:
        with resample_raster(src, scale=scale) as resampled:
            dst_filename = os.path.splitext(filename)[0] + '_downsampled.tif'
            with rasterio.open(dst_filename, "w", **src.meta, compress='lzw', tiled=True ) as dest:
                for band in range(1, resampled.count + 1):
                    dest.write_band(band, resampled.read(band))
    print(f'New File Size: {os.path.getsize(dst_filename)/(1024*1024)} MB')
    return dst_filename
