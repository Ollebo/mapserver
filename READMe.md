# Mapserver 
This docker is build to setup a local ore docker based map server.
The server then supports 

- Upload off tif images
- Making tiles from tif images
- Displaying the tiles


The map server can be run in 

- Docker
- Kubernetes

And can be hosted on any provider that has a Kuberneteser cluster and support block storage (they all do).


## OlleBo Cloud
The Mapserver is build to easy integrarte into the OlleBo cloud and to host you private images on your own locations.
The location can be any provider that supports Kubernetes ore docker run time. Have a storgage for the maps and tiles.
and a external ip that be used to access ti tiles.

Then by linking your mapserver to you account on OlleBo you now can access your private maps from the OlleBo cloud.

#### Large installation
If you are running a large instalaltion you may need to add a CDN infront of the mapserver


#### Access
You self controll the access to the tiles server. Support will come for better but as now there are now auth module


## Docker 
To tets the map server have docker install and create this docker-compose file.


```
version: '2'
services:
  map-server:
    image: ollebo/mapserver
    volumes:
      - ./web:/data/web
      - ./maps:/data/maps
    ports:
      - 8888:8080
    environment:
      - API=http://api.ollebo.com
```

To store the map and tiles the folder web and maps are created.
Mount them if you already habe folder for maps

the maps folder will hold the tif files and the web folder is for the tiles that need to be renderd.


