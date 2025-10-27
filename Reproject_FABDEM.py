import os
import rasterio
import pyproj
from pyproj import Transformer
from filelock import FileLock
import time

# Define CRS
wgs84_egm2008 = pyproj.CRS("epsg:4326+3855")  # Source CRS
wgs84_nzvd2016 = pyproj.CRS("epsg:4326+7839")  # Target CRS

# Create transformer
transformer = Transformer.from_crs(wgs84_egm2008, wgs84_nzvd2016, always_xy=True)

# Define the input and output directories
input_dir = 'D:/Nationwide_Tsunami_Inundation/FABDEM/Full_NZ_FABDEM_Tiles_2'
output_dir = 'D:/Nationwide_Tsunami_Inundation/FABDEM/Full_NZ_FABDEM_NZVD2016/'

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Tracking file for processed files
tracking_file_path = os.path.join(output_dir, 'processed_files2.txt')
tracking_lock_path = tracking_file_path + '.lock'

def is_file_processed(filename):
    """ Check if the file is already processed by checking the tracking file """
    with FileLock(tracking_lock_path):
        if os.path.exists(tracking_file_path):
            with open(tracking_file_path, 'r') as f:
                processed_files = f.read().splitlines()
            return filename in processed_files
        return False

def mark_file_as_processed(filename):
    """ Mark the file as processed by writing it to the tracking file """
    with FileLock(tracking_lock_path):
        with open(tracking_file_path, 'a') as f:
            f.write(f"{filename}\n")

# Loop over each file in the input directory
for filename in os.listdir(input_dir):
    if filename.endswith('.tif'):
        input_filepath = os.path.join(input_dir, filename)
        output_filepath = os.path.join(output_dir, filename.replace('V1-2', 'NZVD2016'))

        # Check if the file is already processed
        if os.path.exists(output_filepath) or is_file_processed(filename):
            print(f"Skipping {filename}, already processed.")
            continue

        # Define a lock file specific to the current file being processed
        lock_file_path = output_filepath + '.lock'

        with FileLock(lock_file_path):
            # Double-check if the file has been processed since we acquired the lock
            if os.path.exists(output_filepath) or is_file_processed(filename):
                print(f"Skipping {filename}, already processed.")
                continue

            print(f"Processing {filename}...")
            start_time = time.time()

            # Open the source raster
            with rasterio.open(input_filepath) as src:
                profile = src.profile
                profile.update(dtype=rasterio.float32)

                # Open a new file to write the transformed data
                with rasterio.open(output_filepath, 'w', **profile) as dst:
                    for ji, window in src.block_windows(1):
                        # Read the block
                        data = src.read(1, window=window)

                        # Initialize an empty array to hold the transformed z values
                        transformed_data = data.copy()

                        # Iterate over each pixel in the block
                        for i in range(data.shape[0]):
                            for j in range(data.shape[1]):
                                # Get the lon/lat for the pixel
                                lon, lat = src.xy(ji[0] + i, ji[1] + j)
                                # Get the height value
                                z = data[i, j]
                                # Transform the height value
                                _, _, transformed_z = transformer.transform(lon, lat, z)
                                transformed_data[i, j] = transformed_z

                        # Write the transformed block to the new file
                        dst.write(transformed_data, window=window, indexes=1)

            mark_file_as_processed(filename)
            end_time = time.time()
            print(f"Processed {filename} and saved to {output_filepath} in {end_time - start_time:.2f} seconds.")
