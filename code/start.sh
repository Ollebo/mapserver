#!/bin/bash
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

echo "Ensuring settings table..."
python3 -c 'from config import ensure_settings_table; ensure_settings_table()' || echo "settings init failed, continuing to flask"

echo "Scanning /data/maps for new files..."
python3 -c 'from mapmaker.makingGeotiff import scan_and_ingest; scan_and_ingest()' || echo "scan failed, continuing to flask"

FLASK_APP=start.py flask run --host=0.0.0.0 --port=8080
