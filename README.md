# Map Server
Map Server for Ollebo lets you host your map server at one of our partner's or by your self.
It will scan and find maps from the disk, Tile the maps, and serve the tiles from a webserver.
It will connect to OlleBo API and update your account with the maps data.


## Full vs Split
Mapserver can be hosted as a Full version where every part runs inside the map server, and all map images are stored at the MapServer or hosting partner.
Ore, it can be run as Split.
In split mode, the parts that render the tiles are run by the hosting provider, but the image detecting and tiling of the map are run on a local computer.
This makes it easy to have one Map Server for several Phootgrafers.


Read more about how you set full ore split mode.





## Install
Map server is made to run in a Kubernetes cluster and can be run by any hosting provider or service that offers a Kubernetes cluster.
You can also run it on your own Kubernetes cluster.





### Req
- Kubernetes cluster (for the service)
- Disk where the images are stored (source image and tiles that are made)
- External IP (So that you can access the images . Can also work with DNS name if you share IP )
- API key from OlleBo (So that maps end up in the right place)
- In Split mode Loadbalanser access for uploading map (SSH)

- Will be nice if the you have disk för many read and write then x number of web servers can be run-
- For large and many images dedicated nodes for making tiles is smart 


### Install ed with helm
Install the MapServer by using helm 

GUIDE HERE WHEN READY

## Disk 
Map Server needs 2 types of disk. "Source Disk" is where the map image is stored in geotiff format (We may update later). Map server will then read the image and make it to tiles and 
store it on the "Map Disk".
You need access to the source disk to add and upload new maps. So, when adding a Map Server to a hosting provider, access to that disk is important.
the Map Diks is where the tiles are saved and that need access only by the webserver that serves the tiles to the users.



## Full Modes
In full mode all the service are run in the Hosting provider. We have a list of hosting provider that we have testet but the Map Server will run on any Kubernetest cluster.
In hosting node access to the "Map Source" (we look at bucket access) and you need to be able to upload files so they are stored in the correct way.

## Split mode
In split mode, only the part that serves the map to the users is run in the Cluster / hosting provider.
Then collection of map and tiling them are run localy on your computer.
Now you can add map to the "Map Source" folder. Maps are now deteced and send to the hosted Map Server.






 
