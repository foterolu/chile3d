from fastapi import FastAPI, Request
import geojson
import laspy
import subprocess as sp
import json
import os
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import pyproj

app = FastAPI()

# poligino de datos de muestra extraidos del portal de descargas CNIG WSG84,
# almacenado temporalmente en storage/
DATA_POLYGON = [[-3.723834 , 40.436867],
                [-3.723805 , 40.405078],
                [-3.670911, 40.404709],
                [-3.672853, 40.436128]]
@app.get('/')
def read_root():
    
    return {"Hello": "World"}

@app.post('/geojson')
async def read_geojson(request: Request):
    directory = 'storage'
    target = 'storage/PNOA_2010_Lote7_CYL-MAD_438-4474_ORT-CLA-COL.laz'
    body = await request.body()
    gj = geojson.loads(body)
    result = {}
    inside = []
    if gj.is_valid:
        for features in gj['features']:
            for filename in os.scandir(directory):
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
                    
                    #se genera el poligno entrante en la request
                    polygon = Polygon(features['geometry']['coordinates'][0])

                    #se transforma el poligono de los archivos laz de ETRS89 / UTM zone 30N  a WSG84
                    wgs_etrs89 = pyproj.Transformer.from_crs( "EPSG:25830","EPSG:4326")
                    
                    #si un punto esta contenido en el poligono de la request se añade a la lista de archivos dentro del poligono
                    for point in [p1, p2, p3, p4]:
                        point = Point(wgs_etrs89.transform(point.x, point.y))
                        point = Point(point.y, point.x)
                        
                        if polygon.contains(point):
                            print('point is inside polygon')
                            print(point)
                           
                            print('----------------------')
                            inside.append(filename.name)
                            break
                        else:
                            print('point is outside polygon')
                            print(point)
                            print('----------------------')
            
        return {"status": "ok", "inside": inside}
    else:
        return {"status": "error, bad geojson file"}
  


