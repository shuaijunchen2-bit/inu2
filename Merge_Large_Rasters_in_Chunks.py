import rasterio
from rasterio.windows import Window
import numpy as np

# Define paths for the input rasters and output merged raster
raster1_path = 'D:/Nationwide_Tsunami_Inundation/DEM_Data/Latest_North_Island_Merged_LiDAR_and_FABDEM.tif'  # "old" raster (base layer)
raster2_path = 'D:/Nationwide_Tsunami_Inundation/DEM_Data/Port_Waikato_10mResolution.tif'  # "new" raster (top layer)
output_raster_path = 'D:/Nationwide_Tsunami_Inundation/DEM_Data/Latest_North_Island_Merged_LiDAR_and_FABDEM_2.tif'  # Output path

# Define no-data value
no_data_value = -9999

# Open both rasters
with rasterio.open(raster1_path) as src1, rasterio.open(raster2_path) as src2:
    # Ensure both rasters have the same dimensions and transform
    assert src1.width == src2.width and src1.height == src2.height, "Rasters must have the same dimensions."
    assert src1.transform == src2.transform, "Rasters must have the same spatial transform."

    # Copy metadata from the first raster and prepare output file metadata
    out_meta = src1.meta.copy()
    out_meta.update({"nodata": no_data_value})  # Set no-data value in metadata
    
    # Open the output file for writing
    with rasterio.open(output_raster_path, 'w', **out_meta) as dest:
        # Process in blocks to avoid memory issues
        block_size = 10000  # Adjust block size as needed

        for row in range(0, src1.height, block_size):
            for col in range(0, src1.width, block_size):
                # Define window for the block
                window = Window(col, row, min(block_size, src1.width - col), min(block_size, src1.height - row))
                
                # Read data blocks from each raster
                data1 = src1.read(1, window=window)  # old raster data
                data2 = src2.read(1, window=window)  # new raster data
                
                # Mask out no-data values
                data1 = np.where(data1 == no_data_value, np.nan, data1)
                data2 = np.where(data2 == no_data_value, np.nan, data2)
                
                # Merge: prioritize new raster values; use old raster values where new is NaN
                merged_data = np.where(np.isnan(data2), data1, data2)
                
                # Write merged data to the output raster in the current window
                dest.write(merged_data, 1, window=window)
