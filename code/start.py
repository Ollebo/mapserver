#
#
#
# File to start
#
# Lissen for events from the que
#!/usr/bin/env python
import time
import time
import json
import os
import names
from flask import Flask, request, render_template, url_for, redirect, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename


from listMaps import listFiles
from listTiles import listTiles
from mapmaker.makingGeotiff import makingMap


UPLOAD_FOLDER = '/data/maps'
ALLOWED_EXTENSIONS = {'tif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app ,resources={r"/maps/*": {"origins": "*"}})





@app.route("/", methods = ['GET', 'POST'])
def start():
	if request.method == 'POST':
		print(request.get_data(as_text=True))
		return "Move along nothing to see"
	else:
		files = json.loads(json.dumps(listFiles()))
		return render_template('home.html', title='Home', files=files)
	
@app.route("/map", methods = ['GET', 'POST'])
def map():
	if request.method == 'POST':
		reqData = request.form.get('name')
		return render_template('map.html', title='Map', filename=reqData)
	else:
		
		return render_template('map.html', title='Map')


@app.route("/mapmaker", methods = ['POST'])
def mapmaker():
		reqName = request.form.get('name')
		reqTags = request.form.get('tags')
		reqLocations = request.form.get('locations')
		mapToMake = {
		    "filename": reqName,
		    "format": "tif",
			"tags": reqTags,
			"locations": reqLocations,
		    "publisher": "ollebo"}
		print(mapToMake)
		mapData = makingMap(mapToMake)
		mapData = "test"
		return render_template('mapmaker.html', title='Map', filename=reqName, tags=reqTags, locations=reqLocations, mapData=mapData)
	
@app.route("/maptiles", methods = ['GET'])
def maptiles():
		files = json.loads(json.dumps(listTiles()))
		return render_template('tiles.html', title='Map' , files=files)


## Public tiles
@app.route("/tiles/<path:path>", methods = ['GET'])
def tiles(path):
	return send_from_directory('/data/web', path)


## Public folder
@app.route("/public/<path:path>", methods = ['GET'])
def public(path):
	return send_from_directory('public', path)


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            print('No file part')
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            print('No selected file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], names.get_first_name()+"-"+filename))
            return redirect("/")

    return render_template('upload.html', title='Upload')