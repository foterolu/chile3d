import subprocess as sp
import os
import json
import fiona
import pyproj
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

MUST_IN_EXTENSIONS = ['.shp' , '.shx', '.dbf']

class ShapefileServices:
    def get_inside_list(self, folder,features,inside):
        for filename in os.listdir(folder):
            if filename.endswith('.shp'):
               
                data = fiona.open(folder.path + "/" + filename)
                bbox, crs = data.bounds, data.crs
               
                espg = crs["init"].split(":")[1]
                minx = bbox[0]
                miny = bbox[1]
                maxx = bbox[2]
                maxy = bbox[3]


                p1 = Point(maxx, maxy)
                p2 = Point(maxx, miny)
                p3 = Point(minx, miny)
                p4 = Point(minx, maxy)

                polygon = Polygon(features['geometry']['coordinates'][0])
                crs_transform = pyproj.Transformer.from_crs( "EPSG:" + espg,"EPSG:4326")
                for point in [p1, p2, p3, p4]:
                    
                    point = Point(crs_transform.transform(point.x, point.y))
                    print(point, folder.path)
                    if polygon.contains(point):
                        print("inside")
                        inside.append(folder.path + "/")
                        break
        return inside
    def check_shp_files(self,folder):
        files = os.listdir(folder)
        shp_files = MUST_IN_EXTENSIONS[:]
        for file in files:
            if file.endswith('.shp'):
                shp_files.remove('.shp')
            elif file.endswith('.shx'):
                shp_files.remove('.shx')
            elif file.endswith('.dbf'):
                shp_files.remove('.dbf')
        if len(shp_files) == 0:
            return True
        else:
            return False