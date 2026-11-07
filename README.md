# OlleBo Mapserver

A self-hosted bridge between your private GeoTIFF imagery and the [ollebo.com](https://ollebo.com) cloud UI.

You run this server on your own machine or cluster. It ingests `.tif` uploads, generates Cloud-Optimized GeoTIFF (COG) variants, and serves them as map tiles. When you pair it with an OlleBo space, the ollebo.com UI displays the maps by pointing its tile requests directly at your server — **the imagery itself never leaves your infrastructure.**

## What it can do

- Upload `.tif` files through a built-in web UI.
- Auto-detect the source as `rgb`, `multispectral`, or `dem` and generate the right COG variants:
  - **rgb** → `rgb`, `grayscale`
  - **multispectral** → `rgb`, `grayscale`, `ndvi`
  - **dem** → `hillshade`, `color-relief`, `slope`
- Serve the resulting variants as standard XYZ map tiles via [terracotta](https://terracotta-python.readthedocs.io/).
- Display a single map with a Leaflet viewer and a variant picker.
- Act as a registered tile origin for ollebo.com so private imagery is reachable from the cloud UI without ever uploading it.

## How it fits with ollebo.com

```
   Browser ──► ollebo.com (UI)
                   │
                   │ tile URLs point at YOUR mapserver
                   ▼
           Your mapserver (this repo)
                   │
                   ├── /data/maps   (source .tif — your storage)
                   ├── /data/cogs   (generated COG variants)
                   └── /data/db     (terracotta SQLite)
```

ollebo.com only ever sees URLs that point at your mapserver. The raster pixels stream from your hardware to the viewer's browser. You stay in control of the data.

## Pairing with an ollebo.com space

1. Sign in at [ollebo.com](https://ollebo.com).
2. Create a mapserver entry in the space you want to expose maps to. ollebo.com generates a unique key.
3. Paste that key into this server's **Settings** page, or set it as `OLLEBO_KEY` (the install scripts below prompt you for it). The key decides which space your maps appear in.
4. Set the public tile URL. Maps that are already built are sent to ollebo.com when you save Settings, and new maps are sent when they finish.

Everyone in that space on ollebo.com can then see your maps, as long as their browser can reach your public tile URL. If you delete a map on ollebo.com, it comes back the next time this server rescans or you save Settings.

> **Maps are private on ollebo.com, but the tile server has no login.** Only your space lists them, yet anyone who has a tile URL can fetch the tiles.

## External reachability

For ollebo.com (and anyone viewing maps through it) to fetch tiles from your server, the terracotta tile URL (`TERRACOTTA_PUBLIC_URL`) must be reachable from the public internet.

**Local install — use a tunnel.** [ngrok](https://ngrok.com), [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/), or a similar service. With ngrok:

```sh
ngrok http 5001
# copy the https URL ngrok prints and set it as TERRACOTTA_PUBLIC_URL
```

Re-run the install script (or edit `.env`) with the new URL and `docker compose up -d` again.

**Kubernetes install — use an Ingress.** The Helm chart ships an optional Ingress (`--set ingress.enabled=true --set ingress.host=tiles.example.com`). It publishes the tile routes only; the web UI has no login, so it stays private unless you set `ingress.exposeUi=true`. Put it behind a public DNS name with TLS. For high-traffic installs, add a CDN (CloudFront, Cloudflare, Fastly) in front of the Ingress.

> The tile server has **no authentication** today. Anything that can reach `TERRACOTTA_PUBLIC_URL` can request tiles. Treat the URL as a shared secret, put it behind a network policy, or wait for the auth module on the roadmap.

## Storage layout

Three folders, all mountable as volumes:

| Path | Purpose |
|---|---|
| `maps/` → `/data/maps` | Source `.tif` uploads — the only thing you supply. |
| `cogs/` → `/data/cogs` | Generated Cloud-Optimized GeoTIFF variants, keyed `<space>/<map>/<variant>.tif`. |
| `db/`   → `/data/db`   | terracotta's SQLite metadata (`terracotta.sqlite`). |

Tiles are computed on the fly by terracotta from the COGs in `cogs/`; nothing is pre-rendered.

---

## Install — Docker (local)

For a single machine, a personal install, or evaluation. You drop `.tif` files into `maps/`, upload them through the web UI, and they appear in your OlleBo space.

```sh
git clone https://github.com/ollebo/mapserver.git
cd mapserver
bash install/docker-install.sh
```

The script:

1. Checks that `docker` and `docker compose` are installed.
2. Prompts for `OLLEBO_KEY`, `OLLEBO_SPACE_ID`, `TERRACOTTA_PUBLIC_URL`, and `API`.
3. Writes a `.env` file in the repo root.
4. Creates `maps/`, `cogs/`, `db/` host directories.
5. Runs `docker compose up -d --build`.

When it finishes you can open `http://localhost:8888` and start uploading. Stop the stack with `docker compose down`; restart it with `docker compose up -d`.

To change configuration, edit `.env` and re-run `docker compose up -d` — no need to re-run the install script.

## Install — Kubernetes (Helm)

For a hosted install on a cloud provider — bigger map catalog, multiple users, public Ingress.

```sh
helm install mapserver oci://ghcr.io/ollebo/charts/mapserver \
  --set ollebo.key=YOUR_KEY \
  --set ollebo.spaceId=YOUR_SPACE_ID \
  --set ingress.enabled=true \
  --set ingress.host=tiles.example.com \
  --set terracotta.publicUrl=https://tiles.example.com
```

The chart deploys **one Pod with two containers** (Flask + terracotta) plus an initContainer that creates the terracotta SQLite schema. Three `PersistentVolumeClaim`s back `maps/`, `cogs/`, `db/`. A single Service exposes both container ports; the optional Ingress publishes them.

Key `values.yaml` knobs:

| Value | What it controls |
|---|---|
| `image.repository`, `image.tag` | Image to deploy. Defaults to the chart's `appVersion`. Set `latest` for the newest build of `main`, or `sha-<short>` for a specific commit. |
| `ollebo.key` | Your map key from ollebo.com, stored in a Secret. |
| `ollebo.spaceId`, `ollebo.apiUrl` | Non-sensitive config, stored in a ConfigMap. |
| `terracotta.publicUrl` | Public URL for tile fetches — must match your Ingress host. |
| `ingress.enabled`, `ingress.host`, `ingress.className`, `ingress.tlsSecret` | Ingress wiring. |
| `ingress.exposeUi` | Also publish the web UI. Off by default because it has no login. |
| `persistence.{maps,cogs,db}.size` | PVC size per dataset folder. |
| `persistence.{maps,cogs,db}.storageClassName` | Per-PVC StorageClass override. |

> **Single-replica only.** The chart pins `replicas: 1` and uses `Recreate` rollouts because the PVCs are `ReadWriteOnce` (the default on GKE/EKS/AKS managed disks) and SQLite is a single-writer database. If you need horizontal scaling, swap SQLite for a remote terracotta provider and use a `ReadWriteMany` StorageClass — that's a follow-up, not a supported knob today.

After install, `helm get notes mapserver` prints the resolved tile URL and a `kubectl port-forward` command for offline checking.

---

## Configuration reference

These are the environment variables consumed by code:

| Variable | Default | Notes |
|---|---|---|
| `OLLEBO_KEY` | _(empty)_ | Your map key from ollebo.com. A key saved on the Settings page takes priority. |
| `OLLEBO_SPACE_ID` | `local` | First key in the terracotta `[space, map, variant]` schema. It doesn't need to match your ollebo.com space. |
| `TERRACOTTA_PUBLIC_URL` | `http://localhost:5001` | Browser-facing tile URL. Must be reachable from any viewer. |
| `API` | `https://www.ollebo.com/api` | ollebo.com API base. Where this server checks its key and registers maps. |
| `TERRACOTTA_DB_PATH` | `/data/db/terracotta.sqlite` | SQLite location inside the container. |
| `TERRACOTTA_PROVIDER` | `sqlite` | terracotta driver. Only `sqlite` is exercised today. |

For Docker installs, the install script writes these to `.env`. For Helm installs, they're set via `values.yaml`.

## Architecture in one paragraph

`code/start.py` is a Flask app with three real routes: `/` (home, lists maps from `/data/maps`), `/upload` (POST, prepends a random name and saves the file), `/mapmaker` (POST, runs the COG pipeline synchronously and redirects to `/map`). The pipeline in `code/mapmaker/makingGeotiff.py` opens the source with `rasterio`, classifies it via `detect_input_type`, and for each `VariantSpec` shells out to `gdal_translate` / `gdal_calc.py` / `gdaldem` to write a COG into `/data/cogs/<space>/<map>/<variant>.tif`. Each generated COG is registered into terracotta's SQLite DB. The viewer template renders a Leaflet map whose tile layer points at `${TERRACOTTA_PUBLIC_URL}/{singleband|rgb}/<space>/<map>/<variant>/{z}/{x}/{y}.png`.

The COG/variant code under `code/mapmaker/maps/` is mirrored with the sibling `map-maker` project; changes in one should be ported to the other.

## Container images

CI (`.github/workflows/docker-publish.yml`) builds `Dockerfile_build` on every push to `main` and pull request, and publishes to GitHub Container Registry on pushes:

- `ghcr.io/ollebo/mapserver:latest` — current `main`.
- `ghcr.io/ollebo/mapserver:sha-<short>` — pinned to a specific commit.
- `ghcr.io/ollebo/mapserver:X.Y.Z` — on git tags matching `v*.*.*`.
- `oci://ghcr.io/ollebo/charts/mapserver` version `X.Y.Z` — the Helm chart, on the same git tags, after its image has been published.

Pull requests build the image for verification but don't push. The Docker install script builds locally from `Dockerfile_build`; the Helm chart runs the image matching its release by default.

## Known rough edges

- **No auth on the tile server.** See "External reachability."
- **No login on the web UI.** It can upload files and show the map key, so keep it private.
- **Single-replica only on Kubernetes** because of SQLite + RWO PVCs.
- **Container build is fragile.** `Dockerfile_build` uses `--break-system-packages` on Ubuntu 24.04 with pinned `terracotta==0.10.1`. A move to a venv-based image is on the roadmap; for now, rebuild from the pinned base if pip breakage occurs.
- **Dev bind-mount is in a separate file.** `docker-compose.yaml` deploys the baked-in image. `docker-compose.override.yaml` adds the `./code:/code` live-reload mount and is auto-merged by `docker compose` when present. Delete it before publishing an image to production.
