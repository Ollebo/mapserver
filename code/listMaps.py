import os

from mapmaker.maps import terracotta_client


SOURCE_DIR = "/data/maps"


def _existing_variants(space_id):
    """Return {map_id: [variant, ...]} for all datasets currently in the DB."""
    try:
        driver = terracotta_client._driver()
        with driver.connect():
            if not driver.key_names:
                return {}
            datasets = driver.get_datasets(where={"space": space_id})
    except Exception as e:
        print("terracotta lookup failed: {0}".format(e))
        return {}

    by_map = {}
    for key_tuple in datasets.keys():
        keys = dict(zip(driver.key_names, key_tuple))
        by_map.setdefault(keys["map"], []).append(keys["variant"])
    return by_map


def variants_for_map(space_id, map_id):
    return _existing_variants(space_id).get(map_id, [])


def listFiles():
    # Home is driven by terracotta, not the folder scan. A .tif removed from
    # /data/maps but still present in the DB will keep showing up here —
    # cleanup of orphaned DB rows is intentionally out of scope.
    space_id = os.environ.get("OLLEBO_SPACE_ID", "local")
    variants_by_map = _existing_variants(space_id)

    files = []
    for map_id, variants in sorted(variants_by_map.items()):
        filename = "{0}.tif".format(map_id)
        files.append({
            "filename": filename,
            "mapID": map_id,
            "variants": variants,
            "link": "/map?name={0}".format(filename),
        })

    return files
