import os
import subprocess
from geotiff import GeoTiff

API_URL = "https://www.ollebo.com/api/v1/maps"
import requests





def updateMap(map):
    url = API_URL
    return requests.post(url, json = map)


def getGeoTiffData(tiff_file):
    
    geo_tiff = GeoTiff(tiff_file)
    geoData = {
        "originalCrsCode": geo_tiff.crs_code,
        "theCurrentCrsCode": geo_tiff.as_crs,
        "theShapeOfTheTiff": geo_tiff.tif_shape,
        "theBoundingBoxInTheAsCrsCRS": geo_tiff.tif_bBox,
        "theBoundingBoxAsWGS84" : geo_tiff.tif_bBox_wgs_84,
        "theBoundingBoxInTheAsCrsConvertedCoordinates": geo_tiff.tif_bBox_converted,
        "location": {
          "type": "Point",
          "coordinates": [geo_tiff.tif_bBox_wgs_84[0][0], geo_tiff.tif_bBox_wgs_84[0][1]]
    },
        "area": {
          "type": "LineString",
          "coordinates": [
            [geo_tiff.tif_bBox_wgs_84[0][0], geo_tiff.tif_bBox_wgs_84[0][1]],
            [geo_tiff.tif_bBox_wgs_84[1][0], geo_tiff.tif_bBox_wgs_84[1][1]]
          ]}

    }

    #for attr in dir(geo_tiff):
    #    print(f"{attr}: {getattr(geo_tiff, attr)}")
    return geoData


def makingTiles(map,destfile):
    """
    Making the tile and store them into a s3 bucket
    """
    tilesFolder="/data/web/"+map["format"]+"/"+map["mapID"]
    subprocess.run("/usr/bin/gdal2tiles.py --profile=mercator -z 8- --xyz -v "+destfile+" "+tilesFolder+" ", shell=True)

        




    



def makingMap(map):
    """
    This function is used to make a map from the geotiff file
    """
    print("Starting to make map")
    #Map data
    

    print("Making MapServer Map")
    if os.path.isfile("/data/maps/"+map["filename"]) == False:
        print("File not found /data/maps/"+map["filename"] )
        return "File not found"
    mapType=map["format"]
    mapID=map["filename"].split(".")[0]
    group="none"
           

    destinationFile="public"
    map.update({"mapType": mapType})
    map.update({"mapID": mapID})
    map.update({"group": group})
    map.update({"status": "Published"})
    map.update({"action": "map-published"})



    destfile="/data/maps/"+map["filename"]




    #Download file

    #Get data from geotiff
    map["fileData"]= getGeoTiffData(destfile)
    map["location"]= map["fileData"]["location"]
    map["area"]= map["fileData"]["area"]


    #Making tiles
    makingTiles(map,destfile)

    #Fiding the map
    #if map["access"] == "public":
    #    map["url"]="https://www.ollebo.com/tiles/"+map["publisher"]+"/"+map["format"]+"/"+map["mapid"]
    #else:
    #    map["url"]="https://www.ollebo.com/private-tiles/"+map["publisher"]+"/"+map["format"]+"/"+map["mapid"]






    #resones = updateMap(map) 
    #print(resones.text)
    print(map)
    return map


