"""Utilities for multi-resolution tsunami inundation processing.

This module implements the workflow that was previously shared via a code
snippet.  The goal of the refactor is to improve the consistency of results
across spatial resolutions by using a more inclusive definition of the
shoreline.  When the Digital Elevation Model (DEM) is downscaled to a coarser
resolution, using bilinear resampling can artificially raise the lowest cell
values.  The previous implementation detected the initial water mask directly
from the bilinearly resampled DEM, which could result in many coastal cells
being considered dry at coarse resolutions.  Consequently the inundated area
became much smaller for the same tsunami height.

To address this, the script now builds two virtual datasets (VRTs) for the
DEM:

* ``DEM_vrt`` – bilinear resampling for smooth elevation values used by the
  hydraulic solver.
* ``DEM_min_vrt`` – ``Resampling.min`` resampling that preserves the lowest
  source elevation present inside each coarse pixel.  The shoreline mask is
  derived from this dataset which ensures that if any high-resolution cell is
  at or below mean high water springs (MHWS), the entire coarse pixel is
  treated as water.  This change drastically reduces the resolution-induced
  shrinkage of the inundated area.

The remainder of the workflow (tiling, scenario iteration, raster writes) is
functionally equivalent to the original code shared by the user.  The only
behavioural change is the shoreline detection strategy.

Note: The repository does not contain the actual DEM data or the ``Functions``
module.  The script is therefore non-executable in this environment but is
structured so that the user can drop it into their project.
"""

from __future__ import annotations

import gc
import math
import os
from datetime import datetime
from typing import Dict, Iterable, Optional, Tuple

import numpy as np
import rasterio as rio
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from rasterio.windows import Window
from rasterio.warp import Resampling
from scipy.ndimage import binary_erosion

from Functions import TwoD_Crawl  # noqa: F401  # provided by the user's project


Scenario = Tuple[str, float]


def make_vrt(
    src: rio.DatasetReader,
    bounds: rio.coords.BoundingBox,
    target_res_m: float,
    resampling: Resampling,
) -> WarpedVRT:
    """Create a virtual raster at ``target_res_m`` using ``resampling``."""

    width = int((bounds.right - bounds.left) / target_res_m)
    height = int((bounds.top - bounds.bottom) / target_res_m)
    transform = from_origin(bounds.left, bounds.top, target_res_m, target_res_m)

    return WarpedVRT(
        src,
        crs=src.crs,
        transform=transform,
        width=width,
        height=height,
        resampling=resampling,
    )


def read_dem_block(vrt: WarpedVRT, win: Window) -> np.ndarray:
    """Read a DEM window and ensure finite elevation values."""

    dem = vrt.read(1, window=win).astype(np.float32)
    dem = np.nan_to_num(dem, nan=0.0)  # treat nodata as sea level
    dem[dem < 0] = 0.0
    return dem


def read_sea_mask_block(vrt: WarpedVRT, win: Window) -> np.ndarray:
    """Read the minimum-resampled DEM window and produce a water mask."""

    dem_min = vrt.read(1, window=win).astype(np.float32)
    dem_min = np.nan_to_num(dem_min, nan=9999.0)  # nodata -> dry
    mask = (dem_min <= 0.0).astype(np.uint8)
    return mask


def process_resolution(
    folder: str,
    region: str,
    area: str,
    dem_src: rio.DatasetReader,
    rough_path: Optional[str],
    scenarios: Iterable[Scenario],
    target_res: float,
    core_size: int = 3000,
    halo: int = 400,
    shoreline_structure: Optional[np.ndarray] = None,
) -> None:
    """Process a single resolution and export inundation rasters."""

    os.makedirs(f"{folder}/{region}/{area}", exist_ok=True)

    dem_vrt = make_vrt(dem_src, dem_src.bounds, target_res, Resampling.bilinear)
    dem_min_vrt = make_vrt(dem_src, dem_src.bounds, target_res, Resampling.min)

    rough_vrt = None
    rough_src = None
    if rough_path and os.path.exists(rough_path):
        rough_src = rio.open(rough_path)
        rough_vrt = make_vrt(rough_src, rough_src.bounds, target_res, Resampling.nearest)

    height = dem_vrt.height
    width = dem_vrt.width
    transform = dem_vrt.transform
    crs = dem_vrt.crs

    tiles_rows = math.ceil(height / core_size)
    tiles_cols = math.ceil(width / core_size)
    total_tiles = tiles_rows * tiles_cols

    print(f"计划总块数：{tiles_rows} x {tiles_cols} = {total_tiles}")

    nodata_val = -9999.0
    dst_map: Dict[str, rio.DatasetWriter] = {}

    for scen_id, _ in scenarios:
        out_tif = f"{folder}/{region}/{area}/{area}_{scen_id}_{target_res}m_full.tif"
        if os.path.exists(out_tif):
            os.remove(out_tif)

        dst = rio.open(
            out_tif,
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=1,
            dtype="float32",
            crs=crs,
            transform=transform,
            nodata=nodata_val,
            BIGTIFF="YES",
            tiled=True,
            blockxsize=256,
            blockysize=256,
            compress="lzw",
        )

        fill_row = np.full((1, width), nodata_val, dtype=np.float32)
        for r in range(height):
            dst.write(fill_row, 1, window=Window(0, r, width, 1))

        dst_map[scen_id] = dst

    if shoreline_structure is None:
        shoreline_structure = np.ones((3, 3), dtype=np.uint8)

    processed_tiles = 0
    start_all = datetime.now()

    for r0_core in range(0, height, core_size):
        for c0_core in range(0, width, core_size):
            r1_core = min(r0_core + core_size, height)
            c1_core = min(c0_core + core_size, width)
            core_win = Window(c0_core, r0_core, c1_core - c0_core, r1_core - r0_core)

            r0 = max(r0_core - halo, 0)
            c0 = max(c0_core - halo, 0)
            r1 = min(r1_core + halo, height)
            c1 = min(c1_core + halo, width)
            win = Window(c0, r0, c1 - c0, r1 - r0)

            dem_win = read_dem_block(dem_vrt, win)
            sea_mask_win = read_sea_mask_block(dem_min_vrt, win)

            eroded = binary_erosion(
                sea_mask_win,
                structure=shoreline_structure,
                border_value=0,
            ).astype(np.uint8)

            shoreline = (sea_mask_win - eroded).astype(np.uint8)

            if shoreline.max() == 0 and sea_mask_win.max() == 0:
                processed_tiles += 1
                if processed_tiles % 5 == 0:
                    elapsed = datetime.now() - start_all
                    pct = processed_tiles * 100.0 / total_tiles
                    print(
                        f"[{target_res}m] 已处理 {processed_tiles}/{total_tiles}"
                        f" ({pct:.1f}%)，耗时 {elapsed}"
                    )
                continue

            if rough_vrt is not None:
                rough_block = rough_vrt.read(1, window=win).astype(np.int32)
            else:
                rough_block = np.full(dem_win.shape, 5000, dtype=np.int32)

            rr0 = r0_core - r0
            cc0 = c0_core - c0
            rr1 = rr0 + (r1_core - r0_core)
            cc1 = cc0 + (c1_core - c0_core)

            for scen_id, h_tsunami in scenarios:
                fill_lvl = sea_mask_win.astype(np.float32, copy=True)
                fill_lvl[sea_mask_win == 1] = h_tsunami

                try:
                    inundation_win, _ = TwoD_Crawl(
                        int(r1 - r0),
                        int(c1 - c0),
                        dem_win,
                        h_tsunami,
                        10,
                        10,
                        rough_block,
                        fill_lvl,
                        shoreline,
                    )
                except MemoryError:
                    print(
                        f"[{target_res}m {scen_id}] 跳过块 r{r0}-{r1}, c{c0}-{c1}"
                    )
                    del fill_lvl
                    gc.collect()
                    continue

                inundation_win[fill_lvl > 0] = 0.0
                inundation_win = inundation_win + fill_lvl

                shoreline_vals = shoreline.astype(np.float32) * h_tsunami
                water_depth = inundation_win - fill_lvl + shoreline_vals
                water_depth = water_depth.astype(np.float32, copy=False)
                water_depth[water_depth <= 0] = nodata_val

                water_core = water_depth[rr0:rr1, cc0:cc1]
                dst_map[scen_id].write(water_core, 1, window=core_win)

                del fill_lvl, inundation_win, water_depth, water_core
                gc.collect()

            processed_tiles += 1
            if processed_tiles % 5 == 0:
                elapsed = datetime.now() - start_all
                pct = processed_tiles * 100.0 / total_tiles
                print(
                    f"[{target_res}m] 已处理 {processed_tiles}/{total_tiles}"
                    f" ({pct:.1f}%)，耗时 {elapsed}"
                )

            del dem_win, sea_mask_win, shoreline, eroded, rough_block
            gc.collect()

    for scen_id, dst in dst_map.items():
        dst.close()

    dem_vrt.close()
    dem_min_vrt.close()

    if rough_vrt is not None:
        rough_vrt.close()
    if rough_src is not None:
        rough_src.close()

    print(f"\n✅ 完成 {target_res} m: 输出在 {folder}/{region}/{area}")


def run_workflow(
    folder: str,
    region: str,
    area: str,
    dem_path: str,
    scenarios: Iterable[Scenario],
    resolutions: Iterable[float],
    roughness_path: Optional[str] = None,
) -> None:
    """Entry point for running the multi-resolution inundation workflow."""

    dem_src = rio.open(dem_path)

    try:
        for target_res in resolutions:
            print(f"\n=== Processing resolution {target_res} m ===")
            process_resolution(
                folder=folder,
                region=region,
                area=area,
                dem_src=dem_src,
                rough_path=roughness_path,
                scenarios=scenarios,
                target_res=target_res,
            )
    finally:
        dem_src.close()


if __name__ == "__main__":
    # Example configuration for the Napier 50-year ARI scenario.  Adapt the
    # file paths to match your local environment before executing.
    CONFIG = {
        "folder": "C:/Users/echs441/OneDrive - The University of Auckland/Desktop/Nationwide_inundation/Outputs",
        "region": "NorthIsland",
        "area": "Napier",
        "dem_path": "C:/Users/echs441/OneDrive - The University of Auckland/Desktop/Nationwide_inundation/DEM/Latest_North_Island_Merged_LiDAR_and_FABDEM.tif",
        "scenarios": [("H50y84p", 1.8)],
        "resolutions": [5, 10, 20],
        "roughness_path": None,
    }

    run_workflow(**CONFIG)
