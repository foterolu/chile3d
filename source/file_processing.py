import rasterio
import time
import json
import pdal
import sys
import os 

from rasterio.warp import reproject, Resampling
from rasterio import Affine, MemoryFile
from rasterio.warp import Resampling
from numpy import zeros

def resolution_reduction_TIFF(filename, scale=0.5, compression_method='deflate'):
    # Reduce resolution of TIFF file
    # Compression methods available: lossless: lzw, deflate, packbits, zstd. And lossy: jpeg

    if (scale > 0.7):
        print('Scale too high, must be less than 0.7 due to memory limitations')
        print('Original file will be returned')
        return filename

    with rasterio.open(filename) as src:

        data = src.read()

        new_height = int(src.height * scale)
        new_width = int(src.width * scale)
        new_transform = src.transform * src.transform.scale((src.width / new_width), (src.height / new_height))

        resampled_data = zeros((src.count, new_height, new_width), dtype=data.dtype)

        start = time.time()
        reproject(data, resampled_data, src_transform=src.transform, src_crs=src.crs,
                dst_transform=new_transform, dst_crs=src.crs,
                resampling=Resampling.bilinear)

    dst_filename = filename+'_'+compression_method+"_"+str(scale)+'.tif'

    with rasterio.open(dst_filename, 'w', driver='GTiff',
                    width=new_width, height=new_height,
                    count=src.count, crs=src.crs, transform=new_transform,
                    dtype=data.dtype, compress=compression_method) as dst:
        dst.write(resampled_data)

    end = time.time()
    print(f'Processing {filename}, scale: {scale}, compression: {compression_method}, time: {end-start}, file size: {os.path.getsize(dst_filename)/(1024*1024)} MB')
    return dst_filename


def resolution_reduction_point_cloud(filename, cell=1, method='sample'):
    # Reduce resolution of point cloud file

    dst_filename = filename.split('.')[0]
    dst_filename = dst_filename+'_'+method+"_"+str(cell)+'.laz'

    pipeline_dict = { "pipeline" : [
        filename,
        {   "type": f"filters.{method}",
            "cell": cell},
        dst_filename]}
            
    pipeline = json.dumps(pipeline_dict)
    pipeline = pdal.Pipeline(pipeline)
    count = pipeline.execute()
    return dst_filename


def resample_file(filename, scale=0.5):
    print(f'Processing {filename}')
    print(f'Scale: {scale}\n')
    print(f'Original File Size: {os.path.getsize(filename)/(1024*1024)} MB')

    file_format = filename.split('.')[-1]

    if file_format == 'tif':
        dst_filename = resolution_reduction_TIFF(filename=filename, scale=scale)

    elif file_format == 'laz' or file_format == 'las':
        # TODO change cell parameter to scale
        dst_filename = resolution_reduction_point_cloud(filename=filename, cell=scale)



    return dst_filename

def point_cloud_to_tiff(filename, resolution, radius):
# Convert point cloud to raster, using max value of points in each cell
    
    dst_filename = filename.replace("/laz/", "/tiff/")
    dst_filename = dst_filename+'_ex_laz.tif'

    pipeline_dict = {
    "pipeline":[
        filename,
        {
            "type":"writers.gdal",
            "filename":dst_filename,
            "resolution":resolution, # resolution x resolution raster cells size
            "radius":radius, # neighborhood's radius to search for points. Default: sqrt(2) * resolution
            "output_type":"max"
        }]}

    pipeline = json.dumps(pipeline_dict)

    pipeline = pdal.Pipeline(pipeline)
    count = pipeline.execute()

    

    return dst_filename

def reformat_file(filename, radius=1, resolution=1):

    print(f'Reformatting {filename}')
    print(f'Radius: {radius}\n')
    file_format = filename.split('.')[-1]

    if file_format == 'laz' or file_format == 'las':
        point_cloud_to_tiff(filename, resolution, radius)







if __name__ == '__main__':
    filename = sys.argv[1]
    scale = float(sys.argv[2])
    reformat_file(filename, 1, 0.5)

