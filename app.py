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

from services.laz_services import LazServices
from services.shp_services import ShapefileServices

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
@app.get('/')
def read_root():
   
    return {"Hello": "World"}

@app.get('/servicios')
async def servicios(request: Request):
    client_host = await request.client.host
    print(client_host)
    return {"servicios": "disponibles"}


@app.post('/geojson')
async def read_geojson(request: Request):
    body = await request.body()
    gj = geojson.loads(body)
    result = {}
    inside = []
    if gj.is_valid:
        for features in gj['features']:
            flag = 0
            for dir in os.scandir(DIRECTORY):
                #shapefile son varios archvios contenidos en una misma carpeta
                if dir.name == "shapefiles":
                    for folder in os.scandir(dir.path):
                        if folder.is_dir():
                            inside = ShapefileServices().get_inside_list(folder,features,inside)
                if dir.is_dir():
                    for filename in os.scandir(dir.path):
                        if filename.is_file():
                            extension =  filename.name.split('.')[-1]
                            #GeoTiff
                            if extension == "tif":
                                data = rasterio.open(filename.path)
                                z = data.read()[0]
                                maxx = data.bounds.right
                                maxy = data.bounds.top
                                minx = data.bounds.left
                                miny = data.bounds.bottom
                            
                                p1 = Point(maxx, maxy)
                                p2 = Point(maxx, miny)
                                p3 = Point(minx, miny)
                                p4 = Point(minx, maxy)
                                crs_transform = pyproj.Transformer.from_crs(data.crs,"EPSG:4326")
                                polygon = Polygon(features['geometry']['coordinates'][0])

                                for point in [p1,p2,p3,p4]:
                                    point = Point(crs_transform.transform(point.x,point.y))
                                    point = Point(point.y,point.x)
                                    if polygon.contains(point):
                                        inside.append(filename.path)
                                        break

                            elif extension == "laz":
                                #se utiliza pdal para extraer metadata de los archivos laz
                                #se extrae la proyección de los archivos laz, que es un WKT de la OGC
                                inside = LazServices().get_inside_list(filename,features,inside)
                       
        return {"status": "ok", "inside": inside}
    else:
        return {"status": "error, bad geojson file"}


  
@app.post("/files")
async def file_response(request: Request):
    body = await request.body()

    try:
        data = json.loads(body)['files']
        
        url_list = list(data)
        return zipfiles(url_list)

    except Exception as e:
        print(e)
        return {"status" : e}
    #return FileResponse()


def zipfiles(filenames):
    zip_filename = "archive.zip"
    print(filenames)

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

