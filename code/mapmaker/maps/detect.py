import re

import rasterio
from rasterio.enums import ColorInterp


NIR_HINT = re.compile(r"nir|842|b5|rededge|red\s*edge", re.IGNORECASE)


def _band_looks_like_nir(ds, idx):
    desc = (ds.descriptions[idx - 1] or "")
    if NIR_HINT.search(desc):
        return True
    tags = ds.tags(idx)
    for value in tags.values():
        if NIR_HINT.search(str(value)):
            return True
    return False


def detect_input_type(path):
    with rasterio.open(path) as ds:
        count = ds.count
        dtype = ds.dtypes[0]
        colorinterp = list(ds.colorinterp)

        if count == 1:
            has_palette = False
            try:
                ds.colormap(1)
                has_palette = True
            except ValueError:
                pass
            if not has_palette:
                return "dem", {"r": None, "g": None, "b": None, "nir": None, "dtype": dtype}

        if count >= 4 and dtype in ("uint8", "uint16"):
            nir_idx = None
            for i in range(4, count + 1):
                if _band_looks_like_nir(ds, i):
                    nir_idx = i
                    break
            if nir_idx is None and count == 4 and colorinterp[3] in (ColorInterp.undefined, ColorInterp.gray):
                nir_idx = 4
            if nir_idx is not None:
                return "multispectral", {"r": 1, "g": 2, "b": 3, "nir": nir_idx, "dtype": dtype}

        if count in (3, 4) and ColorInterp.red in colorinterp:
            return "rgb", {"r": 1, "g": 2, "b": 3, "nir": None, "dtype": dtype}

        if dtype == "uint8" and count >= 3:
            return "rgb", {"r": 1, "g": 2, "b": 3, "nir": None, "dtype": dtype}

        return "dem", {"r": None, "g": None, "b": None, "nir": None, "dtype": dtype}
