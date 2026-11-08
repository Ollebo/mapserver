# OlleBo Mapserver

Host your own drone and satellite maps, and show them in [ollebo.com](https://www.ollebo.com) without uploading the imagery.

You run the mapserver on your own machine or Kubernetes cluster. It turns GeoTIFF files into map tiles and serves them from your own servers. It tells ollebo.com which maps exist and where their tiles are, so they show up in your Space next to everything else. The map images stay on your servers. Viewers' browsers load the tiles straight from your server.

> **You need your own authentication.** The mapserver has no login. Before you expose it to the internet, put it behind your own access control. See [Authentication is your job](#authentication-is-your-job).

## What it does

- **Turns GeoTIFFs into maps.** Upload a `.tif` in the web UI, or drop it in the maps folder. The mapserver detects what kind of image it is and builds the right views:

  | Source | Views it builds |
  |---|---|
  | RGB photo (orthophoto) | `rgb`, `grayscale` |
  | Multispectral | `rgb`, `grayscale`, `ndvi` |
  | Elevation model (DEM) | `hillshade`, `color-relief`, `slope` |

- **Serves map tiles.** Each view is served as standard XYZ tiles (`/{z}/{x}/{y}.png`). Tiles are rendered on request from Cloud-Optimized GeoTIFFs (COGs), so nothing is pre-generated.
- **Connects to your ollebo.com Space with a map key.** Every finished map is listed in that Space, private to its members.
- **Has a local viewer.** The built-in web UI shows each map with a view picker, so you can check a map before anyone else sees it.

## How it works

```
                    ┌──────────────── your infrastructure ────────────────┐
                    │                                                     │
  .tif upload ────► │  Web UI (Flask, :8080)                              │
                    │    1. detect the image type                         │
                    │    2. build COG views     ──►  /data/cogs           │
                    │    3. add them to the tile store ──► /data/db       │
                    │                                                     │
                    │  Tile server (Terracotta, :5000)  ◄── tile requests │
                    └───────────────┬─────────────────────────▲───────────┘
                                    │ 4. register map         │ 5. browser loads
                                    │    (name, bounds,       │    tiles directly
                                    │    tile URL, views)     │    from your server
                                    ▼                         │
                         ollebo.com API ───── lists map ──► dash.ollebo.com
```

1. **Detect.** The mapserver opens the GeoTIFF and decides whether it is RGB, multispectral or an elevation model.
2. **Build.** It runs GDAL to write one Cloud-Optimized GeoTIFF per view into `/data/cogs`.
3. **Index.** It adds each COG to Terracotta's tile store (an SQLite file in `/data/db`).
4. **Register.** It sends ollebo.com the map's name, bounds, views and public tile URL. It authenticates with your map key. Only this description is sent; the imagery never is.
5. **View.** Members of your Space see the map in ollebo.com. Their browsers fetch the tiles from your public tile URL.

The mapserver keeps working when ollebo.com can't be reached. Maps still build and show in the local viewer, and they are sent again the next time you save Settings or click Rescan.

## Authentication is your job

The mapserver has **no login and no access control of its own**. Plan for this before you install.

**The web UI (port 8080)** can upload files, rebuild maps and show your map key. Never expose it publicly. Keep it on a private network, a VPN, or a `kubectl port-forward`. If people need it remotely, put it behind your own sign-in, for example oauth2-proxy, Cloudflare Access, your Ingress controller's authentication, or your company's SSO gateway. The Helm chart keeps the UI off the Ingress unless you set `ingress.exposeUi=true`.

**The tile server (port 5000)** has to be reachable by the browsers of everyone who views your maps. Anyone who can reach it and knows a map's tile URL can load its tiles. ollebo.com only lists your maps to members of your Space, but it does not protect the tile server itself.

The ollebo.com map viewer fetches your tiles without cookies or login headers, so a login page in front of the tile server will stop tiles from showing. Protect the tile server with network-level rules instead:
- an IP allowlist for your offices
- a VPN that your viewers are connected to
- a firewall or network policy

If none of that fits, at least treat the tile hostname as unlisted.

You are responsible for securing your installation and the data on it.

## Need help hosting it?

If you'd rather not run it yourself, our partner **[Ankra](https://ankra.io)** can host and run the mapserver for you, in **Sweden** or the **US**. Contact them through [ankra.io](https://ankra.io).

---

## Quick start: Docker

For one machine, a trial, or a small install.

```sh
git clone https://github.com/ollebo/mapserver.git
cd mapserver
bash install/docker-install.sh
```

The script checks for `docker` and `docker compose`. It asks for your map key and public tile URL and writes them to `.env`. Then it creates the `maps/`, `cogs/` and `db/` folders and starts the stack.

Open `http://localhost:8888` and upload a `.tif`. The tiles are on `http://localhost:5001`.

- **Change settings:** edit `.env`, then run `docker compose up -d`.
- **Stop:** `docker compose down`.
- **Your files:** they stay in `maps/`, `cogs/` and `db/`.

`docker-compose.override.yaml` mounts `./code` into the containers for live editing. Docker Compose loads it automatically. Delete it if you only want to run the built image.

## Install: Kubernetes (Helm)

For a permanent install with a public tile hostname.

```sh
helm install mapserver oci://ghcr.io/ollebo/charts/mapserver \
  --namespace mapserver --create-namespace \
  --set ollebo.key=YOUR_MAP_KEY \
  --set ingress.enabled=true \
  --set ingress.host=tiles.example.com \
  --set ingress.tlsSecret=tiles-example-com-tls \
  --set terracotta.publicUrl=https://tiles.example.com
```

What the chart creates:
- One pod with two containers: the web UI and the tile server.
- Three persistent volumes, for `maps`, `cogs` and `db`.
- One Service.
- An optional Ingress that publishes only the tile routes (`/rgb`, `/singleband`).

The chart runs a single replica, because the tile store is SQLite on `ReadWriteOnce` volumes.

To reach the web UI:

```sh
kubectl -n mapserver port-forward svc/mapserver 8888:8080
```

Then open `http://localhost:8888`. `helm get notes mapserver -n mapserver` prints the same command and your tile URL.

The full value reference is in [install/helm/mapserver/README.md](install/helm/mapserver/README.md) and [values.yaml](install/helm/mapserver/values.yaml).

## Connecting to ollebo.com

1. Sign in at [ollebo.com](https://www.ollebo.com). Open the Space where the maps should appear, and create a mapserver. Creating one needs the Pro or Full plan. You get a **map key**.
2. Give the key to the mapserver. Either set `OLLEBO_KEY` or `ollebo.key` at install, or paste it on the **Settings** page.
3. Set the **public tile URL** to the address viewers' browsers will use, e.g. `https://tiles.example.com`.
4. Save Settings. The page shows **Connected to ollebo.com — _mapserver_ in _space_**, and every map already built is sent to the Space.

From then on, each new map is sent when it finishes. When you change the public tile URL, save Settings again; the maps keep their place in ollebo.com and get the new address.

If the status says **Map key not accepted**, the key is wrong or its mapserver was deleted on ollebo.com. If it says **Can't reach ollebo.com**, check outbound HTTPS from the server.

The map key gives full control over that mapserver's maps on ollebo.com. Keep it secret. If it leaks, regenerate it on ollebo.com and paste the new one on the Settings page.

## Configuration

| Variable | Helm value | Default | What it does |
|---|---|---|---|
| `OLLEBO_KEY` | `ollebo.key` | _(empty)_ | Your map key. A key saved on the Settings page takes priority. |
| `TERRACOTTA_PUBLIC_URL` | `terracotta.publicUrl` | `http://localhost:5001` | Tile address that viewers' browsers use. |
| `API` | `ollebo.apiUrl` | `https://www.ollebo.com/api` | ollebo.com API. |
| `OLLEBO_SPACE_ID` | `ollebo.spaceId` | `local` | Folder name for your maps inside the local tile store. It doesn't need to match ollebo.com. |
| `TERRACOTTA_DB_PATH` | `terracotta.dbPath` | `/data/db/terracotta.sqlite` | Location of the tile store. |
| `TC_ALLOWED_ORIGINS_TILES` | `terracotta.allowedOrigins` | `dash.ollebo.com`, `dash.northamlin.com` | Websites allowed to load your tiles (CORS). |

## Storage

| Folder | Mounted at | Contains |
|---|---|---|
| `maps/` | `/data/maps` | Your source GeoTIFFs. |
| `cogs/` | `/data/cogs` | Generated views, as `<space>/<map>/<variant>.tif`. |
| `db/` | `/data/db` | Terracotta's tile store and the Settings page values. |

Back up `maps/` and `db/`. `cogs/` can be rebuilt from `maps/` with Rescan.

## Development

```
code/
  start.py              Flask routes: home, upload, map viewer, rescan, settings
  start.sh              Container start: prepare the database, scan /data/maps, start gunicorn
  config.py             Settings storage (SQLite)
  ollebo.py             Calls to the ollebo.com API using the map key
  listMaps.py           Lists maps for the home page
  mapmaker/
    makingGeotiff.py    Build pipeline and syncing with ollebo.com
    maps/               Image detection, COG building, view definitions, Terracotta client
  templates/, public/   Web UI
install/
  docker-install.sh     Interactive Docker install
  helm/mapserver/       Helm chart
```

The code under `code/mapmaker/maps/` is shared with OlleBo's hosted `map-maker` service. Port changes to both.

Run locally with `docker compose up --build`. The override file mounts `./code`, so Python changes apply when the containers restart.

## Releases

CI (`.github/workflows/docker-publish.yml`) builds the image and lints the chart on every pull request and push to `main`:

| Published to | Tag | When |
|---|---|---|
| `ghcr.io/ollebo/mapserver` | `latest`, `sha-<short>` | Every push to `main` |
| `ghcr.io/ollebo/mapserver` | `X.Y.Z` | Git tags `vX.Y.Z` |
| `oci://ghcr.io/ollebo/charts/mapserver` | `X.Y.Z` | Git tags `vX.Y.Z`, published after the image |

## Known limitations

- **No authentication.** See [Authentication is your job](#authentication-is-your-job).
- **Maps deleted on ollebo.com come back.** They return the next time you save Settings or click Rescan. To keep a map off ollebo.com, also delete its source file from `maps/`. Syncing then skips that map and counts it as failed.
- **Single replica.** SQLite and `ReadWriteOnce` volumes mean one pod at a time.
- **Builds run inside the upload request.** A large GeoTIFF can take minutes, and the page waits until the build finishes.
