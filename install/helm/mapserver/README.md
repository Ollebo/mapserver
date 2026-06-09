# OlleBo Mapserver Helm chart

Deploys the OlleBo mapserver (Flask uploader + terracotta tile server) onto a Kubernetes cluster as a single Pod with two containers, backed by three PVCs.

For onboarding, env vars, and architecture, see the [top-level README](../../../README.md). This file is a chart-scoped reference.

## Quick install

```sh
helm install mapserver . \
  --set ollebo.key=YOUR_KEY \
  --set ollebo.spaceId=YOUR_SPACE_ID \
  --set ingress.enabled=true \
  --set ingress.host=tiles.example.com \
  --set terracotta.publicUrl=https://tiles.example.com
```

## Topology

- **One Pod, two containers**: `map-server` (Flask, port 8080) + `terracotta` (port 5000).
- **One initContainer**: `terracotta-init` runs `ensure_schema()` against the SQLite DB so terracotta starts with a populated schema.
- **Three PVCs**: `-maps`, `-cogs`, `-db`. Independently sized and class-able via `persistence.{name}.size` / `persistence.{name}.storageClassName`.
- **One Service** with two named ports (`flask`, `terracotta`).
- **Optional Ingress** routing `/` → flask and `/tiles` → terracotta on a single host.

`replicas: 1` is hard-coded with `strategy: Recreate`. This is intentional: the PVCs default to `ReadWriteOnce` (the only access mode universally supported by GKE/EKS/AKS managed disks), and SQLite is a single-writer database. Scaling out requires a `ReadWriteMany` StorageClass + a non-SQLite terracotta backend; neither is exposed today.

## Pre-install checklist

1. **Use the published image (default) or build your own.** The chart defaults to `ghcr.io/ollebo/mapserver:latest`, which CI publishes on every push to `main`. To pin a specific build, set `--set image.tag=sha-<short>` or `--set image.tag=vX.Y.Z`. To use your own registry, run `docker build -f Dockerfile_build -t YOUR_REGISTRY/mapserver:TAG .` from the repo root, push it, then `--set image.repository=YOUR_REGISTRY/mapserver --set image.tag=TAG`.
2. **Pick a StorageClass.** If your cluster's default doesn't fit, set `persistence.{maps,cogs,db}.storageClassName` per PVC.
3. **DNS + TLS for the Ingress.** Point your chosen host at the Ingress controller's external IP, and create a TLS Secret (or rely on `cert-manager`). Pass `ingress.tlsSecret` and any controller-specific `ingress.annotations`.
4. **Set `terracotta.publicUrl`** to match the public scheme+host you're publishing — both the browser client and the server-side tile URL builder read it.

## Configuration

See `values.yaml` for all defaults and inline comments.

## Uninstall

```sh
helm uninstall mapserver
```

PVCs are not deleted automatically. Run `kubectl delete pvc -l app.kubernetes.io/instance=mapserver` to reclaim storage once you're sure you don't need the data.
