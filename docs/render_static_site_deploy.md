# Render Static Demo Deploy

Status: public-safe demo surface for weekend testing.

This repo does not expose FoxClaw internals as a web service. For Render, use the
generated static demo site:

```powershell
python tools\build_public_demo_site.py --output public_site
```

The generated folder contains:

```text
public_site/
  index.html
  styles.css
  README.txt
  coinfox-export/
    manifest.json
    intelligence_cards.jsonl
    scorecard.json
    outcomes.jsonl
```

`render.yaml` defines the static service:

```yaml
services:
  - type: web
    name: foxclaw-public-demo
    runtime: static
    buildCommand: python tools/build_public_demo_site.py --output public_site
    staticPublishPath: public_site
```

## Safety Boundary

Only fixture/public-contract material is published.

Do not add:

- `.env` files
- local DBs
- Discord archives
- Apollo Mesh data
- private parser fixtures
- screenshots containing private information
- live execution or account authority surfaces

## A2 Checklist

From A2 after pulling:

```powershell
python -m pytest tests\unit\test_public_demo_site.py tests\regression\test_public_export.py -q
python tools\build_public_demo_site.py --output public_site
```

Then connect the repo to Render with the Blueprint file or create a Static Site
manually using the same build command and publish path.

This is a testing/demo site, not production CoinFox.
