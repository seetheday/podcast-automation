# Architecture Diagrams

`workspace.dsl` captures Structurizr C4 views for the Maple History automation platform:

- **System context** – producers/engineers, Syncthing, Reaper, Whisper, Acast, Sanity.
- **Container view** – ingest/edit/export/transcript/notes/artwork/publish CLIs plus shared stores (`configs/`, `assets/`, `outputs/`).
- **Edit component view** – deeper look at the `automation.edit` subsystems (mixing, cuts, transcript sync, export, AI guidance).

## View the diagrams

Use Structurizr Lite so you can tweak the DSL locally and export PNG/SVG:

```bash
# from the repo root
mkdir -p outputs/structurizr
PORT=8081
IMAGE=structurizr/lite

docker run --rm -it \
  -p "${PORT}:8080" \
  -v "$(pwd)/docs/architecture:/usr/local/structurizr" \
  "$IMAGE"
```

Open `http://localhost:8081` and select `workspace.dsl`. Export the three views as PNG/SVG (the repo includes the current PNGs under `docs/architecture/`).

## Structurizr CLI export (optional)

If you prefer the Structurizr CLI:

```bash
structurizr.sh export \
  -workspace docs/architecture/workspace.dsl \
  -format plantuml \
  -output outputs/structurizr
```

## Maintenance

- Update `workspace.dsl` whenever pipeline stages or dependencies change.
- Re-export the diagrams and check them into `docs/architecture/` so README stays accurate.
- Note any intentionally un-automated/tested stages in `handoff.md` per repo guidelines so diagrams stay trustworthy.
