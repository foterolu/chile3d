from contextlib import contextmanager
import os 
import rasterio
from rasterio import Affine, MemoryFile
from rasterio.warp import Resampling
import rasterio
from rasterio.warp import reproject, Resampling
from numpy import zeros

import os
import sys
import time

def resolution_reduction_TIFF(raster, scale=0.5, compression_method='lzw'):
    # Reduce resolution of TIFF file
    # Compression methods available: lossless: lzw, deflate, packbits, zstd. And lossy: jpeg

    with rasterio.open(raster) as src:

        data = src.read()

        new_height = int(src.height * scale)
        new_width = int(src.width * scale)
        new_transform = src.transform * src.transform.scale((src.width / new_width), (src.height / new_height))

        resampled_data = zeros((src.count, new_height, new_width), dtype=data.dtype)

        start = time.time()
        reproject(data, resampled_data, src_transform=src.transform, src_crs=src.crs,
                dst_transform=new_transform, dst_crs=src.crs,
                resampling=Resampling.bilinear)


    dst_filename = 'temp_'+raster+'_'+compression_method+"_"+str(scale)+'.tif'

    with rasterio.open(dst_filename, 'w', driver='GTiff',
                    width=new_width, height=new_height,
                    count=src.count, crs=src.crs, transform=new_transform,
                    dtype=data.dtype, compress=compression_method) as dst:
        dst.write(resampled_data)

    end = time.time()
    print(f'Processing {raster}, scale: {scale}, compression: {compression_method}, time: {end-start}, file size: {os.path.getsize(dst_filename)/(1024*1024)} MB')

    return dst_filename


@contextmanager
def resample_raster(raster, scale=0.5):
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

    # with rasterio.open(filename, compress='lzw', tiled=True) as src:
    #     with resample_raster(src, scale=scale) as resampled:
    #         dst_filename = os.path.splitext(filename)[0] + '_downsampled.tif'
    #         with rasterio.open(dst_filename, "w", **src.meta, compress='lzw', tiled=True ) as dest:
    #             for band in range(1, resampled.count + 1):
    #                 dest.write_band(band, resampled.read(band))
    # print(f'New File Size: {os.path.getsize(dst_filename)/(1024*1024)} MB')

    dst_filename = resolution_reduction_TIFF(raster=filename, scale=scale)


    return dst_filename
