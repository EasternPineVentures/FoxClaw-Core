# Changelog

All notable changes to FoxClaw are recorded here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versioning follows
[Semantic Versioning](https://semver.org/).

The version resets to `0.1.0` for this clean rebuild (`foxclaw-core`). The pre-v2 system is
preserved as the `v1-legacy` archive. Milestone map: `0.x` builds toward launch, one minor
bump per completed overhaul phase; **`1.0.0`** is earned at Apollo-2 cutover when v2 runs the
live track record and is demo-ready.

## [0.1.0] — 2026-06-17
### Added
- Clean `foxclaw-core` scaffold: package layout (`engine` / `store` / `policy` / `adapters`
  / `contract`), `pyproject.toml` (pure-stdlib core, version sourced from `VERSION`),
  README, and the public-contract airlock stub.
- Repository created outside OneDrive by design (local-first; git is the source of truth).
