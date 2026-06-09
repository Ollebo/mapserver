import os

import rasterio
from rasterio.warp import transform_bounds
import requests

from mapmaker.maps import terracotta_client
from mapmaker.maps.detect import detect_input_type
from mapmaker.maps.variants import VARIANTS


API_URL = os.environ.get("API", "https://www.ollebo.com/api/v1")
SOURCE_DIR = "/data/maps"
COG_DIR = "/data/cogs"
TERRACOTTA_PUBLIC_URL = os.environ.get("TERRACOTTA_PUBLIC_URL", "http://localhost:5001")


def updateMap(map):
    return requests.post("{0}/maps/".format(API_URL), json=map)


def getGeoTiffData(tiff_file):
    with rasterio.open(tiff_file) as src:
        src_crs = src.crs
        src_epsg = src_crs.to_epsg() if src_crs else None
        height, width, count = src.height, src.width, src.count
        left, bottom, right, top = src.bounds
        west, south, east, north = transform_bounds(
            src_crs, "EPSG:4326", left, bottom, right, top
        )

    bbox_src = [[left, top], [right, bottom]]
    bbox_wgs84 = [[west, north], [east, south]]

    return {
        "originalCrsCode": src_epsg,
        "theCurrentCrsCode": 4326,
        "theShapeOfTheTiff": [height, width, count],
        "theBoundingBoxInTheAsCrsCRS": bbox_src,
        "theBoundingBoxAsWGS84": bbox_wgs84,
        "theBoundingBoxInTheAsCrsConvertedCoordinates": bbox_wgs84,
        "location": {
            "type": "Point",
            "coordinates": [bbox_wgs84[0][0], bbox_wgs84[0][1]],
        },
        "area": {
            "type": "LineString",
            "coordinates": [
                [bbox_wgs84[0][0], bbox_wgs84[0][1]],
                [bbox_wgs84[1][0], bbox_wgs84[1][1]],
            ],
        },
    }


def _tile_url(space_id, map_id, spec):
    base = "singleband" if spec.singleband else "rgb"
    url = "{0}/{1}/{2}/{3}/{4}/{{z}}/{{x}}/{{y}}.png".format(
        TERRACOTTA_PUBLIC_URL, base, space_id, map_id, spec.name
    )
    if spec.colormap and spec.singleband:
        url += "?colormap=" + spec.colormap
    return url


def makingTiles(map):
    space_id = map["spaceID"]
    map_id = map["mapID"]
    source_path = os.path.join(SOURCE_DIR, map["filename"])

    cog_out_dir = os.path.join(COG_DIR, space_id, map_id)
    os.makedirs(cog_out_dir, exist_ok=True)

    input_type, bands = detect_input_type(source_path)
    print("detected: {0} bands={1}".format(input_type, bands))

    terracotta_client.ensure_schema()
    terracotta_client.replace_map(space_id, map_id)

    variants_meta = []
    for spec in VARIANTS[input_type]:
        cog_path = os.path.join(cog_out_dir, "{0}.tif".format(spec.name))
        status = "ok"
        try:
            spec.build(source_path, cog_path, bands)
            terracotta_client.register(space_id, map_id, spec.name, cog_path)
        except Exception as e:
            print("variant {0} failed: {1}".format(spec.name, e))
            status = "failed"

        variants_meta.append({
            "variant": spec.name,
            "tilesURL": _tile_url(space_id, map_id, spec) if status == "ok" else None,
            "colormap": spec.colormap,
            "singleband": spec.singleband,
            "status": status,
        })

    return input_type, variants_meta


def makingMap(map):
    print("Starting to make map")
    source_path = os.path.join(SOURCE_DIR, map["filename"])
    if not os.path.isfile(source_path):
        print("File not found " + source_path)
        return "File not found"

    map_id = map["filename"].rsplit(".", 1)[0]
    space_id = os.environ.get("OLLEBO_SPACE_ID", "local")

    map["spaceID"] = space_id
    map["mapID"] = map_id
    map["mapType"] = map.get("format", "tif")
    map["status"] = "Published"
    map["action"] = "map-published"

    map["mapData"] = getGeoTiffData(source_path)
    map["location"] = map["mapData"]["location"]
    map["area"] = map["mapData"]["area"]

    input_type, variants_meta = makingTiles(map)
    map["inputType"] = input_type
    map["variants"] = variants_meta

    successful = [v for v in variants_meta if v["status"] == "ok"]
    map["tilesURL"] = successful[0]["tilesURL"] if successful else None
    if not successful:
        map["action"] = "error"
    elif len(successful) < len(variants_meta):
        map["action"] = "partial"

    # ollebo.com sync — left dormant; will be wired up in a follow-up.
    # updateMap(map)

    print(map)
    return map


def _registered_map_ids(space_id):
    try:
        driver = terracotta_client._driver()
        with driver.connect():
            if not driver.key_names:
                return set()
            datasets = driver.get_datasets(where={"space": space_id})
    except Exception as e:
        print("scan: terracotta lookup failed: {0}".format(e))
        return set()

    ids = set()
    for key_tuple in datasets.keys():
        keys = dict(zip(driver.key_names, key_tuple))
        ids.add(keys["map"])
    return ids


def scan_and_ingest(maps_dir=SOURCE_DIR):
    """Ingest every .tif in maps_dir that isn't yet registered in terracotta.

    Returns {"processed": [...], "skipped": [...], "failed": [...]}. Failures
    are caught per-file so one bad TIFF doesn't kill the whole scan.
    """
    result = {"processed": [], "skipped": [], "failed": []}
    if not os.path.isdir(maps_dir):
        print("scan: {0} does not exist, skipping".format(maps_dir))
        return result

    space_id = os.environ.get("OLLEBO_SPACE_ID", "local")
    terracotta_client.ensure_schema()
    registered = _registered_map_ids(space_id)

    for name in sorted(os.listdir(maps_dir)):
        if "." not in name or name.rsplit(".", 1)[1].lower() != "tif":
            continue
        map_id = name.rsplit(".", 1)[0]
        if map_id in registered:
            result["skipped"].append(name)
            continue
        try:
            makingMap({
                "filename": name,
                "format": "tif",
                "tags": "",
                "locations": "",
                "publisher": "ollebo",
            })
            result["processed"].append(name)
        except Exception as e:
            print("scan: ingest failed for {0}: {1}".format(name, e))
            result["failed"].append(name)

    print("scan: processed={0} skipped={1} failed={2}".format(
        len(result["processed"]), len(result["skipped"]), len(result["failed"])
    ))
    return result
