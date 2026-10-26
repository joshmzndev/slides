# Slides

Slide decks written in Markdown and converted to HTML with [Marp](https://marp.app).

- `<course>/*.md`: slide sources (e.g. `ap-cyb/dns.md`); the `.html` next to each is Marp's output.
- `index.html`: hand-written landing page for slides.manzano.dev; `make build` copies it to `build/index.html`. Nothing generates it, so whenever a deck or course is added, renamed, or removed, edit its "What's here" list by hand in the same change (a new course gets its own card).
- `themes/`: custom Marp themes (set via `.marprc.yml`). Marp inlines them into the HTML, so the CSS isn't deployed.
- `make build`: rebuilds decks whose `.md`, a theme, or `.marprc.yml` changed and copies the HTML into `build/`, keeping the folder layout, along with any `images/` files the decks reference.
- `make test`: runs `make build`, then serves `build/` locally with `python3 -m http.server` to preview.
- `make deploy`: runs `make build`, then `git add .`, commits with the current date and time as the message, and pushes.
- `build/`: what gets deployed. GitHub Actions (`.github/workflows/main.yml`) uploads it to Cloudflare with `wrangler deploy` on every push to `main` (see `wrangler.toml`), using the `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` repository secrets.
