import os
# Get the list of all files and directories


def listFiles():
    path = "/data/maps/"
    dir_list = os.listdir(path)
    print("Files and directories in '", path, "' :")
    # prints all files
    files=[]
    for file in dir_list:
        filetype = file.split(".")[1]
        if filetype == "tif":
            fileData = {
                "filename": file,
                "format": "tif",
                "tags": "",
                "locations": "",
                "tiles:": ""
            }
            #Check if we have made tiles
            if os.path.exists("/data/web/"+filetype+"/"+file.split(".")[0]):
                fileData["tiles"] = "yes"
                fileData["link"] = "/tiles/"+filetype+"/"+file.split(".")[0]+"/leaflet.html"
            files.append(fileData)


    print(files)
    return files