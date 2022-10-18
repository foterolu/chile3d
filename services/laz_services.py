

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



class LazServices:
    def get_metadata(self, filename):
        
        metadata = sp.run(['pdal', 'info','--metadata', filename], stderr=sp.PIPE, stdout=sp.PIPE)
        metadata = metadata.stdout.decode()
        metadata = str(metadata).replace("'", '"')
        metadata = json.loads(metadata)
        return metadata

    def get_inside_list(self,filename,features,inside):
        try:
            metadata = self.get_metadata(filename)
            
            spatial = metadata['metadata']['comp_spatialreference']
            if spatial != '':
                srs = osr.SpatialReference(wkt=spatial)
            
                espg_code = srs.GetAttrValue('AUTHORITY',1)

                #se extrae bbox de los archivos laz
                maxx = metadata['metadata']['maxx']
                maxy = metadata['metadata']['maxy']
                minx = metadata['metadata']['minx']
                miny = metadata['metadata']['miny']
                
                #bbox del archivo laz
                p1 = Point(maxx, maxy)
                p2 = Point(maxx, miny)
                p3 = Point(minx, miny)
                p4 = Point(minx, maxy)

                #se genera el poligono entrante en la request
                polygon = Polygon(features['geometry']['coordinates'][0])

                #se transforma el poligono de los archivos laz de ETRS89 / UTM zone 30N  a WSG84
                wgs_etrs89 = pyproj.Transformer.from_crs( "EPSG:" + espg_code,"EPSG:4326")

                #si un punto esta contenido en el poligono de la request se añade a la lista de archivos dentro del poligono
                for point in [p1, p2, p3, p4]:
                    point = Point(wgs_etrs89.transform(point.x, point.y))
                    point = Point(point.y, point.x)
                    
                    if polygon.contains(point):
                    
                        inside.append(filename.name)
                        break
            else:
                print(f'No se pudo obtener la proyección del archivo {filename.name}')
        except Exception as e:
            print(e)
        return inside