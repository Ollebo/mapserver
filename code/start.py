#!/usr/bin/env python
import json
import os

import names
from flask import Flask, request, render_template, redirect, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from listMaps import listFiles, variants_for_map
from mapmaker.makingGeotiff import makingMap, scan_and_ingest


UPLOAD_FOLDER = "/data/maps"
ALLOWED_EXTENSIONS = {"tif"}
TERRACOTTA_PUBLIC_URL = os.environ.get("TERRACOTTA_PUBLIC_URL", "http://localhost:5001")
SPACE_ID = os.environ.get("OLLEBO_SPACE_ID", "local")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
CORS(app)


@app.route("/", methods=["GET", "POST"])
def start():
    if request.method == "POST":
        return "Move along nothing to see"
    files = json.loads(json.dumps(listFiles()))
    return render_template("home.html", title="Home", files=files)


@app.route("/map", methods=["GET", "POST"])
def map():
    name = request.values.get("name", "")
    map_id = name.rsplit(".", 1)[0] if name else ""
    variants = variants_for_map(SPACE_ID, map_id) if map_id else []
    return render_template(
        "map.html",
        title="Map",
        filename=name,
        map_id=map_id,
        space_id=SPACE_ID,
        variants=variants,
        terracotta_url=TERRACOTTA_PUBLIC_URL,
    )


@app.route("/rescan", methods=["POST"])
def rescan():
    scan_and_ingest()
    return redirect("/")


@app.route("/mapmaker", methods=["POST"])
def mapmaker():
    name = request.form.get("name")
    tags = request.form.get("tags") or request.form.get("tag")
    location = request.form.get("locations") or request.form.get("location")
    mapToMake = {
        "filename": name,
        "format": "tif",
        "tags": tags,
        "locations": location,
        "publisher": "ollebo",
    }
    makingMap(mapToMake)
    return redirect("/map?name=" + name)


@app.route("/public/<path:path>", methods=["GET"])
def public(path):
    return send_from_directory("public", path)


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            print("No file part")
        file = request.files["file"]
        if file.filename == "":
            print("No selected file")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(
                app.config["UPLOAD_FOLDER"],
                names.get_first_name() + "-" + filename,
            ))
            return redirect("/")

    return render_template("upload.html", title="Upload")
