# RotaMate

**Status:** active
**Location:** `~/Desktop/RotaMate` (code lives outside this repo)

## What it is

Rota platform. Laravel-based, with a groups-aware roles implementation and database seeder.

The AIOS already runs `scripts/pyrunner/rota-health-check.py` in the PyRunner fleet — a scheduled health checker that reports `started`/`ok`/`failed`/`idle` to the dashboard.

## Open

- `FILES_DELIVERED.txt` plus `LARAVEL_MODELS_WITH_GROUPS.php` and `rota-schema-with-groups.sql` suggest a delivery was made — confirm whether this is **delivered/on hold** rather than active build.
- Link the live URL here once known.
