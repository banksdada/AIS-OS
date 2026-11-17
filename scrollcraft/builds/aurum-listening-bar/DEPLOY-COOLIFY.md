# Coolify deployment — Aurum Listening Bar

Static site (HTML/CSS/JS/assets), no build step. Served by Nginx in Docker.

## Deploy as a Coolify resource

1. **New Resource → Git** and select this repo (`AIS-OS` / your fork).
2. **Build**
   - Build pack: **Dockerfile**
   - Base directory: `scrollcraft/builds/aurum-listening-bar`
   - Dockerfile location: `Dockerfile` (within that base directory)
3. **Network / Domains**
   - Container port: **80**
   - Assign your domain/subdomain in Coolify.
4. **Environment variables:** none required.
5. Deploy.

## What gets served
- `index.html`, `scrollcraft.{css,js}`, `site.css`, `folio.js`
- `assets/` (hero mp4s, poster/images)

`node_modules/`, `lab/`, and logs are excluded via `.dockerignore`.

## Local preview
```bash
cd scrollcraft/builds/aurum-listening-bar
node /Users/banksdada/.agents/skills/scroll-craft/scripts/serve.mjs --root . --port 4518
# open http://localhost:4518
```
(Or `python3 -m http.server 4518` for a quick static preview; the scroll-craft server is preferred for local testing.)

## Notes
- This is a standalone static concept site inside the AIOS repo; deploy it as its own Coolify app/resource (separate from the main AIOS dashboard).
- Large media: `assets/hero.mp4` ~1.9MB, `assets/hero-m.mp4` ~352KB — committed/present in build folder for deployment.
