import os
import subprocess
import tempfile


RAMPS_DIR = os.path.join(os.path.dirname(__file__), "ramps")

COG_CO = [
    "-co", "COMPRESS=DEFLATE",
    "-co", "PREDICTOR=2",
    "-co", "OVERVIEWS=AUTO",
    "-co", "BLOCKSIZE=512",
]


def _run(argv):
    print("[cog] " + " ".join(argv))
    subprocess.run(argv, check=True, capture_output=True, text=True)


def _scale_args(dtype):
    if dtype == "uint16":
        return ["-scale", "0", "65535", "0", "255"]
    return ["-scale"]


def _channel_key(name, channel):
    return "{0}__{1}".format(name, channel)


def build_rgb(input_path, out_dir, name, bands):
    # Terracotta's /rgb endpoint composites three single-band datasets, so we
    # split source R/G/B into three separate single-band COGs.
    scale = _scale_args(bands["dtype"])
    outputs = {}
    for channel, src_band in (("r", bands["r"]), ("g", bands["g"]), ("b", bands["b"])):
        out = os.path.join(out_dir, "{0}.tif".format(_channel_key(name, channel)))
        _run([
            "gdal_translate", "-of", "COG", "-ot", "Byte",
            "-b", str(src_band),
        ] + scale + COG_CO + [input_path, out])
        outputs[_channel_key(name, channel)] = out
    return outputs


def build_grayscale(input_path, out_dir, name, bands):
    out = os.path.join(out_dir, "{0}.tif".format(name))
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
        intermediate = tmp.name
    try:
        _run([
            "gdal_calc.py",
            "--calc=0.299*R+0.587*G+0.114*B",
            "-R", input_path, f"--R_band={bands['r']}",
            "-G", input_path, f"--G_band={bands['g']}",
            "-B", input_path, f"--B_band={bands['b']}",
            "--type=Byte",
            f"--outfile={intermediate}",
            "--overwrite",
        ])
        _run(["gdal_translate", "-of", "COG"] + COG_CO + [intermediate, out])
    finally:
        if os.path.exists(intermediate):
            os.unlink(intermediate)
    return {name: out}


def build_ndvi(input_path, out_dir, name, bands):
    out = os.path.join(out_dir, "{0}.tif".format(name))
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
        intermediate = tmp.name
    try:
        _run([
            "gdal_calc.py",
            "--calc=(NIR.astype(float)-R)/(NIR+R+1e-6)",
            "-R", input_path, f"--R_band={bands['r']}",
            "--NIR", input_path, f"--NIR_band={bands['nir']}",
            "--type=Float32",
            "--NoDataValue=-9999",
            f"--outfile={intermediate}",
            "--overwrite",
        ])
        _run(["gdal_translate", "-of", "COG"] + COG_CO + [intermediate, out])
    finally:
        if os.path.exists(intermediate):
            os.unlink(intermediate)
    return {name: out}


def build_hillshade(input_path, out_dir, name, bands):
    out = os.path.join(out_dir, "{0}.tif".format(name))
    _run([
        "gdaldem", "hillshade",
        "-of", "COG",
        "-compute_edges",
        "-z", "1.0", "-az", "315", "-alt", "45",
        "-co", "COMPRESS=DEFLATE",
        input_path, out,
    ])
    return {name: out}


def build_color_relief(input_path, out_dir, name, bands):
    # gdaldem color-relief produces a 3-band RGB tif; split into single-band
    # COGs so terracotta's /rgb endpoint can composite them.
    ramp = os.path.join(RAMPS_DIR, "dem.txt")
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
        intermediate = tmp.name
    try:
        _run([
            "gdaldem", "color-relief",
            "-of", "GTiff",
            "-co", "COMPRESS=DEFLATE",
            input_path, ramp, intermediate,
        ])
        outputs = {}
        for channel, src_band in (("r", 1), ("g", 2), ("b", 3)):
            out = os.path.join(out_dir, "{0}.tif".format(_channel_key(name, channel)))
            _run([
                "gdal_translate", "-of", "COG", "-ot", "Byte",
                "-b", str(src_band),
            ] + COG_CO + [intermediate, out])
            outputs[_channel_key(name, channel)] = out
        return outputs
    finally:
        if os.path.exists(intermediate):
            os.unlink(intermediate)


def build_slope(input_path, out_dir, name, bands):
    out = os.path.join(out_dir, "{0}.tif".format(name))
    _run([
        "gdaldem", "slope",
        "-of", "COG",
        "-compute_edges",
        "-s", "1.0",
        "-co", "COMPRESS=DEFLATE",
        input_path, out,
    ])
    return {name: out}
