import os

from terracotta import get_driver, exceptions


KEY_NAMES = ["space", "map", "variant"]
KEY_DESCRIPTIONS = {
    "space": "Ollebo space (tenant) ID",
    "map": "Map ID within the space",
    "variant": "Rendering variant (rgb, grayscale, ndvi, hillshade, ...)",
}


def _driver():
    db_path = os.environ.get("TERRACOTTA_DB_PATH", "/data/db/terracotta.sqlite")
    provider = os.environ.get("TERRACOTTA_PROVIDER", "sqlite")
    return get_driver(db_path, provider=provider)


def ensure_schema():
    driver = _driver()
    try:
        with driver.connect():
            if not driver.key_names:
                driver.create(KEY_NAMES, key_descriptions=KEY_DESCRIPTIONS)
    except exceptions.InvalidDatabaseError:
        driver.create(KEY_NAMES, key_descriptions=KEY_DESCRIPTIONS)


def replace_map(space_id, map_id):
    driver = _driver()
    with driver.connect():
        if not driver.key_names:
            return
        datasets = driver.get_datasets(where={"space": space_id, "map": map_id})
        for key_tuple in list(datasets.keys()):
            driver.delete(dict(zip(driver.key_names, key_tuple)))


# Cap the array Terracotta reads when computing band statistics. Without the
# optional `crick` dependency, Terracotta otherwise reads the FULL uncompressed
# raster into memory (rasterio out_shape = full height x width), which OOMKills
# the worker on large orthos. A decimated read at <=1024x1024 is plenty: the
# tile URLs pin an explicit stretch_range=[0,255], so exact percentiles aren't
# used for rendering anyway. See terracotta.raster.compute_image_stats.
_STATS_MAX_SHAPE = (1024, 1024)


def register(space_id, map_id, variant_name, s3_uri):
    driver = _driver()
    with driver.connect():
        metadata = driver.compute_metadata(s3_uri, max_shape=_STATS_MAX_SHAPE)
        driver.insert(
            {"space": space_id, "map": map_id, "variant": variant_name},
            s3_uri,
            override_path=s3_uri,
            metadata=metadata,
        )
