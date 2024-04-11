import os
# Get the list of all files and directories


def listTiles():
    path = "/data/web/tif"
    if os.path.exists(path) == False:
        os.mkdir(path)
    dir_list = os.listdir(path)
    print("Files and directories in '", path, "' :")
    # prints all files
    files=[]
    for file in dir_list:
        fileData = {
                "filename": file,
                "format": "tif",
                "tags": "",
                "locations": "",
                "tiles:": ""
            }
            #Check if we have made tiles

        #fileData["tiles"] = "yes"
        fileData["link"] = "/tiles/tif/"+file+"/leaflet.html"
        files.append(fileData)


    print(files)
    return files

#listFiles()