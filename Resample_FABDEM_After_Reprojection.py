import os
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import calculate_default_transform, reproject, Resampling

# Define input and output directories
input_dir = 'D:/Nationwide_Tsunami_Inundation/FABDEM/Full_NZ_FABDEM_NZVD2016/'
output_dir = 'D:/Nationwide_Tsunami_Inundation/FABDEM/Full_NZ_FABDEM_NZVD2016_10m_Resolution/'
os.makedirs(output_dir, exist_ok=True)

# Define the target CRS and resolution
target_crs = 'EPSG:2193'
target_resolution = 10  # 10m resolution

for filename in os.listdir(input_dir):
    if filename.endswith('.tif'):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, f'Resolution_10m_{filename}')

        with rasterio.open(input_path) as src:
            # Transform to target CRS
            transform, width, height = calculate_default_transform(
                src.crs, target_crs, src.width, src.height, *src.bounds
            )
            transform = from_origin(
                round(transform.c / target_resolution) * target_resolution,
                round(transform.f / target_resolution) * target_resolution,
                target_resolution, target_resolution
            )

            # Prepare metadata for the output file
            out_meta = src.meta.copy()
            out_meta.update({
                'crs': target_crs,
                'transform': transform,
                'width': width,
                'height': height,
                'driver': 'GTiff'
            })

            # Resample and reproject
            with rasterio.open(output_path, 'w', **out_meta) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=target_crs,
                        resampling=Resampling.bilinear
                    )
