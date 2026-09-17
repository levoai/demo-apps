# Nginx and Kong in front of crAPI

A standing gateway chain for exercising Levo's gateway-metadata ingestion (CU-86bb7c4zc) and for
debugging traces that pass through a gateway, so nobody has to stand one up by hand to answer a
question or reproduce a customer report.

```
load  ->  nginx  ->  Kong  ->  crAPI services
          (edge)     (routes + tags)
```

Two hops rather than one on purpose: the customer's edge is nginx with Kong behind it, so a trace
taken here has the same shape as a trace taken at the customer.

Kong runs in its own namespace with one service and route per crAPI service, tagged the way a
customer plausibly tags theirs. **No crAPI traffic is repointed** — Kong sits alongside, and the
route paths deliberately match the paths Levo already discovers from crAPI traffic
(`/identity/...`, `/workshop/...`, `/community/...`, `/payments/...`). That is what makes an export
of this Kong land labels on real, already-discovered endpoints.

## What is in `kong/k8s/`

| File | What it creates |
|---|---|
| `00-namespace.yaml` | the `kong` namespace |
| `01-kong-config.yaml` | Kong's declarative config: services, routes, tags |
| `02-kong-deployment.yaml` | Kong 3.6.1, DB-less |
| `03-kong-service.yaml` | `kong` Service — proxy on 8000, admin on 8001, ClusterIP only |
| `04-nginx.yaml` | nginx config, deployment and Service — the edge in front of Kong |

## Deploy

```bash
kubectl --context spec-building-e2e apply -f kong/k8s/
kubectl --context spec-building-e2e -n kong rollout status deploy/kong
kubectl --context spec-building-e2e -n kong rollout status deploy/nginx
```

Kong is pinned to `3.6.1` and runs DB-less: `kong/k8s/01-kong-config.yaml` *is* the configuration. Kong reads it once at
boot, so after editing it, roll the pod:

```bash
kubectl --context spec-building-e2e -n kong rollout restart deploy/kong
```

## Reach the admin API

The Service is ClusterIP on purpose — the admin API must never be reachable from outside the
cluster. It is unauthenticated *within* the cluster, which is acceptable for a test fixture in a
namespace that holds nothing else; do not copy this shape for anything real.

```bash
kubectl --context spec-building-e2e -n kong port-forward svc/kong 8101:8001
curl -s localhost:8101/routes | jq '.data[] | {name, paths, tags}'
```

## Export and upload

```bash
curl -O https://docs.levo.ai/scripts/levo_kong_export.py
python3 levo_kong_export.py \
    --admin-url http://127.0.0.1:8101 \
    --gateway-id kong-spec-building \
    --auth-mode none
```

Then upload `kong-services.json` in Levo under **APIs → Import → Kong Services File**, or push it
from a pipeline with [levo_push.py](https://docs.levo.ai/scripts/levo_push.py).

This cluster reports to **api.dev.levo.ai**, so that is where the labels appear.

## nginx

`04-nginx.yaml`. A plain reverse proxy: everything to Kong, nothing clever.

- `proxy_pass http://kong.kong:8000` for every path
- `Host` is preserved, because Kong routes on it
- `X-Real-IP` and `X-Forwarded-For` are set, so the original client survives both hops
- `/nginx-health` is answered by nginx itself, so a Kong outage does not take nginx's probes down

## Where the traffic comes from

The hourly Locust job: `.github/workflows/generate_load.yml`, job `generate-crapi-load-kong`. It
drives the chain from outside the cluster through `crapi-spec-building.levoai.app`, reusing the
same locustfile as the other crAPI load jobs.

Before locust starts, the job asserts the response carries Kong's `via: kong/<version>` header. A
200 on its own proves nothing — crAPI answers 200 whether or not the request went through the
gateway — so without that assertion the job would happily pass while testing the wrong path.

Afterwards it asserts on the numbers rather than inheriting locust's exit code: hundreds of
requests must land and under 2% may fail. The crAPI locustfile always produces a few application
level failures by design, so a job that fails on any error at all reports failure forever and
tells you nothing.

For that job to traverse the chain, the Cloudflare tunnel must point that hostname at nginx rather
than straight at crapi-web:

```yaml
# cloudflared ConfigMap, namespace cloudflared
- hostname: crapi-spec-building.levoai.app
  service: http://nginx.kong:80        # was: http://crapi-web.crapi:80
```

Reverting is the same one line.

## What is configured, and why

| Route | Path | Tags | Purpose |
|---|---|---|---|
| `identity` | `/identity` | `tier:critical`, `pii:in-scope` + service `team:identity` | Labels land on real endpoints |
| `workshop` | `/workshop` | `tier:standard` + service `team:workshop` | Labels land on real endpoints |
| `community` | `/community` | `tier:standard` + service `team:community` | Labels land on real endpoints |
| `payments` | `/payments` | `tier:critical`, `pci:in-scope` + service `team:payments` | Labels land on real endpoints |
| `regex-assets` | `~/static/.*` | `tier:standard` | **Must be skipped** — a regex path cannot be matched to endpoints |
| `catch-all` | `/` | `team:platform` | **Must be skipped** — one route must not label the whole inventory |
| `untagged-health` | `/health` | none | Contributes nothing — and is *not* counted as a skip |

**Every route sets `strip_path: false`, including the three web ones.** Kong strips the matched
prefix by default, and that breaks this setup in two different ways:

- on the API routes, `/workshop/api/shop/products` would arrive as `/api/shop/products` and 404,
  because crAPI serves the `/workshop` prefix itself
- on the `~/static/.*` regex route the *whole match* is stripped, so a stylesheet request arrives
  as `/` and crapi-web answers the SPA index — **HTTP 200, with the homepage in place of the CSS**.
  Checking status codes alone will not catch it; compare the content type or the body size

It also keeps the path Kong advertises identical to the path Levo discovers, and that equality is
what makes the labels land on the right endpoints.

The last three are the point of this fixture as much as the first four: they keep Levo's refusal
logic exercised every time someone verifies the flow. A correct import reports **two** skips —
the regex and the catch-all — alongside non-zero labels. The untagged route is not one of them:
it has nothing to give, and counting it would overstate what was dropped.

## Samples

`kong/samples/` holds bundles for exercising the upload UI with no Kong at all:

| File | What it is for |
|---|---|
| `spec-building-cluster-export.json` | A real export taken from the Kong in this cluster |
| `healthy.json` | A well-formed multi-service export |
| `truncated.json` | Declares more routes than it carries — Levo must refuse it whole |
| `nothing-usable.json` | Every route unusable — a clean "nothing applied" |
| `partial-export.json` | `complete: false` — Levo must add but never remove |
| `wrong-gateway.json` | Same shape, `gateway_id: staging-kong` — must not disturb `prod-kong`'s labels |
| `wrong-kind.json` | `kind: APIGEE` — a source Levo does not ingest, refused on its own terms |
