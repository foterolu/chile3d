from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
import geojson
import subprocess as sp
import json
import os
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import pyproj
import os
import zipfile
import io


app = FastAPI()

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

@app.get('/geojson')
async def read_geojson(request: Request):
    
    body = await request.body()
    gj = geojson.loads(body)
    result = {}
    inside = []
    if gj.is_valid:
        for features in gj['features']:
            for filename in os.scandir(DIRECTORY):
                if filename.is_file():
                    #se utiliza pdal para extraer metadata de los archivos laz
                    metadata = sp.run(['pdal', 'info','--metadata', filename], stderr=sp.PIPE, stdout=sp.PIPE)
                    metadata = metadata.stdout.decode()
                    
                    metadata = str(metadata).replace("'", '"')
                    metadata = json.loads(metadata)

                    #se extrae la proyección de los archivos laz
                    spatial_reference = metadata['metadata']['comp_spatialreference']
                    spatial_reference = spatial_reference.split('COMPD_CS')[1].split(',')[0].split('"')[1]

                    #se extrae el poligono de los archivos laz
                    maxx = metadata['metadata']['maxx']
                    maxy = metadata['metadata']['maxy']
                    minx = metadata['metadata']['minx']
                    miny = metadata['metadata']['miny']
                    
                    p1 = Point(maxx, maxy)
                    p2 = Point(maxx, miny)
                    p3 = Point(minx, miny)
                    p4 = Point(minx, maxy)
                    
                    #se genera el poligono entrante en la request
                    polygon = Polygon(features['geometry']['coordinates'][0])

                    #se transforma el poligono de los archivos laz de ETRS89 / UTM zone 30N  a WSG84
                    wgs_etrs89 = pyproj.Transformer.from_crs( "EPSG:25830","EPSG:4326")
                    
                    #si un punto esta contenido en el poligono de la request se añade a la lista de archivos dentro del poligono
                    for point in [p1, p2, p3, p4]:
                        point = Point(wgs_etrs89.transform(point.x, point.y))
                        point = Point(point.y, point.x)
                        
                        if polygon.contains(point):
                           
                            inside.append(filename.name)
                            break
                       
        return {"status": "ok", "inside": inside}
    else:
        return {"status": "error, bad geojson file"}
  
@app.get("/files")
async def file_response(request: Request):
    body = await request.body()
    data = json.loads(body)['data']
    url_list = list(data)
    return zipfiles(url_list)
    #return FileResponse()


def zipfiles(filenames):
    zip_filename = "archive.zip"


    s = io.BytesIO()
    zf = zipfile.ZipFile(s, "w")

    for fpath in filenames:
        # Calculate path for file in zip
        fpath =  DIRECTORY+fpath
        fdir, fname = os.path.split(fpath)

        # Add file, at correct path 
        zf.write(fpath, fname)

    # Must close zip for all contents to be written
    zf.close()

    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = Response(s.getvalue(), media_type="application/x-zip-compressed", headers={
        'Content-Disposition': f'attachment;filename={zip_filename}'
    })

    return resp

